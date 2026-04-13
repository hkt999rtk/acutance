# Intrinsic After Issue 97 Next Slice

This note records the issue `#99` developer-discovery pass after issue `#97` / PR `#98` proved that disconnecting reported-MTF thresholds from the intrinsic reconnect preserves the issue-93 curve/focus/Quality Loss record but still leaves a residual reported-MTF/readout failure mode.

## Selected Slice

- Selected slice: `issue97_topology_add_readout_only_sensor_aperture_compensation`
- Summary: Keep issue #97's observed reported-MTF threshold branch and issue #93's downstream-only matched-ori Quality Loss branch unchanged, but restore sensor-aperture MTF compensation only on the reported-MTF/readout path before `compute_mtf_metrics(...)`. Use the PR #30 readout compensation settings (`sensor_aperture_sinc`, `sensor_fill_factor=1.5`) only on that branch, while leaving `compensated_mtf_for_acutance` and `quality_loss_compensated_mtf_for_acutance` on the existing issue-97 topology.
- Prior narrowing lineage: issue `#95` / PR `#96` selected `issue93_topology_keep_downstream_quality_loss_branch_but_disconnect_reported_mtf_from_intrinsic_reconnect`, and issue `#97` / PR `#98` completed that implementation cleanly enough to expose the next remaining boundary.
- Remaining gap location: after issue #97, the downstream-only matched-ori Quality Loss win is already preserved and the reported-MTF branch is already disconnected from intrinsic reconnect. The next minimum slice is now the readout-only compensation boundary on the observed branch.

## Comparison Table

| Record | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel | Reading |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_best_pr30_branch | 0.03679 | 0.04249 | 1.22150 | 0.03301 | 0.03694 | 0.00933 | 0.08671 | Current best PR30 branch. |
| issue93_downstream_matched_ori_only_candidate | 0.03280 | 0.02892 | 3.94743 | 0.08577 | 0.01789 | 0.00720 | 0.13994 | Issue-93 bounded positive baseline from PR #94. |
| issue97_reported_mtf_disconnect_candidate | 0.03280 | 0.02892 | 3.94743 | 0.07448 | 0.07553 | 0.03429 | 0.37688 | Issue-97 reported-MTF disconnect result from PR #98. |

## Residual Gap Evidence

- Issue #97 preserves issue #93 `curve_mae_mean`: `True`
- Issue #97 preserves issue #93 `focus_preset_acutance_mae_mean`: `True`
- Issue #97 preserves issue #93 `overall_quality_loss_mae_mean`: `True`
- Issue #97 improves issue #93 `mtf20`: `True`
- Issue #97 regresses issue #93 `mtf30`: `True`
- Issue #97 regresses issue #93 `mtf50`: `True`
- Issue #97 regresses issue #93 `mtf_abs_signed_rel_mean`: `True`

## Band Direction Evidence

- `low` signed-rel mean: pr30=0.02379, issue93=-0.00365, issue97=-0.09685, `issue97_flips_negative_vs_issue93=False`
- `mid` signed-rel mean: pr30=0.10965, issue93=0.10027, issue97=-0.28413, `issue97_flips_negative_vs_issue93=True`
- `high` signed-rel mean: pr30=0.04983, issue93=0.35027, issue97=-0.41914, `issue97_flips_negative_vs_issue93=True`
- `top` signed-rel mean: pr30=-0.16358, issue93=0.10557, issue97=-0.70739, `issue97_flips_negative_vs_issue93=True`

## Pipeline Delta Between Issue 97 And PR30

- `calibration_file`: issue97='algo/deadleaf_13b10_psd_calibration.json', pr30='algo/deadleaf_13b10_psd_calibration_anchored.json'
- `high_frequency_guard_start_cpp`: issue97=None, pr30=0.36
- `intrinsic_full_reference_mode`: issue97='paired_ori_transfer', pr30='none'
- `intrinsic_full_reference_scope`: issue97='reported_mtf_disconnect_quality_loss_isolation_downstream_matched_ori_only', pr30='replace_all'
- `intrinsic_full_reference_transfer_mode`: issue97='radial_real_mean', pr30='magnitude_ratio'
- `matched_ori_anchor_mode`: issue97='all', pr30='acutance_only'
- `mtf_compensation_mode`: issue97='none', pr30='sensor_aperture_sinc'
- `sensor_fill_factor`: issue97=1.0, pr30=1.5
- `texture_support_scale`: issue97=False, pr30=True

## Why The Next Slice Is Readout-Only Sensor-Aperture Compensation

- Issue #97 preserves issue #93's `curve_mae_mean`, `focus_preset_acutance_mae_mean`, and `overall_quality_loss_mae_mean` exactly, so the downstream-only matched-ori Quality Loss branch remains correctly isolated and does not need to be reopened.
- Issue #97 improves `mtf20` versus issue #93, but it regresses `mtf_abs_signed_rel_mean`, `mtf30`, and `mtf50`, which means the disconnect boundary moved the reported-MTF readout path in the right direction only for the lowest threshold and still left a residual readout-only failure mode.
- In the raw PSD output, issue #97 flips every signed-relative band negative (`low`, `mid`, `high`, `top`), while issue #93 was positive in `mid`, `high`, and `top`. That is a directional underestimation pattern on the observed readout curve rather than a Quality Loss branch interaction.
- The current PR #30 branch differs from issue #97 on several readout-adjacent knobs, but `mtf_compensation_mode='sensor_aperture_sinc'` plus `sensor_fill_factor=1.5` is the narrowest one that directly changes readout-curve amplitude before threshold extraction. `high_frequency_guard_start_cpp`, anchored calibration, and `texture_support_scale` are broader upstream or axis-scaling changes.
- Issue #97 still keeps `readout_smoothing_window=1` and `readout_interpolation='linear'`, matching PR #30 already, so the remaining failure mode is not in the final threshold smoother/interpolator pair.

## Runtime Boundary Evidence

### `algo/benchmark_parity_psd_mtf.py` (425-435, 686-730)

- The PSD driver builds `compensated_mtf` and `compensated_mtf_for_acutance` from the same profile-wide `mtf_compensation_mode` before any intrinsic or matched-ori branching happens.
- `compute_mtf_metrics(...)` and `band_error_summary(...)` later consume only `readout_scaled_frequencies` plus `compensated_mtf`, so a dedicated readout-only compensation variable would directly isolate the remaining failure mode without touching the acutance branches.
- Issue #97 already leaves `compensated_mtf` on the observed branch by not overwriting it with `intrinsic_mtf`; the next minimum slice is therefore to change the readout compensation boundary on that observed branch, not to reconnect intrinsic MTF again.

### `algo/benchmark_parity_acutance_quality_loss.py` (741-747, 866-972)

- The acutance/quality-loss driver already keeps `quality_loss_compensated_mtf_for_acutance` separate from the main acutance branch and anchors it later on the downstream-only matched-ori path.
- Because issue #97 preserves the issue-93 topology here, a readout-only compensation graft in the PSD driver can leave `compensated_mtf_for_acutance` and `quality_loss_compensated_mtf_for_acutance` untouched.
- This makes readout-only sensor-aperture compensation the smallest implementation that can target the remaining reported-MTF failure mode while preserving issue #97's curve/focus/Quality Loss record.

## Implementation Boundary

- Keep issue #97's `reported_mtf_disconnect_quality_loss_isolation_downstream_matched_ori_only` topology, intrinsic transfer, registration mode, and downstream-only matched-ori Quality Loss branch unchanged.
- Add one bounded scope or profile family that computes a readout-only `sensor_aperture_sinc` compensation path with `sensor_fill_factor=1.5` for the observed reported-MTF branch consumed by `compute_mtf_metrics(...)` and `band_error_summary(...)`.
- Leave `compensated_mtf_for_acutance` and `quality_loss_compensated_mtf_for_acutance` on the existing issue-97 branches; do not yet enable anchored calibration, `texture_support_scale`, or `high_frequency_guard_start_cpp`.

## Explicit Non-Changes

- Do not reopen the issue-97 reported-MTF disconnect boundary or route thresholds back through the intrinsic reconnect path.
- Do not touch the downstream-only matched-ori Quality Loss branch, the main acutance branch, or release-facing PR30 coefficients/configs.
- Do not bundle anchored calibration, texture-support scaling, and high-frequency guard into the same implementation issue.
- Do not write new fitted outputs under `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`, or `release/deadleaf_13b10_release/config/`.

## Excluded Routes

### `bundle_anchored_calibration_texture_scale_and_high_frequency_guard`

- Route: bundle PR30's anchored calibration, texture-support scaling, and high-frequency guard into issue-97 now
- Those knobs live in a broader observable-stack family and would change both upstream PSD estimation and the frequency axis together.
- Issue #99 is a narrowing pass, so it should not jump from one failed readout boundary straight into a three-knob bundle before the single compensation boundary is isolated.

### `reconnect_reported_mtf_to_intrinsic_branch_again`

- Route: route reported-MTF thresholds back through the intrinsic reconnect path
- Issue #95 / PR #96 already selected the disconnect boundary as the minimum post-issue93 slice, and PR #98 completed that experiment cleanly.
- Reconnecting thresholds to the intrinsic branch would reopen a path that issue #97 has already bounded, rather than narrowing the remaining failure mode.

### `restart_broader_matched_ori_or_intrinsic_family_search`

- Route: restart broader matched-ori, observable-stack, or intrinsic family search
- The remaining failure mode is already localized to the reported-MTF/readout path after issue #97; the repo evidence no longer supports reopening whole-family search.
- Issue #99 must leave engineering with one direct bounded implementation issue, not another unbounded family sweep.

## Acceptance For The Next Implementation Issue

- The new bounded implementation keeps `curve_mae_mean`, `focus_preset_acutance_mae_mean`, and `overall_quality_loss_mae_mean` no worse than issue #97.
- The same implementation improves `mtf_abs_signed_rel_mean`, `mtf30`, and `mtf50` versus issue #97 while keeping `mtf20` no worse than issue #97.
- The implementation keeps the downstream-only matched-ori Quality Loss branch isolated from the reported-MTF/readout path.
- All new fitted outputs remain under `algo/` or `artifacts/`, not under golden/reference roots or release-facing config roots.

## Validation Plan For The Next Implementation Issue

- Run `python3 -m algo.benchmark_parity_psd_mtf ...` on an issue-97-based profile that adds readout-only sensor-aperture compensation, then compare `mtf_abs_signed_rel_mean`, `mtf20`, `mtf30`, and `mtf50` against issue #97, issue #93, and PR #30.
- Run `python3 -m algo.benchmark_parity_acutance_quality_loss ...` on the same scope to confirm `curve_mae_mean`, `focus_preset_acutance_mae_mean`, and `overall_quality_loss_mae_mean` stay at or below issue #97.
- Add focused tests that prove only the reported-MTF/readout path receives the new compensation mode while `compensated_mtf_for_acutance` and `quality_loss_compensated_mtf_for_acutance` remain on the existing issue-97 branches.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`
- Fitted artifact roots: `algo/*.json`, `artifacts/*.json`
- Release config roots: `release/deadleaf_13b10_release/config/*.json`
- Keep this issue's discovery outputs under `docs/` and `artifacts/` only.
- Do not write new fitted intrinsic profiles, transfer tables, or benchmark outputs under the golden/reference roots.
- Do not touch release-facing configs until a later bounded implementation clears the current README-facing guardrails.
