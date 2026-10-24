# Networked Data Systems — Knowledge Index

A working reference for implementation and research discussion in networked data
systems. Use it like a manual: browse by topic, apply relevant insights, and
return as new questions arise. Notes provide claims, evidence, assumptions, and
practical implications. Scope includes unikernel and operating-system development;
coverage is partial, and some tasks may have no relevant section yet.

## Insights

Add topic entries with relative links and a one-sentence description as
evidence-backed notes are added.Cloud specific stuff will mainly refer to AWS, the primary evaluation platform.

## Structure

| Topic | Path | Insights |
| --- | --- | --- |
| Cloud-NICs | `cloud-nics` | Insights on offload features and performance insights for NICs in the Public Cloud |
| OS boot | [os-boot](os-boot/Index.md) | Boot and handover mechanisms for kernels and unikernels, e.g. what state kexec leaves for a non-Linux successor on arm64 |

## Repository map

- [AGENTS.md](AGENTS.md): lookup, contribution, organization, and file-size rules.
- [Consult the KB](skills/consult-networked-data-systems/SKILL.md): skill
  for applying research insights to implementation, discussion, and analysis.
- [Skill installation](skills/README.md): install the shared skill for Codex and
  Claude Code on another machine.
- As content grows: `<topic>/` holds focused notes and related code;
  `<topic>/shared/` holds resources reused within that topic; root `shared/`
  holds resources reused across topics. These directories are created as needed.
