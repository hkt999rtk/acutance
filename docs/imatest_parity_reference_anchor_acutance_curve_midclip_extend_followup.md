# Imatest Parity Acutance Curve Mid-Clip Extend Follow-up

Issue: `#29`  
PR: `#30`

## What changed

- Extended the winning curve-side mid-scale `clip_hi` notch family below the current `1.015` branch.
- Promoted the new best branch as:
  - `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip1005_profile.json`
- Checked in:
  - `artifacts/imatest_parity_reference_anchor_acutance_curve_midclip1005_benchmark.json`
  - `artifacts/imatest_parity_reference_anchor_acutance_curve_midclip_extend_search.json`

## Why this family

The previous bounded search from `1.025` to `1.015` improved monotonically while leaving:

- `acutance_focus_preset_mae_mean` fixed
- `overall_quality_loss_mae_mean` fixed

So the next useful step was to probe whether the same mid-scale curve-side family still improves below `1.015`, or whether it finally rolls over.

## Result

This family still improves monotonically.

Baseline:

- `curve_mae_mean = 0.03766648`
- `acutance_focus_preset_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22214`

Bounded extension:

- `curve_midclip_notch_10125`
  - `curve_mae_mean = 0.03765069`
- `curve_midclip_notch_1010`
  - `curve_mae_mean = 0.03763389`
- `curve_midclip_notch_1005`
  - `curve_mae_mean = 0.03759884`

Across all three probes:

- `acutance_focus_preset_mae_mean` stays fixed at `0.04249`
- `overall_quality_loss_mae_mean` stays fixed at `1.22214`

## Conclusion

The new `curve_midclip_notch_1005` branch is now the strongest overall issue-29 branch so far:

- `curve_mae_mean = 0.03759884`
- `acutance_focus_preset_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22214`

This confirms the same curve-side mid-scale region is still actionable and has not yet rolled over inside this bounded extension.
