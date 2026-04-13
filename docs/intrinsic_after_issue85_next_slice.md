# Intrinsic After Issue 85 Next Slice

This note records the issue `#87` developer-discovery pass after issue `#85` / PR `#86` proved that the intrinsic line can reconnect the readout path without giving back the issue-81 downstream Quality Loss isolation gains.

## Selected Slice

- Selected slice: `phase_retained_intrinsic_matched_ori_correction_graft_with_quality_loss_isolation`
- Summary: Keep issue #85's phase-retained intrinsic transfer, readout reconnect, and downstream Quality Loss isolation, but graft the current-best PR30 matched-ori correction / acutance-anchor family onto the readout path and the isolated Quality Loss branch.
- Prior narrowing lineage: issue `#83` selected `phase_retained_intrinsic_readout_reconnect_with_quality_loss_isolation`, and issue `#85` implemented it successfully.
- Remaining gap location: the surviving `overall_quality_loss_mae_mean` and `mtf20` gaps now point to the still-missing matched-ori downstream correction / anchor family, not to a new intrinsic transfer family.

## Comparison Table

| Record | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel | Quality Loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_best_pr30_branch | 0.03679 | 0.04249 | 1.22150 | 0.03301 | 0.03694 | 0.00933 | 0.08671 | Current best branch; already carries the matched-ori downstream correction stack. |
| issue47_phase_retained_replace_all | 0.03280 | 0.02892 | 14.47576 | 0.08577 | 0.01789 | 0.00720 | 0.13994 | Phase-retained intrinsic baseline; its readout metrics exactly match issue #85. |
| issue81_quality_loss_isolation_candidate | 0.03280 | 0.02892 | 8.02054 | 0.07456 | 0.07570 | 0.03462 | 0.37917 | Quality Loss isolation landed; its overall Quality Loss metrics exactly match issue #85. |
| issue85_readout_reconnect_quality_loss_isolation_candidate | 0.03280 | 0.02892 | 8.02054 | 0.08577 | 0.01789 | 0.00720 | 0.13994 | Readout reconnect landed; residual `mtf20` / overall Quality Loss gap still remains. |

## Why The Gap Still Remains After Issue 85

- Issue #85's `overall_quality_loss_mae_mean` is exactly equal to issue #81, including the per-preset Quality Loss errors, so the remaining overall Quality Loss gap did not move when readout reconnect landed.
- Issue #85's `mtf_abs_signed_rel_mean`, threshold errors, and MTF band errors are exactly equal to issue #47, so the residual `mtf20` gap also predates issue #85's split and stays on the readout side.
- The current-best PR30 branch carries a tuned matched-ori reference-correction family and acutance-anchor family that issue #85 does not enable, which is the largest still-untried downstream boundary shared by the remaining `overall_quality_loss_mae_mean` and `mtf20` gaps.
- The low-band MTF MAE on issue #85 is already better than PR30, yet `mtf20` is still farther away. That points to threshold-crossing / correction-shape behavior rather than to a missing wholesale intrinsic transfer family.

## Residual Alignment Evidence

- Issue `#85` and issue `#81` have identical overall Quality Loss MAE: `8.02054`.
- Issue `#85` and issue `#47` have identical `mtf_abs_signed_rel_mean`: `0.13994`.
- Issue `#85` Quality Loss focus-preset MAE mean also matches issue `#81`: `8.02054`.

### Issue 85 Quality Loss Preset Errors

| Preset | PR30 | Issue47 | Issue81 | Issue85 |
| --- | --- | --- | --- | --- |
| 5.5" Phone Display Quality Loss | 0.14298 | 60.77411 | 0.54696 | 0.54696 |
| Computer Monitor Quality Loss | 2.90291 | 5.98020 | 20.18458 | 20.18458 |
| Large Print Quality Loss | 0.95482 | 1.75927 | 5.95818 | 5.95818 |
| Small Print Quality Loss | 0.60769 | 1.53368 | 8.66719 | 8.66719 |
| UHDTV Display Quality Loss | 1.49910 | 2.33154 | 4.74581 | 4.74581 |

### Issue 85 MTF Band Errors

| Band | PR30 | Issue47 | Issue81 | Issue85 |
| --- | --- | --- | --- | --- |
| low | 0.03705 | 0.00935 | 0.07904 | 0.00935 |
| mid | 0.03899 | 0.04533 | 0.11518 | 0.04533 |
| high | 0.01765 | 0.04654 | 0.09587 | 0.04654 |
| top | 0.07374 | 0.04557 | 0.26035 | 0.04557 |

## Pipeline Gap Versus PR30

The current-best PR30 branch still carries the matched-ori correction / anchor family that issue `#85` does not enable:

- `matched_ori_reference_anchor`: PR30=True, issue85=False
- `matched_ori_strength_curve_frequencies`: PR30=[0.0, 0.12, 0.22, 0.35, 0.5], issue85=None
- `matched_ori_strength_curve_values`: PR30=[1.0, 1.0, 0.82, 0.95, 1.0], issue85=None
- `matched_ori_acutance_reference_anchor`: PR30=True, issue85=False
- `matched_ori_acutance_strength_curve_relative_scales`: PR30=[0.0, 0.2, 0.8, 1.6, 2.5], issue85=None
- `matched_ori_acutance_strength_curve_values`: PR30=[0.7, 0.69, 0.64, 0.62, 0.6], issue85=None
- `matched_ori_acutance_curve_correction_clip_hi_relative_scales`: PR30=[0.0, 0.25, 0.6, 0.8, 1.6, 2.5], issue85=None
- `matched_ori_acutance_curve_correction_clip_hi_values`: PR30=[1.02, 1.03, 0.895, 0.895, 1.05, 1.06], issue85=None
- `matched_ori_acutance_preset_correction_delta_power_relative_scales`: PR30=[0.0, 4.5, 5.8, 6.2], issue85=None
- `matched_ori_acutance_preset_correction_delta_power_values`: PR30=[1.05, 1.05, 1.85, 1.85], issue85=None
- `matched_ori_acutance_preset_strength_curve_relative_scales`: PR30=[0.0, 3.0, 4.5, 5.8, 6.2], issue85=None
- `matched_ori_acutance_preset_strength_curve_values`: PR30=[1.0, 1.0, 0.85, 0.45, 0.45], issue85=None

## Runtime Boundary Evidence

### `algo/benchmark_parity_psd_mtf.py` (502-508, 509-653, 654-659)

- Issue #85 already reconnects the phase-retained intrinsic branch into `compensated_mtf` when the scope is `readout_reconnect_quality_loss_isolation`.
- The matched-ori reference correction then applies directly to both `compensated_mtf` and `compensated_mtf_for_acutance`, so the next bounded slice can target readout correction without touching the intrinsic transfer derivation.
- `compute_mtf_metrics(...)` still reads thresholds from the corrected `compensated_mtf`, which makes this the narrowest live boundary for the residual `mtf20` gap.

### `algo/benchmark_parity_acutance_quality_loss.py` (329-337, 745-869, 921-948, 1003-1008)

- `maybe_anchor_acutance_results(...)` is gated by `matched_ori_acutance_reference_anchor`, and it runs on both the main acutance path and the isolated Quality Loss acutance path.
- The matched-ori reference correction also applies to `quality_loss_compensated_mtf_for_acutance`, which means one bounded graft can influence both the residual overall Quality Loss gap and the readout-side threshold shape.
- `quality_loss_presets_from_acutance(...)` consumes that isolated downstream acutance path after correction and anchoring, so the next issue can stay bounded to downstream correction/anchor behavior rather than reopening intrinsic transfer or OECF work.

## Excluded Routes

### promote issue-85 scope as-is

- Issue #85 is a real bounded positive, but it still trails PR #30 materially on `overall_quality_loss_mae_mean` and does not improve `mtf20` toward the current best branch.
- Promoting it without another narrowing pass would skip the exact residual gaps this issue was created to isolate.

### reopen measured OECF

- Measured OECF already closed as a bounded negative in issue #77 / PR #78.
- Issue #87 is downstream of issue #85's intrinsic split result, and the surviving gap maps to correction / anchor boundaries that already exist in the repo.

### rerun affine-registration intrinsic variant

- Affine registration was already dominated by the phase-correlation intrinsic path and is still explicitly out of scope for this narrowing pass.
- The issue-85 residuals match earlier branches exactly, which points to post-transfer downstream correction rather than to registration choice.

### restart an unbounded intrinsic family search

- Issue #87 is a developer-discovery narrowing pass, not a license to reopen the full intrinsic search tree.
- The repo already contains one implementable next slice with code-level boundary evidence, so broader family churn would be workflow regress rather than progress.

## Implementation Boundary

- Keep issue #85's `readout_reconnect_quality_loss_isolation` topology and `radial_real_mean` / `phase_correlation` intrinsic path unchanged.
- Add one bounded mode or profile family that grafts PR30's matched-ori reference correction onto the issue-85 readout path, including the `matched_ori_reference_anchor` strength-curve settings used around `compensated_mtf`.
- Apply the same bounded graft to the isolated downstream Quality Loss path, including the `matched_ori_acutance_reference_anchor` family that runs through `maybe_anchor_acutance_results(...)`.
- Keep downstream Quality Loss isolated off the non-intrinsic branch; do not collapse back to `replace_all`.

## Explicit Non-Changes

- Do not change intrinsic transfer mode, registration mode, or restart a wider intrinsic-family sweep.
- Do not reopen measured OECF or affine-registration branches.
- Do not retune release-facing PR30 coefficients directly or promote any fitted intrinsic profile into release-facing config in this issue.
- Do not write fitted profiles, transfer tables, or generated outputs under `20260318_deadleaf_13b10` or `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`
- Fitted artifact roots: `algo/*.json`, `artifacts/*.json`
- Release config roots: `release/deadleaf_13b10_release/config/*.json`
- Keep this issue's discovery outputs under `docs/` and `artifacts/` only.
- Do not write new fitted intrinsic profiles, transfer tables, or benchmark outputs under the golden/reference roots.
- Do not touch release-facing configs until a later bounded implementation actually clears the current README-facing guardrails.

## Acceptance For The Next Implementation Issue

- The new bounded graft preserves issue #85's curve and focus-preset Acutance gains closely enough that `curve_mae_mean` and `focus_preset_acutance_mae_mean` are no worse than issue #85.
- The same implementation improves `overall_quality_loss_mae_mean` versus issue #85 while keeping the isolated downstream Quality Loss routing intact.
- The same implementation improves `mtf20` toward the current PR #30 branch versus issue #85 and does not give back the issue-85 `mtf_abs_signed_rel_mean` improvement.
- All new fitted outputs remain under `algo/` or `artifacts/`, not under golden/reference roots or release-facing config roots.

## Validation Plan For The Next Implementation Issue

- Run `python3 -m algo.benchmark_parity_psd_mtf ...` on an issue-85-based profile that enables the bounded matched-ori correction graft, then compare thresholds and `mtf_abs_signed_rel_mean` against issue #85 and PR #30.
- Run `python3 -m algo.benchmark_parity_acutance_quality_loss ...` on the same profile/scope pair to confirm `overall_quality_loss_mae_mean` improves without collapsing the isolated downstream branch.
- Add focused tests that cover the graft across `compensated_mtf`, `compensated_mtf_for_acutance`, `quality_loss_compensated_mtf_for_acutance`, and `maybe_anchor_acutance_results(...)`.
