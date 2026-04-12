# Issue 65 Chart-Prior / Inverse-Linearization Follow-up

Issue: `#65`  
Refs: `#29`, `#65`  
Context from: `#31`, `#32`, `#41`, `#63`, `#64`

## Why this pass

Issue `#65` asked for one bounded chart-prior / inverse-linearization family that is justified by current repo evidence and existing dead-leaves captures, without waiting on new Stepchart or Colorcheck artifacts.

The narrowest family already supported by the repo evidence was:

- the issue-`#63` empirical inverse-linearization branch on the current direct-method line
- combined with the issue-`#41` bounded chart-prior slope calibration, which already proved that chart-prior shape is a real signal-bearing lever inside the current ideal-PSD family

This stays narrower than the broader measured-OECF direction because it does not introduce new external chart-patch measurements or reopen a generic proxy sweep. It reuses one already-documented chart-prior perturbation and applies it to the already-bounded empirical inverse-linearization branch from `PR #64`.

## What changed

- Added the bounded issue-65 candidate profile:
  - `algo/deadleaf_13b10_imatest_sensor_comp_power_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_chart_prior_slope_m006_anchored_hf_psd_roi_reference_only_empirical_linearization_profile.json`
- Added tracked benchmark artifacts:
  - `artifacts/issue65_chart_prior_inverse_linearization_psd_benchmark.json`
  - `artifacts/issue65_chart_prior_inverse_linearization_acutance_benchmark.json`

No runtime code changed in this pass. The implementation is a bounded profile-only follow-up on top of the merged `PR #64` schema support.

## Candidate

Baseline from `PR #64`:

- `calibration_file = algo/deadleaf_13b10_psd_calibration_anchored.json`
- `linearization_mode = power`
- `gamma = 1.0`
- `black_percentile = 0.1`
- `white_percentile = 99.5`

Issue-65 candidate:

- keeps the full `PR #64` direct-method profile fixed
- swaps only the calibration file to `algo/deadleaf_13b10_psd_calibration_chart_prior_slope_m006.json`

That makes the issue-65 slice the direct composition of the bounded issue-41 chart-prior lever and the bounded issue-63 empirical linearization lever.

## Result Versus PR 64

This is another bounded negative result, not a new default path and not a useful refinement of the `PR #64` branch.

Compared with the `PR #64` empirical-linearization profile:

- PSD `curve_mae_mean` regresses: `0.04943691 -> 0.04982241`
- PSD signed-relative residual regresses materially: `0.10525592 -> 0.13670371`
- threshold MAE regresses:
  - `MTF20`: `0.03805077 -> 0.04277803`
  - `MTF30`: `0.04422298 -> 0.04902804`
  - `MTF50`: unchanged at `0.02158925`
- Acutance `curve_mae_mean` regresses slightly: `0.03163068 -> 0.03189952`
- `acutance_focus_preset_mae_mean` improves only trivially: `0.01309645 -> 0.01306828`
- `overall_quality_loss_mae_mean` regresses: `1.52185412 -> 1.53177498`
- explicit Phone movement is negligible and still mixed:
  - Phone Acutance improves slightly: `0.01233973 -> 0.01233877`
  - Phone Quality Loss improves slightly: `0.31667489 -> 0.31661996`

The issue-41 slope lever helped the old branch only by moving the curve aggressively while destabilizing threshold behavior. On top of the issue-63 empirical linearization branch, it no longer even buys a meaningful curve improvement; it mostly preserves the old regressions and makes the lower-layer PSD readouts worse.

## Result Versus Umbrella Gate

The umbrella README gate recorded in `planning/workgraph.yaml` still points to `PR #30` as the current best branch:

- `curve_mae_mean = 0.03683438`
- `acutance_focus_preset_mae_mean = 0.04249131`
- `overall_quality_loss_mae_mean = 1.22214341`
- `phone_display_acutance_mae = 0.01380215`

Compared with that gate, the issue-65 candidate still has:

- stronger aggregate Acutance metrics
  - `curve_mae_mean`: `0.03189952`
  - `acutance_focus_preset_mae_mean`: `0.01306828`
  - `5.5\" Phone Display Acutance`: `0.01233877`
- but much worse aggregate Quality Loss
  - `overall_quality_loss_mae_mean`: `1.53177498`
- and the PSD / reported-MTF side remains too weak to justify replacing the current main-line workaround branch

So issue `#65` does not move the repo closer to the canonical observable target enough to justify promoting this family.

## Working Conclusion

This pass closes one explicit current-data-supported chart-prior / inverse-linearization family:

- the family is well-justified by existing repo evidence because it composes the already-recorded issue-41 chart-prior slope lever with the already-recorded issue-63 empirical inverse-linearization branch
- the family is still narrower than the broader measured-OECF direction because it requires no new external chart artifacts
- the result is not merely mixed; on the current direct-method branch it is effectively a bounded negative refinement of `PR #64`

So the remaining canonical parity gap is still not explained or solved by combining the current empirical linearization branch with this one bounded chart-prior slope variant.

## Validation

- `python3 -m algo.benchmark_parity_psd_mtf 20260318_deadleaf_13b10 algo/deadleaf_13b10_imatest_sensor_comp_power_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_empirical_linearization_profile.json algo/deadleaf_13b10_imatest_sensor_comp_power_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_chart_prior_slope_m006_anchored_hf_psd_roi_reference_only_empirical_linearization_profile.json --output artifacts/issue65_chart_prior_inverse_linearization_psd_benchmark.json`
- `python3 -m algo.benchmark_parity_acutance_quality_loss 20260318_deadleaf_13b10 algo/deadleaf_13b10_imatest_sensor_comp_power_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_empirical_linearization_profile.json algo/deadleaf_13b10_imatest_sensor_comp_power_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_chart_prior_slope_m006_anchored_hf_psd_roi_reference_only_empirical_linearization_profile.json --output artifacts/issue65_chart_prior_inverse_linearization_acutance_benchmark.json`
