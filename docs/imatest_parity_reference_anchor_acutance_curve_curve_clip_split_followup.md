# Imatest parity direct acutance-curve anchor curve-clip split follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The current best branch already isolates the phone-preserving preset path from the curve-side direct Acutance-domain correction path. That makes it possible to tighten only the curve-side correction without disturbing the now-stable preset metrics.

This follow-up tests that exact idea by splitting the direct Acutance-domain correction clipping between:

- the curve-side observable Acutance branch, and
- the preset-side report branch

## Change

The matched-`ori` Acutance correction cache now stores the raw correction ratio, and the benchmark path clips it separately for the curve and preset applications.

New profile knobs:

- `matched_ori_acutance_curve_correction_clip_lo`
- `matched_ori_acutance_curve_correction_clip_hi`
- `matched_ori_acutance_preset_correction_clip_lo`
- `matched_ori_acutance_preset_correction_clip_hi`

The current best tracked branch uses:

- curve-side `clip_hi = 1.04`
- preset-side `clip_hi = 1.10`

Tracked profile:

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve_shape_gentle_down_curveclip104_profile.json`

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_curve_clip_split_search.json`

Measured against the earlier gentle-down branch:

- baseline curve clip `1.10`
  - `curve_mae_mean = 0.03842318`
- curve clip `1.08`
  - `curve_mae_mean = 0.03831260`
- curve clip `1.06`
  - `curve_mae_mean = 0.03819763`
- curve clip `1.04`
  - `curve_mae_mean = 0.03806777`

Across the full bounded search, the preset metrics stayed fixed:

- `acutance_focus_preset_mae_mean = 0.04375`
- `overall_quality_loss_mae_mean = 2.35463`
- `5.5" Phone Display Acutance` MAE `= 0.01919`
- `5.5" Phone Display Quality Loss` MAE `= 0.37906`

## Validation

```bash
python3 -m algo.benchmark_parity_psd_mtf \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve_shape_gentle_down_curveclip104_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve_shape_gentle_down_curveclip104_psd_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve_shape_gentle_down_curveclip104_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve_shape_gentle_down_curveclip104_benchmark.json
```

## Result

Compared with the earlier gentle-down curve-shape branch:

- `curve_mae_mean`: `0.03842318 -> 0.03806777`
- `acutance_focus_preset_mae_mean`: unchanged at `0.04375`
- `overall_quality_loss_mae_mean`: unchanged at `2.35463`
- `5.5" Phone Display Acutance` MAE: unchanged at `0.01919`
- `5.5" Phone Display Quality Loss` MAE: unchanged at `0.37906`

## Interpretation

This is a meaningful improvement and the strongest overall issue-29 branch so far.

The curve-side clip split is a better next family than the earlier nonlinear delta-power compression because it narrows the curve gap directly while preserving the preset-side gains.

The canonical README target is still not fully closed:

- `curve_mae_mean = 0.03806777` is still slightly above the earlier reference-refined branch (`0.03795`)
- `5.5" Phone Display Acutance` MAE `= 0.01919` is still slightly above the earlier mid-dip extreme (`0.01447`)

But the remaining gap is narrower again, and the curve-side / preset-side split is now clearly the right structural direction.
