# Developer Workflow

Use this workflow for concrete implementation, issue continuation, draft PR progress, and targeted validation in this repo.

## Read first

1. Read `skills/references/workflow-logic.md`.
2. Read `planning/workgraph.yaml`.
3. Read `skills/references/validation-and-build.md` when code, runtime behavior, tools, firmware, or tests are involved.

## Main job

Move implementation forward with concrete changes. Do not stop at abstract advice when the task is actionable.

## Developer flow

1. Refresh the relevant branch state before assuming what is left.
2. Resume before rewrite:
   - inspect existing branch
   - inspect recent commits
   - inspect linked PRs/issues
   - inspect explicit issue references in PR title/body/comments
   - inspect the relevant node(s) in `planning/workgraph.yaml`
3. If working on a PR:
   - validate against the PR's actual current head
   - inspect the latest reviewer outcome and labels
   - check whether the linked work-graph node is blocked by another node
4. If the PR is ready but GitHub reports `mergeable=CONFLICTING` or `mergeStateStatus=DIRTY`:
   - treat merge-conflict resolution as developer work
   - sync with `main`
   - resolve the conflicts on the PR branch
   - rerun focused validation
   - push a new head for reviewer
   - do not leave the PR stuck on an old conflicting head
5. If working on a draft PR:
   - do not mark the same blocked head ready again without a real fix
6. If no suitable PR exists:
   - inspect the actionable open issue pool
   - choose one issue intentionally based on repo state and `planning/workgraph.yaml`
   - do not choose issues already waiting in `question`
   - do not choose items blocked by an unfinished dependency unless you are explicitly unblocking that dependency
7. Make concrete code changes when needed.
8. Run focused validation before handoff.
9. Publish issue-driven completion as a PR instead of stopping at local changes.
10. If the relevant implementation PR is already merged and the linked issue remains open:
   - do not post a new developer "workflow blocker" comment just because the issue still needs closure work
   - treat that state as PM close-out territory unless there is still concrete code work left
   - let PM reconcile closure, follow-up split, or workflow metadata

## Required metadata behavior

1. Put the issue number explicitly in the PR body/title/comment.
2. Prefer `Refs #<issue>` in the PR body.
3. Do not rely on `issue:<n>` label as the primary linkage.
4. After a meaningful implementation pass, update the PR with `gh` so the next handoff is explicit.

## Bounce handling

1. If reviewer and developer are bouncing on the same PR head, stop the bounce.
2. Do not keep flipping draft/ready or repeating the same metadata-only move.
3. If the blocker is workflow clarity, dependency ordering, validation gate ambiguity, or scope ambiguity, return `blocked` and clearly hand the PR to `pm` via `question`.
4. If the PR already has `need po`, stop and wait for human action.
5. If implementation is already merged and only issue close-out / follow-up splitting remains, do not bounce that back to developer; PM owns that cleanup.

## State decisions

Choose the completion state intentionally:
- `continue`: concrete implementation work still exists now
- `waiting_signal`: no concrete next step until some external signal changes
- `blocked`: a concrete answer / credential / scope / dependency decision is missing
- `done`: this developer pass completed the useful work for the current snapshot

If blocked, state the exact missing answer and move the workflow toward `question`.
