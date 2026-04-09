# Imatest parity direct acutance-curve anchor clip-shape follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The previous clip-split branch showed that tightening the curve-side clip without touching the preset-side path improves the observable Acutance curve while keeping preset and Quality Loss metrics fixed.

This follow-up tests the next structural step inside that family:

- keep the preset-side clip fixed
- keep the curve-side global cap at `1.04`
- add a curve-side relative-scale-dependent clip-high shape so low-scale points can be capped more tightly than the rest of the observable curve

## Change

The shared matched-`ori` Acutance correction path now supports a curve-side `clip_hi` shape over relative viewing scale:

- `matched_ori_acutance_curve_correction_clip_hi_relative_scales`
- `matched_ori_acutance_curve_correction_clip_hi_values`

Tracked profile:

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve_clip_shape_profile.json`

Tracked curve-side clip shape:

- relative scales: `[0.0, 0.25, 0.8, 1.6, 2.5]`
- clip-high values: `[1.02, 1.03, 1.04, 1.05, 1.06]`

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_curve_clip_shape_search.json`

Measured against the previous `curveclip104` branch:

- baseline scalar `clip_hi = 1.04`
  - `curve_mae_mean = 0.03806777`
- tail-relax only `[1.04, 1.04, 1.04, 1.05, 1.06]`
  - `curve_mae_mean = 0.03806777`
- low-tight plus tail-relax `[1.02, 1.03, 1.04, 1.05, 1.06]`
  - `curve_mae_mean = 0.03803290`
- low-tight plus looser tail `[1.02, 1.03, 1.04, 1.06, 1.08]`
  - `curve_mae_mean = 0.03803290`

Across the full bounded search, the preset metrics stayed fixed:

- `acutance_focus_preset_mae_mean = 0.04375`
- `overall_quality_loss_mae_mean = 2.35463`
- `5.5" Phone Display Acutance` MAE `= 0.01919`
- `5.5" Phone Display Quality Loss` MAE `= 0.37906`

## Validation

```bash
python3 -m algo.benchmark_parity_psd_mtf \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve_clip_shape_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_clip_shape_psd_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve_clip_shape_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_clip_shape_benchmark.json
```

## Result

Compared with the earlier `curveclip104` branch:

- `curve_mae_mean`: `0.03806777 -> 0.03803290`
- `acutance_focus_preset_mae_mean`: unchanged at `0.04375`
- `overall_quality_loss_mae_mean`: unchanged at `2.35463`
- `5.5" Phone Display Acutance` MAE: unchanged at `0.01919`
- `5.5" Phone Display Quality Loss` MAE: unchanged at `0.37906`

The reported-MTF branch remains fixed:

- `curve_mae_mean = 0.04306442`
- `mtf_abs_signed_rel_mean = 0.08692956`

## Interpretation

This is another real improvement and the strongest overall issue-29 branch so far.

The bounded search also explains where the gain comes from:

- tail relaxation alone is a no-op
- once the low-scale caps are tightened to `1.02 / 1.03`, the remaining tail values do not materially change the result in the tested neighborhood

That means the useful new model-family step is not a looser high-scale tail. It is the lower relative-scale cap shape itself.

The canonical README target is still not fully closed:

- `curve_mae_mean = 0.03803290` is still slightly above the earlier reference-refined branch (`0.03795`)
- `5.5" Phone Display Acutance` MAE `= 0.01919` is still slightly above the earlier mid-dip extreme (`0.01447`)

But the remaining gap is narrower again, and the direct Acutance-domain curve-side clip shape is now the best tracked branch for issue `#29`.
