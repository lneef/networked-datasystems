---
name: consult-networked-data-systems
description: Consult this networked data systems research KB for implementation, debugging, review, discussion, or analysis, including unikernel and operating-system development, cloud NICs, network performance, flow steering, and data paths. Use relevant notes as an ongoing manual; coverage is partial, so keep lookups bounded and continue when no relevant section exists. Skip unrelated coding or editorial tasks.
---

# Consult the networked data systems KB

Use the KB to inform implementation and research, including unikernel and OS
development. The root `Index.md` maps current coverage, which may not include a
section for the task. Cloud-specific findings primarily concern AWS, the current
evaluation platform, and require care when applied elsewhere.

## Consult as the work develops

Move back and forth between the task and the KB, as a developer uses a manual.
Look up the current question, apply the relevant insight, and compare the outcome
or argument with the note's assumptions. Let that comparison guide the next lookup.

Return when a design decision needs support, a test behaves unexpectedly, or a
discussion introduces a new hypothesis or tradeoff. For example, unexpected queue
placement can prompt a return to steering notes; a throughput discussion can lead
to measurement conditions and competing explanations in performance notes.

Keep lookups focused on unresolved questions. Reuse notes already read and follow
related material as needed; resume the task once there is enough evidence to
proceed. Record the main new supported insights and corrections before finishing.

## Find relevant evidence

1. Use a user-supplied KB checkout or worktree when provided. Otherwise resolve
   symlinks to this `SKILL.md`; its path is `<kb>/skills/<skill-name>/SKILL.md`,
   so the KB root is `Path(skill_path).resolve().parents[2]` in Python.
   Verify that root contains `Index.md` and `AGENTS.md`; if unavailable, ask for
   its location. Resolve KB paths from that root, not the current project.
2. Read the root `AGENTS.md` and `Index.md`, then follow relevant topic indexes
   and notes. Index entries may name directories or paths without Markdown links.
3. If the index has no relevant entry or navigation is incomplete, make one
   focused search pass with `rg` for task-specific mechanisms, APIs, or symptoms.
   Follow concrete leads, but do not scan unrelated sections or repeatedly broaden
   searches. If no relevant material appears, briefly note the coverage gap and
   continue the task without KB guidance. Reuse this assessment until a materially
   new question or concrete lead warrants another lookup.
   Read matching notes in context; snippets and index summaries are not evidence.
4. Check the claim's source, date, hardware, kernel/driver versions, workload,
   measurement method, and limitations where available. Inspect referenced code
   when the conclusion depends on it. Identify missing evidence explicitly.

## Apply findings to the task

- **Implementation:** connect relevant insights to concrete design choices,
  configuration, or code changes. Compare the target environment with the
  measured one; preserve applicable assumptions and propose or run focused checks
  for transferred claims. Read experimental commands before using them and run
  them only within the user's authorized task and environment.
- **Discussion and analysis:** use the notes to explain mechanisms, compare
  alternatives, and evaluate tradeoffs. Separate measured observations, cited
  research, and your own deductions; surface conflicting evidence or open questions.
- Cite the note paths, with headings or line numbers when useful, alongside the
  decisions or claims they support. Retain conditions and units with quantitative
  results; do not present a benchmark result as a universal guarantee.
- If the KB lacks relevant coverage or evidence, say what is missing and
  continue with clearly distinguished reasoning or external research as needed.
  Verify current platform behavior when the task depends on it. Never invent a
  KB finding or treat absence as evidence against a claim.

## Required capture of new insights

Before completing an in-scope task, record the main new evidence-backed insights
and corrections useful to future work, including findings from another repository.
Update an existing note or add a focused one with evidence, conditions,
limitations, and implications; include supported negative results where relevant.
Keep main findings concise and self-contained: what changed, its effect, why it
matters, and the conditions needed to interpret and apply it without source digging.
For each performance comparison, state the metric and units or normalization,
baseline configuration, workload, and relevant hardware/software conditions.
Label the result as isolated, incremental on top of named changes, or cumulative
for a named combination; identify enabled features and the percentage denominator.
For example, distinguish "X alone improves throughput by Y% over baseline B"
from "adding X to B+Z improves throughput by Y% over B+Z" and "X+Z together
improve throughput by Y% over B." These are distinct claims, not interchangeable.
Do not sum percentages or assign a combined gain to one feature without evidence.
If comparison details are unknown, state that explicitly and qualify the finding.
Retain uncertainty or variability when it affects the conclusion, and distinguish
measured effects from proposed explanations. Link to the source experiment or
report for details; do not import raw results, exhaustive tables, plot-recreation
data, or benchmark reproduction guides. Such artifacts are not required for a
KB contribution; retain only enough context to interpret and apply the insight.
Synthesize reusable findings and inspect neighboring notes before choosing their
place in the topic hierarchy. Keep each note focused on a research question or
mechanism. Split larger insights into meaningful subtopics with local tabular
`Index.md` files, linked from their parent indexes, and focused leaf notes.
Use shared resources and cross-links for reused material; repair links when
moving content. Avoid transcript dumps, chronological session notes, duplicate
findings, and arbitrary numbered file parts. Add hierarchy when it improves lookup.
Follow the root `AGENTS.md`: draft on a dedicated branch or worktree and update
the relevant indexes with relative links. Cite changed note paths in the final
response. Do not leave findings only in chat or defer recording to a suggestion.

If no new supported finding emerged, no edit is needed; avoid duplicate content.
If access or permissions prevent recording, report the blocker and unrecorded
finding explicitly. Keep index entries about scope and navigation; place
measurements, explicit numbers, and implementation details in notes unless vital
to define an entry's scope. Preserve unrelated work and distinguish newly
measured results from proposed experiments. Every new file must stay below
200 lines; `AGENTS.md` must stay below 100 lines.
