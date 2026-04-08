# Skills

This repo keeps canonical repo-local workflows under `skills/`.
Treat `skills/` as the authoritative workflow source for this context.
Treat `.local/` as scratch worktrees and one-off notes, not as the canonical workflow definition.

## Workflow map

Read these references before or while using a role skill when the task touches workflow state:

- [Workflow Logic](skills/references/workflow-logic.md)
  Canonical state machine for draft / ready / question / need po / waiting_signal, role handoff, and bounce handling.
- [Validation And Build](skills/references/validation-and-build.md)
  Host/WSL/firmware validation expectations and high-signal test paths.
- [Work Graph](planning/workgraph.yaml)
  PM-owned dependency graph for issue ordering, blocked edges, and done criteria.

## Role skills

- [Developer Workflow](skills/developer-workflow/SKILL.md)
  Use for concrete implementation, issue continuation, draft PR iteration, and targeted validation.
- [PR Review](skills/pr-review/SKILL.md)
  Use for findings-first review of ready PRs. Reviewer is read-only for tracked source files.
- [PM Workflow](skills/pm-workflow/SKILL.md)
  Use when scope, acceptance criteria, issue/PR linkage, dependency ordering, or follow-up splitting is the main problem.

## Role boundaries

- `developer`
  Owns code changes, validation, issue continuation, and draft PR progress.
- `reviewer`
  Owns findings, merge-risk judgment, and ready-for-review passes. Reviewer does not implement tracked source changes.
- `pm`
  Owns workflow clarity: work graph maintenance, scope boundaries, question wording, issue linkage, validation sufficiency, and follow-up split.
- `none`
  General repo work when no stronger role-specific workflow is required.

## Escalation rules

- If work is blocked by a concrete missing answer or decision, move toward `question` and state the exact question.
- If there is no new work until an external signal arrives, use `waiting_signal` rather than bouncing metadata.
- If a PR keeps bouncing between developer and reviewer, stop the bounce and hand it to `pm`.
- If `pm` has already clarified the same PR head multiple times and it still needs a product decision, move it to `need po` and stop automation.
