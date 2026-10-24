# Working with this knowledge base

This repository holds research insights in networked data systems for use in
implementation and research discussion, including unikernel and operating-system
development. Organize it by research topic and question, not as a book, thesis,
or sequence of chapters. Coverage is partial; a task may have no relevant section.

## Consult throughout the work

- Use the KB as a developer uses a manual or guide: move between relevant notes
  and the implementation or research discussion as questions arise.
- Start with `Index.md` to locate relevant insights, then read the linked notes.
- Return to the KB when design choices, unexpected results, or new hypotheses
  need context. Apply an insight, check its fit, and refine the next lookup.
- Read what the current question needs; reuse context already gathered and
  follow related notes when they help resolve it.
- If the index suggests a gap or incomplete navigation, make one focused search
  pass using task-specific terms. Do not exhaustively scan unrelated sections or
  repeatedly broaden searches. With no relevant result or concrete lead, continue
  the task without KB guidance and briefly state that no relevant coverage was found.
- Reuse that coverage assessment; search again only when a materially new
  question or concrete lead warrants it.
- Before implementing or discussing work informed by this research, check the
  relevant claims, evidence, assumptions, and limitations.
- Cite the relevant note paths in answers and implementation rationale. Do not
  treat an absent entry as evidence that a claim is false or settled.

## Record new insights

- Before completing implementation, research discussion, or analysis within the
  KB's scope, agents **must record the main new evidence-backed insights and
  corrections** useful to future work, including findings from another repository.
- Update an existing note when it covers the finding; otherwise add a focused
  note. Include evidence, conditions, limitations, and practical implications.
  Supported negative results and newly identified limits also count as insights.
- Synthesize reusable findings before writing. Integrate them into the topic
  hierarchy below; do not dump chat transcripts, session logs, or undigested results.
- Keep main findings self-contained: state what changed, its effect, implications,
  and essential conditions so readers can interpret and apply them without digging.
- For performance claims, specify the metric, units or normalization, baseline,
  workload, and relevant configuration. State whether gains are isolated,
  incremental on top of named changes, or cumulative for a named combination.
  Make the percentage denominator and enabled features clear for each comparison.
  Do not add percentages or attribute a combined gain to one feature without evidence.
  Mark unknown comparison details explicitly and qualify the claim accordingly.
- Distinguish measured effects from proposed explanations; retain uncertainty
  or variability when it materially affects the conclusion.
- Link to the source experiment or report for detail. Do not add raw benchmark
  outputs, exhaustive result tables, plot-recreation data, or reproduction guides
  merely to preserve a finding; the KB captures insights rather than experiments.
- Update the relevant indexes and cite changed note paths in the final response.
  Do not leave a new finding only in chat or merely suggest adding it later.
- If no new supported insight emerged, no KB edit is required. Do not invent
  findings or duplicate existing content to satisfy this rule.
- If recording is blocked by access or permissions, report the blocker and the
  unrecorded finding explicitly; do not claim the KB was updated.

## Making changes

- Draft every change on a dedicated branch or worktree, never directly on the
  default branch. Consult the KB throughout the work and incorporate supported
  findings as required above.
- Store concrete research insights, not filler, speculative claims presented as
  facts, or chapter outlines. Distinguish sourced findings, local observations,
  and hypotheses; ground open questions in existing evidence.
- Keep notes focused. Include the insight, its evidence or source, the conditions
  under which it holds, and implications for implementation or discussion.
- Link sources precisely enough to trace claims; include only the experimental
  context needed to interpret or apply the main finding. Reproduction steps and
  exact datasets belong with the source experiment, not in the KB contribution.
- Update `Index.md` when adding, moving, or materially changing an insight.
  Use relative links and brief descriptions that help an agent choose what to read.
- Check links and factual support; run relevant checks when changing code.

## Organization and limits

- Use descriptive topic directories as content emerges, with focused notes and
  directly useful reference code. Do not create empty topic scaffolding.
- Before adding content, inspect neighboring notes and choose the narrowest
  existing topic that fits. Organize by research question or mechanism, not by
  session, date, or the order in which findings were discovered.
- When an insight spans several questions or outgrows a focused note, create
  meaningful subtopics and split it into independently useful, linked notes.
  Add depth only when it improves lookup; avoid arbitrary numbered file parts.
- Give each new topic or subtopic directory an `Index.md` using the
  `Topic | Path | Insights` table. Link it from its parent index and link its
  focused notes locally, so readers can navigate from broad scope to detail.
- When reorganizing existing content, repair affected links and index entries.
  Cross-link related topics instead of duplicating findings across branches.
- Use `<topic>/shared/` for resources reused within a topic and root `shared/`
  for resources reused across topics. Link to shared material instead of copying it.
- Keep `Index.md` a short map of actual content, not a duplicate of the notes.
  Describe scope and what each entry helps answer. Keep measurements, explicit
  numbers, and implementation details in the notes unless vital to define scope.
- Every file an agent creates must be **fewer than 200 lines** (199 maximum).
  Split larger content using the topic hierarchy above; do not evade the limit
  by compressing content into unreadable lines.
- Keep `AGENTS.md` **fewer than 100 lines** (99 maximum).
