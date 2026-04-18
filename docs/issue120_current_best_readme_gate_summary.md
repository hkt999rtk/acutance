# Issue 120 Current Best README Gate Summary

Issue `#120` refreshes the canonical current-best record after issue `#118` / PR `#119`.

## Current Best

- Current best canonical-target candidate: issue `#118` / PR `#119` at commit `52bbca7`.
- Candidate profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_computer_monitor_small_print_large_print_pr30_input_profile.json`
- Baseline comparison branch: PR `#30` (`current_best_pr30_branch`).
- This is not a release-facing config promotion; fitted outputs remain under `algo/` and `artifacts/`.

## PR 119 Versus PR 30

| Metric | PR 30 | PR 119 | Delta |
| --- | --- | --- | --- |
| Curve MAE | 0.03679 | 0.03280 | -0.00399 |
| Focus Acu MAE | 0.04249 | 0.02892 | -0.01357 |
| Overall Quality Loss | 1.22150 | 1.20436 | -0.01714 |
| MTF20 | 0.03301 | 0.03301 | +0.00000 |
| MTF30 | 0.03694 | 0.03694 | +0.00000 |
| MTF50 | 0.00933 | 0.00933 | +0.00000 |

## README Gate Status

| Gate | Value | Threshold | Status |
| --- | --- | --- | --- |
| curve_mae_mean | 0.03280 | <= 0.02000 | miss |
| focus_preset_acutance_mae_mean | 0.02892 | <= 0.03000 | pass |
| overall_quality_loss_mae_mean | 1.20436 | <= 1.30000 | pass |
| non-Phone Acutance max (Small Print Acutance) | 0.03173 | <= 0.03000 | miss |
| 5.5" Phone Display Acutance | 0.03526 | <= 0.05000 | pass |

Remaining README misses:

- `curve_mae_mean <= 0.020` still misses because PR #119 is `0.03280`.
- Non-Phone Acutance still misses only at `Small Print Acutance = 0.03173` against the `<= 0.030` gate.

## Next Handoff

- Mode: `developer_discovery`
- Selected slice id: `issue118_remaining_curve_small_print_acutance_discovery`
- Goal: Use the issue #118 profile and checked-in per-sample/benchmark artifacts to decide whether the remaining curve MAE miss and Small Print Acutance miss can be handled by one bounded acutance-side/readout-boundary implementation, or whether they must be split.
- Why discovery first: The issue #118 branch already passes focus-preset Acutance mean, Phone, overall Quality Loss, and reported-MTF checks. The remaining failures are cross-family: curve MAE is still far above the README threshold, while only Small Print exceeds the non-Phone Acutance preset gate by a small margin. Issue #120 explicitly rules out another broad Quality Loss or readout retune, so the next implementable slice needs evidence mining before code changes.

Acceptance criteria for the next slice:

- Identify one source-backed knob or boundary that targets either the curve MAE miss or the Small Print Acutance miss without broad retuning.
- Show whether the selected slice is expected to preserve the PR #119 Quality Loss and reported-MTF record.
- Record explicit pass/miss deltas against README gates and PR #119.

Validation plan:

- Regenerate the relevant acutance/Quality Loss benchmark artifact on the issue #118 profile family.
- Compare curve MAE, focus-preset Acutance mean, per-preset Acutance, overall Quality Loss, and MTF thresholds against PR #119.
- Keep fitted artifacts under algo/ and artifacts/ only; do not promote release-facing configs.

## Release Separation

- The issue #118 / PR #119 profile is a canonical-target candidate, not a release-facing config promotion.
- Do not copy fitted outputs into golden/reference data roots or release config roots.
- Release-facing configs remain separate until a later bounded implementation clears README gates.
