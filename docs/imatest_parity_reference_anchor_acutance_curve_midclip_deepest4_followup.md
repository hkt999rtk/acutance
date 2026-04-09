# Imatest Parity Acutance Curve Mid-Clip Deepest-4 Follow-up

Issue: `#29`  
PR: `#30`

## What changed

- Extended the same winning curve-side mid-scale `clip_hi` notch family below the current `0.925` branch.
- Promoted the new best branch as:
  - `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0915_profile.json`
- Checked in:
  - `artifacts/imatest_parity_reference_anchor_acutance_curve_midclip0915_benchmark.json`
  - `artifacts/imatest_parity_reference_anchor_acutance_curve_midclip_deepest4_search.json`

## Why this family

The previous deepest-3 follow-up down to `0.925` was still monotonic while holding:

- `acutance_focus_preset_mae_mean` fixed
- `overall_quality_loss_mae_mean` fixed

So the next useful step was to keep pushing the same mid-scale notch family outward and find where it finally stops helping.

## Result

This next deepest bounded extension is still monotonic.

Baseline:

- `curve_mae_mean = 0.03700084`
- `acutance_focus_preset_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22214`

Next deepest extension:

- `curve_midclip_notch_09225`
  - `curve_mae_mean = 0.03698655`
- `curve_midclip_notch_09200`
  - `curve_mae_mean = 0.03697271`
- `curve_midclip_notch_09150`
  - `curve_mae_mean = 0.03694616`

Across all three probes:

- `acutance_focus_preset_mae_mean` stays fixed at `0.04249`
- `overall_quality_loss_mae_mean` stays fixed at `1.22214`

## Conclusion

The new `curve_midclip_notch_09150` branch is now the strongest overall issue-29 branch so far:

- `curve_mae_mean = 0.03694616`
- `acutance_focus_preset_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22214`

This means the same curve-side mid-scale family still has not rolled over inside the current bounded search. The remaining release-facing blockers are still the curve gate and the focus-preset Acutance gate.
