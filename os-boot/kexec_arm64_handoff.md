# kexec from Linux into a non-Linux kernel on arm64: inherited state

Which hardware state does Linux leave live at `kexec -e`, and which of it must the next kernel reset
itself? This matters for unikernels such as miniosv, whose init assumes the state firmware leaves.

## Conditions

- The Linux side comes from reading the Linux 7.2.12 source (arm64), on 2026-10-24.
- It covers the normal path (`kernel_kexec`, not preserve_context). The kdump/crash path differs; see the end.
- The successor examined is miniosv at commit 8bca4e60 (aarch64, UEFI-stub-only boot). Its gaps are
  findings from reading the code. No miniosv kexec boot has been run yet, so none of this is measured.
- Linux self-kexec (kexec_load, kexec_file_load, kdump, KHO/LUO) was verified working under QEMU 10.2 TCG
  (`virt`, GICv3+ITS, neoverse-v1, AAVMF/ACPI). QEMU has no cache model, so cache-coherency hazards
  cannot show up there.

## What Linux leaves behind on the normal kexec path

| State | Left as | Evidence (Linux 7.2.12) |
| --- | --- | --- |
| Secondary CPUs | Offline via PSCI CPU_OFF | `kernel/cpu.c:1538`, `arch/arm64/kernel/psci.c:68` |
| CPU mode | MMU, D-cache and I-cache off; DAIF masked; x0 = DTB, x1-x3 = 0 | `relocate_kernel.S:20,96`; `asm/sysreg.h:859` |
| Exception level | EL2 if Linux ran at EL2 (VHE or nVHE), else EL1; HCR_EL2 untouched | `relocate_kernel.S:88-94`, `hyp-stub.S:62` |
| Caches | Only the copied image pages are cleaned (`dc civac`); other lines remain | `relocate_kernel.S:67` |
| SPIs/PPIs | Not masked: `machine_kexec_mask_interrupts` runs only on the crash path | `machine_kexec.c:220` |
| GICD / redistributors / ICC | GICD enabled, redistributors awake, IGRPEN1 = 1 (no shutdown hooks) | `irq-gic-v3.c` |
| ITS | Still enabled; command queue and device/collection tables in freed (unreserved) RAM | `irq-gic-v3-its.c:5097` (syscore suspend/resume only) |
| LPIs | EnableLPIs = 1; PROPBASER/PENDBASER live on every redistributor, including offline CPUs | `irq-gic-v3-its.c:2345,5476` |
| LPI table memory | Reserved only via `LINUX_EFI_MEMRESERVE_TABLE_GUID` (EFI config table) | `efi.c:1102-1161` |
| Boot-CPU timer | Not disabled. EL1 without EL2 uses CNTV; nVHE uses CNTP; VHE uses CNTHV | `arm_arch_timer.c:1136-1152` |
| PMU | Counters/PMINTEN may still run if perf was active | `arm_pmuv3.c` (no shutdown hook) |
| PCI | Bus Master cleared; MSI/MSI-X, INTx, BARs and MSE untouched by the core | `pci-driver.c:574` |
| ENA / NVMe / virtio | Driver shutdown resets the device (ENA also disables MSI-X) | `ena_netdev.c:4158-4200`, `virtio.c:411-449` |
| SMMUv3 (metal) | CR0 = 0 only; GBPA is ABORT only if SMMU was on at Linux probe, else firmware's value | `arm-smmu-v3.c:5556,4778` |
| EFI runtime | 1:1 (no SetVirtualAddressMap) when VA_BITS_MIN >= 48, else at Linux-chosen VAs | `libstub/arm64.c:67` |
| DTB /chosen | bootargs, `linux,uefi-system-table`, `linux,uefi-mmap-*` (pre-Linux map); no /memory on ACPI | `drivers/of/kexec.c`, `libstub/fdt.c:97-177` |

The EFI memory map handed over is the one from the original `ExitBootServices`. The LPI table ranges in
it are ordinary conventional memory; only the MEMRESERVE table marks them as in use.

## What a successor must reset or adopt

1. **ITS**: clear `GITS_CTLR.Enabled`, poll `Quiescent`, and only then program `GITS_BASERn`/`CBASER`.
   `CREADR` resets only when `CBASER` is written with the ITS disabled. Write every `GITS_BASERn` field
   explicitly: Linux may leave Indirect, Size and cacheability set. Linux does this in `its_force_quiescent`
   (`irq-gic-v3-its.c:4756`).
2. **LPIs**: either clear `GICR_CTLR.EnableLPIs` and poll RWP, verifying that it cleared, or adopt the
   inherited PROPBASER/PENDBASER tables. Clearing is IMPLEMENTATION DEFINED (`irq-gic-v3-its.c:5416`).
   Adopting is what Linux does, and it works on any GIC (`allocate_lpi_tables`, `:3068-3086`).
3. **Memory map**: subtract the MEMRESERVE ranges (the GIC keeps writing LPI pending bits there). Also
   subtract the DTB and the successor's own image.
4. **Caches** (real hardware only): invalidate to PoC everything written with the MMU off (page tables,
   .bss) before enabling caches. Linux's `head.S:95-106` does this.
5. **GIC CPU interface**: zero `ICC_AP1Rn_EL1`. This is not needed after a normal kexec from process
   context, but it is needed after a crash in IRQ context. Linux does it in `irq-gic-v3.c:1218-1226`.
6. **SPIs/PPIs**: disable and deactivate all of them. Clearing pending state is optional; Linux does not.
7. **EL2 entry** (metal): drop to EL1 (HCR_EL2.RW, E2H, CNTHCTL_EL2, CNTVOFF_EL2) or support EL2.
8. **SMMUv3** (metal): set GBPA to bypass, or program the SMMU, before device DMA.

## miniosv status (commit 8bca4e60)

- **Already handled:**
  - Disabling, deactivating and reconfiguring SPIs/PPIs (`arch/aarch64/gic-v3.cc:421-518`).
  - CNTV_CTL clear (`arm-clock.cc:160`).
  - PMU reset before use (`arch-perf.hh:98`).
  - Bus Master set (`minidpdk/internal/pci.hh:95`).
  - ENA reset at init (`ena_ethdev.c:1522`).
  - All MSI-X vectors masked before enable (`drivers/pci-function.cc:624`).
  - Polled console with no IRQ.
- **Missing:**
  - Items 1-5 above: `init_its` and `init_lpis` reprogram an enabled ITS/LPI setup
    (`gic-v3.cc:137,556-606`).
  - BASERn keeps all non-address fields (`gic-v3.cc:582`).
  - `boot.S` has no `dc` maintenance.
  - Metal also needs items 7-8; `validate_el` halts at EL2.
- **Unrelated bug seen while tracing:** `mask_irq` uses `|= ~GIC_LPI_ENABLE` for LPIs (`gic-v3.cc:631`), so
  it never clears the enable bit. It also issues no ITS INV after changing the property table.

## Crash path and open questions

- kdump runs `machine_kexec_mask_interrupts` and skips device shutdown, so devices may still be doing DMA.
- With kexec_load, kexec-tools builds the DTB in userspace; its exact /chosen contents were not checked.
- The GBPA value left by AWS metal firmware is unknown; check it on a Graviton metal instance.
