# Imatest Parity Acutance Curve Mid-Clip Even Further Follow-up

Issue: `#29`  
PR: `#30`

## What changed

- Extended the same winning curve-side mid-scale `clip_hi` notch family below the current `0.965` branch.
- Promoted the new best branch as:
  - `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0955_profile.json`
- Checked in:
  - `artifacts/imatest_parity_reference_anchor_acutance_curve_midclip0955_benchmark.json`
  - `artifacts/imatest_parity_reference_anchor_acutance_curve_midclip_even_further_search.json`

## Why this family

The previous further follow-up down to `0.965` was still monotonic while holding:

- `acutance_focus_preset_mae_mean` fixed
- `overall_quality_loss_mae_mean` fixed

So the next useful step was to keep pushing the same mid-scale notch family outward and find where it finally stops helping.

## Result

This even further bounded extension is still monotonic.

Baseline:

- `curve_mae_mean = 0.03727608`
- `acutance_focus_preset_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22214`

Even further extension:

- `curve_midclip_notch_09625`
  - `curve_mae_mean = 0.03725629`
- `curve_midclip_notch_09600`
  - `curve_mae_mean = 0.03723652`
- `curve_midclip_notch_09550`
  - `curve_mae_mean = 0.03719917`

Across all three probes:

- `acutance_focus_preset_mae_mean` stays fixed at `0.04249`
- `overall_quality_loss_mae_mean` stays fixed at `1.22214`

## Conclusion

The new `curve_midclip_notch_09550` branch is now the strongest overall issue-29 branch so far:

- `curve_mae_mean = 0.03719917`
- `acutance_focus_preset_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22214`

This means the same curve-side mid-scale family still has not rolled over inside the current bounded search. The remaining release-facing blockers are still the curve gate and the focus-preset Acutance gate.
