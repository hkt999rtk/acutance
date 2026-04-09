# Imatest Parity Acutance Curve Mid-Clip Outer Follow-up

Issue: `#29`  
PR: `#30`

## What changed

- Extended the same winning curve-side mid-scale `clip_hi` notch family below the current `1.005` branch.
- Promoted the new best branch as:
  - `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0995_profile.json`
- Checked in:
  - `artifacts/imatest_parity_reference_anchor_acutance_curve_midclip0995_benchmark.json`
  - `artifacts/imatest_parity_reference_anchor_acutance_curve_midclip_outer_search.json`

## Why this family

The previous bounded extension from `1.015` down to `1.005` kept improving monotonically while holding:

- `acutance_focus_preset_mae_mean` fixed
- `overall_quality_loss_mae_mean` fixed

So the next useful step was to probe slightly below `1.005` and see whether the same family finally rolls over.

## Result

This outer bounded extension is still monotonic.

Baseline:

- `curve_mae_mean = 0.03759884`
- `acutance_focus_preset_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22214`

Outer extension:

- `curve_midclip_notch_10025`
  - `curve_mae_mean = 0.03758023`
- `curve_midclip_notch_1000`
  - `curve_mae_mean = 0.03755983`
- `curve_midclip_notch_0995`
  - `curve_mae_mean = 0.03751859`

Across all three probes:

- `acutance_focus_preset_mae_mean` stays fixed at `0.04249`
- `overall_quality_loss_mae_mean` stays fixed at `1.22214`

## Conclusion

The new `curve_midclip_notch_0995` branch is now the strongest overall issue-29 branch so far:

- `curve_mae_mean = 0.03751859`
- `acutance_focus_preset_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22214`

This means the same curve-side mid-scale family is still improving and has not yet shown rollover inside this outer bounded search.
