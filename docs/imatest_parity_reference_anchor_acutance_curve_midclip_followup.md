# Imatest Parity Acutance Curve Mid-Clip Follow-up

Issue: `#29`  
PR: `#30`

## What changed

- Benchmarked a bounded curve-side `clip_hi` notch family on top of the current best sextic branch:
  - `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_profile.json`
- Promoted the best winning branch as:
  - `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip1015_profile.json`
- Checked in:
  - `artifacts/imatest_parity_reference_anchor_acutance_curve_midclip_search.json`
  - `artifacts/imatest_parity_reference_anchor_acutance_curve_midclip1015_benchmark.json`

## Why this family

The exported Acutance records showed that the remaining curve blocker is concentrated in the mid-distance region:

- strongest residual around `d24` to `d30`
- positive signed Acutance error almost everywhere

Those distances correspond to relative scales around `0.6` to `0.75` on the observable Acutance curve. So this follow-up narrows the curve-side `clip_hi` cap only in that region while leaving the preset-side branch unchanged.

## Result

This is a real win on the still-open curve gate.

Baseline:

- `curve_mae_mean = 0.03776865`
- `acutance_focus_preset_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22214`

Bounded search:

- `curve_midclip_notch_1025`
  - `curve_mae_mean = 0.03771770`
- `curve_midclip_notch_1020`
  - `curve_mae_mean = 0.03769417`
- `curve_midclip_notch_1015`
  - `curve_mae_mean = 0.03766648`

Across all three probes:

- `acutance_focus_preset_mae_mean` stays fixed at `0.04249`
- `overall_quality_loss_mae_mean` stays fixed at `1.22214`

So this family cleanly improves the remaining curve gate without reopening the current preset or Quality Loss branch.

## Conclusion

The winning `curve_midclip_notch_1015` branch is now the strongest overall issue-29 branch so far:

- `curve_mae_mean = 0.03766648`
- `acutance_focus_preset_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22214`

This also confirms that the exported mid-scale curve residual was actionable: a narrower curve-side cap around relative scales `0.6` to `0.8` improves the branch while leaving the preset-side and Quality Loss-side wins intact.
