# PR Review

Use this workflow for findings-first review of ready PRs in this repo.

## Read first

1. Read `skills/references/workflow-logic.md`.
2. Read `planning/workgraph.yaml`.
3. Read `skills/references/validation-and-build.md` when review touches code, runtime behavior, tools, firmware, or tests.

## Main job

Find real regressions, behavior changes, missing coverage, and merge blockers.
Do not drift into tracked source implementation.

## Reviewer guardrails

1. Reviewer is read-only for tracked source files.
2. Reviewer may checkout the PR branch or detached head to inspect/build/test.
3. Always restore the original branch/HEAD before finishing.
4. Review only ready PRs.
5. Findings first, ordered by severity.
6. Separate true findings from baseline/environment noise.

## Review flow

1. Fetch PR metadata with `gh pr view`.
2. Inspect title, body, comments, explicit issue references, labels, and claimed test plan.
3. Inspect the linked node(s) in `planning/workgraph.yaml` so you know whether the PR is aligned with the intended scope.
4. Refresh `origin/main` before judging the diff.
5. Review `origin/main...<pr-head>` against the current PR head.
6. Prefer a dedicated `.local/review-pr<N>` worktree.
7. Run focused validation when practical.
8. Post concise Traditional Chinese findings and update PR state with `gh`.
9. If the review finds no remaining blockers and the PR is ready, merge it directly with `gh pr merge` instead of only leaving a comment.
10. After a successful merge, leave a concise close-out summary instead of leaving the thread ending on the last blocking review comment.
11. Do not add a second manual handoff comment on the linked issue after merge; Jarvis runtime will move linked open issues into the PM close-out path automatically.

## Same-head and merge-conflict rules

1. If the same blocked `headRefOid` returns without a new commit:
   - do not repeat the same full review
   - do not bounce metadata again
   - treat it as waiting for a new head unless the user explicitly asked for a metadata-only recheck
2. If GitHub reports `mergeable=CONFLICTING` or `mergeStateStatus=DIRTY`:
   - do not keep reviewing the same head
   - do not try to resolve the conflict as reviewer
   - hand the PR back to developer to sync `main`, resolve conflicts, and push a new head
3. If the real blocker is dependency ordering, missing scope clarity, missing product decision, or workflow drift rather than code correctness:
   - stop the developer/reviewer bounce
   - return `blocked`
   - clearly hand the PR to `pm` via `question`
4. If the PR already has `need po`, stop and wait for human action.

## Merge close-out rules

1. After merge, clean workflow-only labels such as `in progress`, `in review`, `question`, and `need po`.
2. If the merged PR still links to an open issue, do not kick that issue back to developer just because closure metadata remains.
3. A merged implementation with an open linked issue is a PM close-out case:
   - PM should verify scope completion,
   - close the issue if original scope is done,
   - or split the residual work into follow-up issue(s).
4. Reviewer should not leave the final PR timeline ending on an obsolete blocker if the blocker has already been resolved and merged.
5. Keep the PR close-out summary on the PR thread. Let PM own the linked issue thread if closure or follow-up splitting is still needed.

## Metadata expectations

1. Issue linkage should be explicit in PR title/body/comments.
2. If the PR only has an `issue:<n>` label and no explicit issue reference, call that out as workflow drift.
3. If the PR is going back to the developer, make the next state explicit with `gh` and matching labels when those labels already exist.
4. If there are no remaining blockers, do not stop at "looks good"; merge the PR so the workflow actually moves forward.
