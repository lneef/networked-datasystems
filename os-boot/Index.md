# OS boot

Insights on how kernels and unikernels are booted and handed over, including firmware handoff and kexec.

## Structure

| Topic | Path | Insights |
| --- | --- | --- |
| kexec handoff on arm64 | [kexec_arm64_handoff.md](kexec_arm64_handoff.md) | State Linux leaves live at `kexec -e` (GICv3 ITS/LPIs, caches, timers, PCI, SMMUv3, EFI) and what a non-Linux successor such as miniosv must reset or adopt. |
