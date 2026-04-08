# Workflow Logic

This file is the shared workflow contract for `developer`, `reviewer`, and `pm` in this repo.

## Sources of workflow truth

1. The canonical dependency/source-of-truth document is `planning/workgraph.yaml`.
2. `pm` is the only role allowed to edit `planning/workgraph.yaml`.
3. `developer` and `reviewer` consume the work graph as read-only workflow input.
4. GitHub issues and PRs must stay consistent with the work graph; when they drift, `pm` fixes the workflow metadata.

## Primary linkage rules

1. The primary issue/PR linkage must be explicit in the PR itself:
   - prefer `Refs #<issue>` in the PR body
   - use `Closes #<issue>` only when merge should actually close that issue
   - issue references in PR title/body/comments are authoritative
2. Labels are secondary workflow metadata. Do not rely on an `issue:<n>` label as the only linkage.
3. If linkage is unclear or missing, `pm` should fix the metadata before more implementation/review churn happens.

## PR states

### Draft PR

A draft PR means one of these:
- active developer work is still happening
- the PR is waiting for an external signal
- the PR needs a concrete question answered before it can proceed
- `pm` still needs to clarify scope / acceptance / dependency / follow-up split

A draft PR does **not** mean it should be re-run forever. The role must decide which of the four cases above is true.

### Ready for review

A ready PR means reviewer action is justified now.
Reviewer should treat this as a real review pass, not a passive status report.

### Question

Use `question` when progress requires a concrete answer, decision, missing credential, missing environment input, missing dependency resolution, or missing scope judgment.
The exact question must be written clearly in the issue or PR comment.
Do not leave `question` vague.
When developer/reviewer detect workflow bounce, they should prefer `question` over another metadata bounce.
Question applies to both PRs and issues; question issues are PM-owned until the workflow state is clarified.

### Need PO

Use `need po` when `pm` has already tried to resolve the same PR head multiple times and the remaining blocker is a product / requirement / priority decision that only a human PO can make.
Once a PR is in `need po`, no automation role should keep processing it.
The PR must wait for human intervention.

### waiting_signal

Use `waiting_signal` when there is no concrete question, but no useful next step exists until some external signal changes:
- a new commit
- a maintainer / PM decision
- a reviewer response
- an environment becoming available
- a dependency in `planning/workgraph.yaml` becoming unblocked

`waiting_signal` is a cooldown / wait state, not a silent dead-end.

### Merged implementation with open linked issue

If a PR is already merged but a linked issue remains open, do not automatically send that issue back to `developer`.
That state usually means one of these:
- PM needs to close the issue because original scope is done
- PM needs to split residual work into follow-up issue(s)
- PM needs to repair workflow metadata or linkage

Treat that path as PM close-out work unless there is still concrete unmerged implementation work.
The canonical close-out thread for that state is the issue thread, not a mirrored PR comment loop.

## Developer rules

1. Resume before rewrite.
2. Read `planning/workgraph.yaml` before choosing between draft PRs and issues.
3. For draft PRs, check:
   - current `headRefOid`
   - latest reviewer outcome
   - labels and PR body/comments
   - whether the PR still belongs to the linked issue scope
   - whether the linked work-graph node is blocked by another node
4. Do not move a PR back to ready on the same blocked head unless there is a real fix or the reviewer explicitly asked for a metadata-only recheck.
5. If there is concrete implementation work left and dependencies are clear, keep moving the PR forward.
6. If only an external signal is missing, return `waiting_signal`.
7. If a concrete answer/decision/input is missing, return `blocked` and move workflow toward `question`.
8. If reviewer and developer are bouncing the same PR head, stop bouncing and hand it to `pm` through `question`.
9. When no suitable draft PR exists, review actionable open issues and choose one using the work graph, not only issue age.
10. Do not reopen issues already in `question` state unless the workflow state was intentionally cleared.
11. If a PR has `need po`, stop and wait for human action.
12. If implementation is already merged and the linked issue is still open, do not create a fresh developer blocker loop unless there is real unmerged code work remaining.

## Reviewer rules

1. Reviewer is read-only for tracked source files.
2. Reviewer may checkout the PR branch or a detached head, but must restore the original branch/HEAD before finishing.
3. Review only ready PRs.
4. Findings first, ordered by severity.
5. If the same blocked `headRefOid` reappears with no new commit, skip a full re-review and treat it as waiting for a new head.
6. Reviewer should not repeatedly bounce metadata on the same head.
7. If the real blocker is workflow scope / dependency / product clarification rather than code correctness, stop bouncing and move the PR to `question` for `pm`.
8. If there are no blockers, merge the PR instead of leaving it stuck in ready state.
9. If a PR has `need po`, stop and wait for human action.
10. After merge, leave a concise close-out summary and let PM handle any remaining linked-issue closure/follow-up decision.
11. Do not manually duplicate the linked-issue handoff on the issue thread after merge; Jarvis runtime already creates that handoff.

## PM rules

1. `pm` intervenes when question issues or draft/question PRs bounce because scope, acceptance, dependency ordering, linkage, or validation expectations are unclear.
2. `pm` may also intervene when developer/reviewer both have no actionable work but the repo still needs workflow cleanup.
3. `pm` is the only role allowed to edit `planning/workgraph.yaml`.
4. Prefer metadata and workflow fixes over source-code edits:
   - `planning/workgraph.yaml`
   - PR body/title/comments
   - issue body/comments
   - follow-up issue split
   - question wording
5. `pm` should decide whether the current issue/PR snapshot is:
   - still active developer work
   - waiting for an external signal
   - blocked by a concrete missing decision
   - already complete for original scope, with extra work split out
6. If reviewer-side credentialed OpenAI validation is required, tell the reviewer to read the needed token/config from `~/.env`.
7. If `pm` cannot resolve the same PR head after repeated passes, escalate it to `need po` and stop automation on that PR.
8. PM owns merged-PR close-out when a linked issue stays open after implementation merged.
9. For merged-PR close-out, PM should normally comment on the issue thread only; avoid mirroring the same close-out summary onto the merged PR unless a PR-specific clarification is required.

## Completion states

Use these output states consistently:
- `done`: this role completed its useful work for the current snapshot
- `continue`: there is still concrete work this same role can do now
- `waiting_signal`: no concrete action until an external signal changes
- `blocked`: a concrete answer/decision/input is required
