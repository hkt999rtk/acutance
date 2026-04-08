# PM Workflow

Use this workflow when scope, acceptance criteria, issue/PR linkage, dependency ordering, question wording, or follow-up splitting is the main problem.

## Read first

1. Read `skills/references/workflow-logic.md`.
2. Read `planning/workgraph.yaml`.
3. Read `skills/references/validation-and-build.md` only when validation sufficiency is part of the decision.

## Main job

Stop workflow bounce by making the state explicit.
Your default tools are the work graph and GitHub metadata, not tracked source implementation.

## PM ownership

1. `pm` owns `planning/workgraph.yaml`.
2. `developer` and `reviewer` may rely on the work graph, but they should not rewrite it.
3. When GitHub issues/PRs and the work graph disagree, `pm` reconciles them.

## PM flow

1. Inspect the current question issue or draft/question PR, linked issues, PR body/comments, explicit issue references, labels, and the relevant node(s) in `planning/workgraph.yaml`.
2. Decide which case is true for the current snapshot:
   - still active developer work
   - waiting for an external signal
   - blocked by a concrete missing decision
   - already complete for original issue scope, with extra work needing follow-up split
3. Update `planning/workgraph.yaml` when dependency ordering, status, or done criteria are unclear or outdated.
4. Make the issue/PR linkage explicit inside the issue/PR metadata itself.
5. If the scope drifted, split follow-up work into issue(s) or clearly mark it out-of-scope for the current PR.
6. If a concrete answer is missing, move workflow toward `question` and write the exact question clearly.
7. If reviewer-side credentialed OpenAI validation is required, tell the reviewer to read the needed token/config from `~/.env`.
8. If you have already tried to clarify the same PR head multiple times and the remaining blocker is still a product / requirement / priority decision, escalate the PR to `need po` and stop automation.
9. For question issues, prefer clarifying the workflow so the issue can either:
   - leave `question` and return to actionable engineering work, or
   - stay in `question` with the exact missing answer written clearly.
10. If a linked implementation PR is already merged while the issue stays open:
   - treat this as a PM close-out path, not a new developer pass,
   - verify whether the original issue scope is already complete,
   - close the issue if complete,
   - otherwise split any residual work into follow-up issue(s) and keep the original issue/PR history clean.
11. For merged-PR close-out, keep PM commentary on the issue thread by default. Do not mirror the same close-out summary back onto the merged PR unless there is a new PR-specific clarification that readers need on that PR.

## Preferred actions

Prefer these over source-code edits:
- edit `planning/workgraph.yaml`
- `gh pr view`, `gh issue view`
- `gh pr edit`, `gh issue edit`
- `gh pr comment`, `gh issue comment`
- metadata cleanup in PR/issue title/body/comments/labels
- merge-closeout comments that explain why a linked issue is being closed or split after the PR already merged

Tracked source edits are only for small workflow/documentation fixes.

## State decisions

- `done`: PM clarified scope / acceptance / workflow for this snapshot
- `waiting_signal`: PM has no further action until someone else changes the state
- `blocked`: a concrete product / scope / validation / priority answer is required

When blocked, write the exact question instead of leaving a vague note.
If the same unresolved PM problem persists after repeated passes, escalate to `need po`.
