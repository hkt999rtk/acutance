# Intrinsic After Issue 102 Next Slice

This note records the issue `#105` developer-discovery pass after issue `#102` / PR `#103` / PR `#104` proved that readout-only sensor-aperture compensation is a real bounded improvement but still leaves a residual gap versus PR `#30`.

## Selected Slice

- Selected slice: `issue102_topology_graft_pr30_observable_stack_onto_observed_branches`
- Summary: Keep issue #102's intrinsic main-acutance branch and readout-only sensor-aperture compensation record intact, but move the observed-branch consumers that still lag PR #30 onto one bounded PR30-style observable-stack bundle: anchored calibration, `texture_support_scale`, and `high_frequency_guard_start_cpp=0.36` for the reported-MTF/readout path and the downstream Quality Loss branch only.
- Prior narrowing lineage: issue `#99` / PR `#100` / PR `#101` selected the readout-only compensation slice, and issue `#102` / PR `#103` / PR `#104` completed it cleanly enough to expose the next remaining boundary.
- Remaining gap location: after issue `#102`, the intrinsic main branch and the readout-only compensation boundary are both bounded. The large residual gap now sits on the observed-branch observable stack that still feeds reported-MTF and downstream Quality Loss differently from PR `#30`.

## Comparison Table

| Record | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel | Reading |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_best_pr30_branch | 0.03679 | 0.04249 | 1.22150 | 0.03301 | 0.03694 | 0.00933 | 0.08671 | Current best PR30 branch. |
| issue97_reported_mtf_disconnect_candidate | 0.03280 | 0.02892 | 3.94743 | 0.07448 | 0.07553 | 0.03429 | 0.37688 | Issue-97 mixed-negative disconnect result from PR #98. |
| issue102_readout_only_sensor_comp_candidate | 0.03280 | 0.02892 | 3.94743 | 0.02972 | 0.04293 | 0.03094 | 0.23033 | Issue-102 bounded positive result from PR #103/#104. |

## Residual Gap Evidence

- Issue #102 preserves issue #97 `curve_mae_mean`: `True`
- Issue #102 preserves issue #97 `focus_preset_acutance_mae_mean`: `True`
- Issue #102 preserves issue #97 `overall_quality_loss_mae_mean`: `True`
- Issue #102 improves `mtf_abs_signed_rel_mean` versus issue #97: `True`
- Issue #102 still trails PR #30 on `mtf30`: `True`
- Issue #102 still trails PR #30 on `mtf50`: `True`
- Issue #102 still trails PR #30 on `mtf_abs_signed_rel_mean`: `True`
- Issue #102 already beats PR #30 on `mtf20`: `True`
- Issue #93 / #97 / #102 keep the same downstream Quality Loss record: `True`

## Pipeline Delta Summary

- `calibration_file`: issue102='algo/deadleaf_13b10_psd_calibration.json', pr30='algo/deadleaf_13b10_psd_calibration_anchored.json'
- `high_frequency_guard_start_cpp`: issue102=None, pr30=0.36
- `intrinsic_full_reference_mode`: issue102='paired_ori_transfer', pr30='none'
- `intrinsic_full_reference_scope`: issue102='reported_mtf_disconnect_readout_only_sensor_comp_quality_loss_isolation_downstream_matched_ori_only', pr30='replace_all'
- `intrinsic_full_reference_transfer_mode`: issue102='radial_real_mean', pr30='magnitude_ratio'
- `matched_ori_anchor_mode`: issue102='all', pr30='acutance_only'
- `mtf_compensation_mode`: issue102='none', pr30='sensor_aperture_sinc'
- `readout_mtf_compensation_mode`: issue102='sensor_aperture_sinc', pr30=None
- `sensor_fill_factor`: issue102=1.0, pr30=1.5
- `readout_sensor_fill_factor`: issue102=1.5, pr30=None
- `texture_support_scale`: issue102=False, pr30=True

## Why The Next Slice Is The Observed-Branch PR30 Observable Stack

- Issue #102 proved the readout-only sensor-aperture compensation boundary and already improved all tracked readout metrics versus issue #97, so another single-knob readout retune is no longer the highest-signal follow-up.
- `overall_quality_loss_mae_mean` never changed across issue `#93`, issue `#97`, and issue `#102`, which means the residual large PR30 gap still sits on the downstream observed-branch family rather than the issue-102 intrinsic main branch.
- The remaining pipeline deltas that can hit both reported-MTF and downstream Quality Loss without discarding the issue-102 intrinsic main branch are PR30's anchored calibration, `texture_support_scale`, and `high_frequency_guard_start_cpp` on the observed branch.
- PR #104 changed only summary-artifact provenance, so the post-issue102 narrowing should treat PR #103 and PR #104 as the same benchmark record.

## Selected Implementation Boundary

- Keep issue #102's intrinsic main-acutance branch, `intrinsic_full_reference_scope`, and readout-only sensor-aperture compensation (`sensor_aperture_sinc`) unchanged.
- Introduce one observed-branch bundle for the reported-MTF/readout path and the downstream Quality Loss branch that uses PR #30's anchored calibration file, `texture_support_scale=True`, and `high_frequency_guard_start_cpp=0.36`.
- Do not move the main acutance branch back to PR #30's non-intrinsic topology, and do not promote release-facing PR30 configs directly.

## Explicit Non-Changes

- Do not drop the issue-102 intrinsic main branch back to PR #30's non-intrinsic observable stack.
- Do not reopen broader observable-stack, matched-ori, or intrinsic family search outside the bounded observed-branch bundle.
- Do not retune only the readout-only sensor-aperture compensation again as a single-knob follow-up.
- Do not write new fitted outputs under `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`, or `release/deadleaf_13b10_release/config/`.

## Excluded Routes

### `retune_readout_only_sensor_aperture_compensation_again`

- Route: keep tuning only the readout-only sensor-aperture compensation parameters
- Issue #102 already improved every tracked readout metric versus issue #97 and even beat PR #30 on `mtf20`, so the remaining readout gap is no longer the same single-knob amplitude problem.
- Overall Quality Loss never moved across issue #93, issue #97, and issue #102, so another readout-only compensation retune would not address the largest residual PR30 gap.

### `drop_intrinsic_main_branch_and_rejoin_whole_pr30_stack`

- Route: discard the issue-102 intrinsic main branch and move the whole stack back toward PR #30
- Issue #102 still beats PR #30 on `curve_mae_mean` and `focus_preset_acutance_mae_mean`, so collapsing the whole topology back toward PR #30 would throw away the strongest part of the current bounded record.
- Issue #105 is supposed to leave one direct bounded implementation slice, not reopen the full observable-stack replacement path.

### `restart_broader_observable_stack_or_intrinsic_family_search`

- Route: restart broader observable-stack, matched-ori, or intrinsic family search
- The remaining issue-102 residuals are already localized: the intrinsic main branch is stable, the readout-only compensation boundary is proven, and the unchanged downstream Quality Loss record points at the observed-branch bundle.
- Issue #105 is a developer-discovery narrowing pass and must hand engineering one direct next implementation issue rather than another unbounded search.

## Validation Plan For The Next Implementation Issue

- Run `python3 -m algo.benchmark_parity_psd_mtf ...` on an issue-102-based profile that keeps readout-only sensor-aperture compensation but adds the PR30 observable-stack bundle on the observed readout branch, then compare `mtf_abs_signed_rel_mean`, `mtf20`, `mtf30`, and `mtf50` against issue #102 and PR #30.
- Run `python3 -m algo.benchmark_parity_acutance_quality_loss ...` on the same bounded scope to confirm `curve_mae_mean` and `focus_preset_acutance_mae_mean` stay no worse than issue #102 while `overall_quality_loss_mae_mean` improves materially.
- Add focused tests that prove anchored calibration, `texture_support_scale`, and `high_frequency_guard_start_cpp` affect only the observed reported-MTF / downstream Quality Loss consumers and not the issue-102 intrinsic main-acutance branch.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`
- Discovery outputs for this issue stay under `docs/` and `artifacts/` only.
- Do not write new fitted profiles, transfer tables, or benchmark outputs under the golden/reference roots or release-facing config roots.
