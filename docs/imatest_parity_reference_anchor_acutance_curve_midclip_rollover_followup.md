# Imatest Parity Acutance Curve Mid-Clip Rollover Follow-up

Issue: `#29`  
PR: `#30`

## What changed

- Extended the same winning curve-side mid-scale `clip_hi` notch family below the current `0.995` branch.
- Promoted the new best branch as:
  - `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0985_profile.json`
- Checked in:
  - `artifacts/imatest_parity_reference_anchor_acutance_curve_midclip0985_benchmark.json`
  - `artifacts/imatest_parity_reference_anchor_acutance_curve_midclip_rollover_search.json`

## Why this family

The previous outer extension down to `0.995` was still monotonic while holding:

- `acutance_focus_preset_mae_mean` fixed
- `overall_quality_loss_mae_mean` fixed

So the next useful step was to probe whether the same family would finally roll over once the mid-scale notch moved a bit lower.

## Result

This bounded rollover search is still monotonic.

Baseline:

- `curve_mae_mean = 0.03751859`
- `acutance_focus_preset_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22214`

Rollover search:

- `curve_midclip_notch_09925`
  - `curve_mae_mean = 0.03749835`
- `curve_midclip_notch_09900`
  - `curve_mae_mean = 0.03747805`
- `curve_midclip_notch_09850`
  - `curve_mae_mean = 0.03743780`

Across all three probes:

- `acutance_focus_preset_mae_mean` stays fixed at `0.04249`
- `overall_quality_loss_mae_mean` stays fixed at `1.22214`

## Conclusion

The new `curve_midclip_notch_09850` branch is now the strongest overall issue-29 branch so far:

- `curve_mae_mean = 0.03743780`
- `acutance_focus_preset_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22214`

This means the same curve-side mid-scale family still has not rolled over inside the current bounded search. The remaining release-facing blockers are still the curve gate and the focus-preset Acutance gate.
