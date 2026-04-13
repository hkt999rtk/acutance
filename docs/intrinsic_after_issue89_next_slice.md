# Intrinsic After Issue 89 Next Slice

This note records the issue `#91` developer-discovery pass after issue `#89` / PR `#90` proved that the matched-ori graft contains a real downstream Quality Loss win and a separate readout-side regression.

## Selected Slice

- Selected slice: `phase_retained_intrinsic_quality_loss_only_matched_ori_graft_without_readout_correction`
- Summary: Keep issue #85's phase-retained intrinsic transfer, readout reconnect, and downstream Quality Loss isolation, but carry forward only issue #89's matched-ori correction / acutance-anchor on the isolated downstream Quality Loss branch. Do not reapply matched-ori reference correction to the reported-MTF/readout path.
- Prior narrowing lineage: issue `#87` selected `phase_retained_intrinsic_matched_ori_correction_graft_with_quality_loss_isolation`, and issue `#89` implemented that combined graft successfully enough to expose the remaining sub-boundary split.
- Remaining gap location: the residual tradeoff is no longer a whole matched-ori family question. It now sits between the readout-side reference correction on `compensated_mtf` and the isolated downstream Quality Loss correction / anchor path.

## Comparison Table

| Record | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel | Reading |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_best_pr30_branch | 0.03679 | 0.04249 | 1.22150 | 0.03301 | 0.03694 | 0.00933 | 0.08671 | Current best PR30 branch. |
| issue81_quality_loss_isolation_candidate | 0.03280 | 0.02892 | 8.02054 | 0.07456 | 0.07570 | 0.03462 | 0.37917 | Phase-retained intrinsic with downstream Quality Loss isolation only. |
| issue85_readout_reconnect_quality_loss_isolation_candidate | 0.03280 | 0.02892 | 8.02054 | 0.08577 | 0.01789 | 0.00720 | 0.13994 | Issue-81 plus readout reconnect; Quality Loss still unchanged from issue-81. |
| issue89_matched_ori_graft_candidate | 0.03280 | 0.02892 | 3.94743 | 0.09532 | 0.11756 | 0.07657 | 0.74771 | Issue-85 plus matched-ori graft; Quality Loss improves, readout regresses. |

## Residual Tradeoff Evidence

- Issue #89 preserves issue #85 `curve_mae_mean`: `True`
- Issue #89 preserves issue #85 `focus_preset_acutance_mae_mean`: `True`
- Issue #89 improves overall Quality Loss versus issue #85: `True`
- Issue #89 overall Quality Loss delta versus issue #85: `-4.07311`
- Issue #89 regresses `mtf_abs_signed_rel_mean` versus issue #85: `True`
- Issue #89 threshold regressions versus issue #85: `mtf20=True`, `mtf30=True`, `mtf50=True`

## Pipeline Delta Between Issue 85 And Issue 89

- `intrinsic_full_reference_scope`: issue85='readout_reconnect_quality_loss_isolation', issue89='readout_reconnect_quality_loss_isolation_matched_ori_graft'
- `matched_ori_acutance_curve_correction_clip_hi`: issue85=None, issue89=1.04
- `matched_ori_acutance_curve_correction_clip_hi_relative_scales`: issue85=None, issue89=[0.0, 0.25, 0.6, 0.8, 1.6, 2.5]
- `matched_ori_acutance_curve_correction_clip_hi_values`: issue85=None, issue89=[1.02, 1.03, 0.895, 0.895, 1.05, 1.06]
- `matched_ori_acutance_curve_correction_delta_power`: issue85=None, issue89=0.95
- `matched_ori_acutance_preset_correction_delta_power_relative_scales`: issue85=None, issue89=[0.0, 4.5, 5.8, 6.2]
- `matched_ori_acutance_preset_correction_delta_power_values`: issue85=None, issue89=[1.05, 1.05, 1.85, 1.85]
- `matched_ori_acutance_preset_strength_curve_relative_scales`: issue85=None, issue89=[0.0, 3.0, 4.5, 5.8, 6.2]
- `matched_ori_acutance_preset_strength_curve_values`: issue85=None, issue89=[1.0, 1.0, 0.85, 0.45, 0.45]
- `matched_ori_acutance_reference_anchor`: issue85=False, issue89=True
- `matched_ori_acutance_strength_curve_relative_scales`: issue85=None, issue89=[0.0, 0.2, 0.8, 1.6, 2.5]
- `matched_ori_acutance_strength_curve_values`: issue85=None, issue89=[0.7, 0.69, 0.64, 0.62, 0.6]
- `matched_ori_reference_anchor`: issue85=False, issue89=True
- `matched_ori_strength_curve_frequencies`: issue85=None, issue89=[0.0, 0.12, 0.22, 0.35, 0.5]
- `matched_ori_strength_curve_values`: issue85=None, issue89=[1.0, 1.0, 0.82, 0.95, 1.0]

## Why The Next Slice Is Smaller Than Issue 89

- Issue #89 preserves issue #85's `curve_mae_mean` and `focus_preset_acutance_mae_mean` exactly, so the residual tradeoff does not require reopening the main intrinsic curve/acutance branch.
- Issue #89 still improves `overall_quality_loss_mae_mean` versus both issue #81 and issue #85 by `4.07311`, which means the matched-ori value that appeared in issue #89 is downstream and real rather than noise from the readout reconnect itself.
- Issue #89 simultaneously regresses `mtf_abs_signed_rel_mean` by `0.60778` versus issue #85, and all three threshold errors (`mtf20`, `mtf30`, `mtf50`) get worse. That points to the readout-side matched-ori reference correction on `compensated_mtf`, not to the isolated Quality Loss branch.
- The changed pipeline keys from issue #85 to issue #89 are entirely the matched-ori reference-correction and acutance-anchor families, so the next narrowing pass can stay bounded to those subfamilies instead of reopening intrinsic transfer, measured OECF, or registration choice.

## Runtime Boundary Evidence

### `algo/benchmark_parity_psd_mtf.py` (504-653, 684-689)

- For `readout_reconnect_quality_loss_isolation_matched_ori_graft`, the intrinsic branch is still connected into `compensated_mtf`, and `apply_readout_correction` becomes true only for this scope.
- That branch applies `apply_reference_correction_curve(...)` directly to `compensated_mtf` using the matched-ori strength-curve settings.
- `compute_mtf_metrics(...)` then reads thresholds from the corrected `compensated_mtf`, so this is the narrowest live boundary for the issue-89 readout regression.

### `algo/benchmark_parity_acutance_quality_loss.py` (843-862, 922-953, 1003-1008)

- For the issue-89 scope, the main `compensated_mtf_for_acutance` correction path is skipped, and the main curve/acutance path also skips `maybe_anchor_acutance_results(...)`.
- The isolated downstream branch still applies matched-ori correction to `quality_loss_compensated_mtf_for_acutance`, and `quality_loss_acutance` still passes through `maybe_anchor_acutance_results(...)`.
- `quality_loss_presets_from_acutance(...)` consumes only that isolated downstream branch, so the next bounded slice can preserve the issue-89 Quality Loss gain while leaving readout and the main acutance path unchanged.

## Implementation Boundary

- Keep issue #85's `readout_reconnect_quality_loss_isolation` topology and the existing phase-retained intrinsic transfer / registration path unchanged.
- Add one bounded scope or profile family that enables the issue-89 matched-ori correction curve only on `quality_loss_compensated_mtf_for_acutance` and keeps the downstream `matched_ori_acutance_reference_anchor` path active for `quality_loss_acutance` only.
- Do not apply matched-ori reference correction to `compensated_mtf`, and do not change the reported-MTF/readout threshold extraction path.
- Do not enable matched-ori correction or anchoring on the main `compensated_mtf_for_acutance` / curve / preset path.

## Explicit Non-Changes

- Do not change intrinsic transfer mode, registration mode, or restart a wider intrinsic-family sweep.
- Do not reopen measured OECF or affine-registration variants.
- Do not reapply the full issue-89 readout+Quality-Loss graft to the readout path, and do not promote issue #89 as a main-line branch.
- Do not retune release-facing PR30 coefficients directly or write fitted outputs under `20260318_deadleaf_13b10` or `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`.

## Excluded Routes

### `reapply_issue89_readout_and_quality_loss_graft_as_is`

- Route: reapply the full issue-89 readout+Quality-Loss graft as-is
- Issue #89 already established that the full graft materially improves Quality Loss but sharply regresses the readout path.
- Repeating the same combined boundary would not narrow the residual tradeoff any further.

### `expand_matched_ori_into_main_acutance_branch`

- Route: expand matched-ori correction / anchor into the main acutance branch
- Issue #89 preserves issue #85's curve and focus-preset Acutance exactly while already skipping the main-branch matched-ori acutance correction / anchor path.
- That means the remaining tradeoff is not asking for more matched-ori churn on the main acutance branch.

### `reopen_measured_oecf_family`

- Route: reopen measured OECF
- Measured OECF already closed as a bounded negative in issue #77 / PR #78.
- Issue #91 is downstream of issue #89's matched-ori split result, and the remaining evidence is entirely inside the existing matched-ori boundary.

### `rerun_affine_registration_intrinsic`

- Route: rerun affine-registration intrinsic variant
- Affine registration was already dominated by the phase-correlation intrinsic path and remains out of scope for this narrowing pass.
- Issue #89 changed only matched-ori correction / anchor fields, so registration choice is not the live residual question.

### `restart_unbounded_matched_ori_inventory`

- Route: restart an unbounded matched-ori family search
- Issue #91 is a developer-discovery narrowing pass, not a license to reopen the whole matched-ori family inventory.
- The repo already contains one implementable next slice with code-level evidence that splits the readout and downstream Quality Loss sub-boundaries.

## Acceptance For The Next Implementation Issue

- The new bounded implementation keeps `curve_mae_mean` and `focus_preset_acutance_mae_mean` no worse than issue #85.
- The same implementation improves `overall_quality_loss_mae_mean` versus issue #85 while preserving downstream Quality Loss isolation.
- The same implementation keeps `mtf20` and `mtf_abs_signed_rel_mean` no worse than issue #85 because the readout path is no longer matched-ori corrected.
- All new fitted outputs remain under `algo/` or `artifacts/`, not under golden/reference roots or release-facing config roots.

## Validation Plan For The Next Implementation Issue

- Run `python3 -m algo.benchmark_parity_acutance_quality_loss ...` on an issue-85-based profile that enables only the isolated downstream matched-ori correction / anchor path, then compare `overall_quality_loss_mae_mean` against issue #85 and issue #89.
- Run `python3 -m algo.benchmark_parity_psd_mtf ...` on the same scope to confirm `mtf20`, `mtf30`, `mtf50`, and `mtf_abs_signed_rel_mean` stay at or below issue #85 instead of replaying issue #89's regression.
- Add focused tests that prove `compensated_mtf` and the main acutance branch stay untouched while `quality_loss_compensated_mtf_for_acutance` and `quality_loss_acutance` still receive the bounded matched-ori subfamily.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`
- Fitted artifact roots: `algo/*.json`, `artifacts/*.json`
- Release config roots: `release/deadleaf_13b10_release/config/*.json`
- Keep this issue's discovery outputs under `docs/` and `artifacts/` only.
- Do not write new fitted intrinsic profiles, transfer tables, or benchmark outputs under the golden/reference roots.
- Do not touch release-facing configs until a later bounded implementation actually clears the current README-facing guardrails.
