# Intrinsic After Issue 93 Next Slice

This note records the issue `#95` developer-discovery pass after issue `#93` / PR `#94` proved that the downstream-only matched-ori branch is a safe bounded improvement but still leaves a residual PR `#30` gap.

## Selected Slice

- Selected slice: `issue93_topology_keep_downstream_quality_loss_branch_but_disconnect_reported_mtf_from_intrinsic_reconnect`
- Summary: Keep issue #93's phase-retained intrinsic curve/main-acutance branch and downstream-only matched-ori Quality Loss branch unchanged, but stop feeding reported-MTF thresholds from the intrinsic reconnect path. Leave `compensated_mtf_for_acutance` and `quality_loss_compensated_mtf_for_acutance` on the issue-93 topology, while reported-MTF extraction stays on the observed calibrated/compensated branch.
- Prior narrowing lineage: issue `#91` selected `phase_retained_intrinsic_quality_loss_only_matched_ori_graft_without_readout_correction`, and issue `#93` implemented that downstream-only matched-ori branch successfully enough to expose the next live boundary.
- Remaining gap location: after issue #93, the safe downstream Quality Loss gain is already isolated. The next minimum slice is the reported-MTF reconnect boundary itself, while the remaining Quality Loss gap stays on a broader downstream observable-stack family for later work.

## Comparison Table

| Record | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel | Reading |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_best_pr30_branch | 0.03679 | 0.04249 | 1.22150 | 0.03301 | 0.03694 | 0.00933 | 0.08671 | Current best PR30 branch. |
| issue85_readout_reconnect_quality_loss_isolation_candidate | 0.03280 | 0.02892 | 8.02054 | 0.08577 | 0.01789 | 0.00720 | 0.13994 | Issue-81 plus readout reconnect; readout thresholds now follow the intrinsic reconnect path. |
| issue89_matched_ori_graft_candidate | 0.03280 | 0.02892 | 3.94743 | 0.09532 | 0.11756 | 0.07657 | 0.74771 | Issue-85 plus matched-ori graft; Quality Loss improves, readout regresses sharply. |
| issue93_downstream_matched_ori_only_candidate | 0.03280 | 0.02892 | 3.94743 | 0.08577 | 0.01789 | 0.00720 | 0.13994 | Issue-85 readout path plus issue-89 downstream-only Quality Loss gain. |

## Residual Gap Evidence

- Issue #93 preserves issue #89 `overall_quality_loss_mae_mean`: `True`
- Issue #93 Quality Loss delta versus issue #89: `0.00000`
- Issue #93 recovers issue #89 `mtf_abs_signed_rel_mean`: `True`
- Issue #93 threshold recoveries versus issue #89: `mtf20=True`, `mtf30=True`, `mtf50=True`
- Issue #93 preserves issue #85 `mtf_abs_signed_rel_mean`: `True`
- Issue #93 threshold equality versus issue #85: `mtf20=True`, `mtf30=True`, `mtf50=True`
- Issue #93 still trails PR #30 on overall Quality Loss: `True`
- Issue #93 still trails PR #30 on `mtf20`: `True`
- Issue #93 still trails PR #30 on `mtf_abs_signed_rel_mean`: `True`

## Pipeline Delta Between Issue 93 And PR30

- `acutance_noise_scale_mode`: issue93='fixed', pr30='high_frequency_noise_share_quadratic'
- `calibration_file`: issue93='algo/deadleaf_13b10_psd_calibration.json', pr30='algo/deadleaf_13b10_psd_calibration_anchored.json'
- `high_frequency_guard_start_cpp`: issue93=None, pr30=0.36
- `intrinsic_full_reference_mode`: issue93='paired_ori_transfer', pr30='none'
- `intrinsic_full_reference_scope`: issue93='readout_reconnect_quality_loss_isolation_downstream_matched_ori_only', pr30='replace_all'
- `intrinsic_full_reference_transfer_mode`: issue93='radial_real_mean', pr30='magnitude_ratio'
- `matched_ori_anchor_mode`: issue93='all', pr30='acutance_only'
- `mtf_compensation_mode`: issue93='none', pr30='sensor_aperture_sinc'
- `sensor_fill_factor`: issue93=1.0, pr30=1.5
- `texture_support_scale`: issue93=False, pr30=True

## Why The Next Slice Is The Readout Reconnect Boundary

- Issue #93 preserves issue #89's `overall_quality_loss_mae_mean` exactly while recovering the entire readout regression, so the current Quality Loss gain and the current readout behavior are already on separate runtime branches.
- Issue #93 also preserves issue #85's `mtf_abs_signed_rel_mean`, `mtf20`, `mtf30`, and `mtf50` exactly, which means the remaining readout gap versus PR #30 is inherited from the issue-85 reconnect boundary rather than from the downstream-only matched-ori split.
- In `algo/benchmark_parity_psd_mtf.py`, the issue-93 scope still overwrites `compensated_mtf` with `intrinsic_mtf` before `compute_mtf_metrics(...)` reads thresholds, so one assignment now defines the whole reported-MTF branch.
- In `algo/benchmark_parity_acutance_quality_loss.py`, the downstream Quality Loss branch is already independent: `quality_loss_compensated_mtf_for_acutance` stays on the observed compensated stack and still receives the issue-93 downstream matched-ori correction / anchor path. That means a readout-only reconnect change can preserve the current issue-93 Quality Loss gain.
- The remaining Quality Loss gap to PR #30 still lives in a broader observable-stack family (`calibration_file`, `acutance_noise_scale_mode`, `high_frequency_guard_start_cpp`, `texture_support_scale`, `mtf_compensation_mode`, `sensor_fill_factor`). That family is larger than one boundary, so it is not the next smallest slice.

## Runtime Boundary Evidence

### `algo/benchmark_parity_psd_mtf.py` (500-512, 675-679)

- For issue-93-class scopes, the PSD driver assigns `compensated_mtf = intrinsic_mtf` inside the intrinsic reconnect block.
- `compute_mtf_metrics(...)` later consumes that `compensated_mtf` directly, so the reported-MTF thresholds are currently locked to the intrinsic reconnect path.
- A bounded next slice can stop only this assignment while leaving the intrinsic main-acutance branch intact.

### `algo/benchmark_parity_acutance_quality_loss.py` (676-677, 740-746, 864-968)

- The Quality Loss driver creates `quality_loss_compensated_mtf_for_acutance` as a separate observed-stack copy before the intrinsic reconnect runs.
- For issue-93-class scopes, the intrinsic reconnect updates only `compensated_mtf_for_acutance`; the downstream Quality Loss copy stays on its own branch unless the scope is `replace_all`.
- The downstream branch still receives matched-ori correction and anchoring later, so a readout-only reconnect change can preserve issue #93's current downstream Quality Loss behavior.

## Implementation Boundary

- Keep issue #93's `readout_reconnect_quality_loss_isolation_downstream_matched_ori_only` topology, intrinsic transfer mode, registration mode, and downstream matched-ori Quality Loss subfamily unchanged.
- Add one bounded scope or profile family that leaves `compensated_mtf_for_acutance` and `quality_loss_compensated_mtf_for_acutance` on the issue-93 branches, but no longer overwrites `compensated_mtf` with `intrinsic_mtf` before reported-MTF threshold extraction.
- Use the observed calibrated/compensated readout stack for `compute_mtf_metrics(...)` only; do not retune release-facing coefficients, calibration families, or the downstream Quality Loss observable stack yet.

## Explicit Non-Changes

- Do not reopen the intrinsic transfer family, measured OECF family, or affine-registration variants.
- Do not reapply matched-ori correction to the reported-MTF/readout path.
- Do not touch issue #93's downstream-only matched-ori Quality Loss branch or promote issue #93 directly as a main-line branch.
- Do not rewrite release-facing PR30 configs or write fitted outputs under `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`, or `release/deadleaf_13b10_release/config/`.

## Excluded Routes

### `bundle_pr30_observable_stack_into_issue93_now`

- Route: bundle PR30's entire observable stack into issue-93 now
- The remaining Quality Loss gap does point at a broader observable-stack family, but that family still contains multiple live knobs instead of one minimum boundary.
- Issue #95 is a narrowing pass, so it should not jump directly into a multi-knob calibration / noise-share / texture-support / compensation bundle before the readout reconnect boundary is isolated.

### `reopen_issue89_full_matched_ori_graft`

- Route: reopen the full issue-89 readout+Quality-Loss matched-ori graft
- Issue #93 already proved that the safe matched-ori value is the downstream-only subfamily, and the full issue-89 graft reintroduces the known readout regression.
- Replaying the same combined matched-ori boundary would not shrink the residual PR30 gap any further.

### `restart_intrinsic_or_measured_oecf_family_search`

- Route: restart the intrinsic family or measured-OECF search
- The current residual gap is downstream of issue #93's already-bounded topology and does not justify reopening whole-family search.
- Measured OECF closed as a bounded negative in issue #77 / PR #78, and affine-registration intrinsic was already excluded earlier in the chain.

## Acceptance For The Next Implementation Issue

- The new bounded implementation keeps `curve_mae_mean`, `focus_preset_acutance_mae_mean`, and `overall_quality_loss_mae_mean` no worse than issue #93.
- The same implementation improves `mtf20` and `mtf_abs_signed_rel_mean` versus issue #93 by moving the reported-MTF readout path toward the PR #30 side.
- The implementation keeps the downstream-only matched-ori Quality Loss branch isolated from the reported-MTF path.
- All new fitted outputs remain under `algo/` or `artifacts/`, not under golden/reference roots or release-facing config roots.

## Validation Plan For The Next Implementation Issue

- Run `python3 -m algo.benchmark_parity_psd_mtf ...` on an issue-93-based profile that disconnects only the reported-MTF readout path from the intrinsic reconnect, then compare `mtf20` and `mtf_abs_signed_rel_mean` against issue #93 and PR #30.
- Run `python3 -m algo.benchmark_parity_acutance_quality_loss ...` on the same scope to confirm `curve_mae_mean`, `focus_preset_acutance_mae_mean`, and `overall_quality_loss_mae_mean` stay at or below issue #93.
- Add focused tests that prove `compensated_mtf` stays on the observed calibrated/compensated path while `compensated_mtf_for_acutance` and `quality_loss_compensated_mtf_for_acutance` remain on the existing issue-93 branches.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`
- Fitted artifact roots: `algo/*.json`, `artifacts/*.json`
- Release config roots: `release/deadleaf_13b10_release/config/*.json`
- Keep this issue's discovery outputs under `docs/` and `artifacts/` only.
- Do not write new fitted intrinsic profiles, transfer tables, or benchmark outputs under the golden/reference roots.
- Do not touch release-facing configs until a later bounded implementation clears the current README-facing guardrails.
