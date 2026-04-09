# Imatest parity direct acutance-curve anchor preset-phone-aware gentle-down shape follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

After the preset-only phone-aware split and the best bounded scalar retune (`0.70`), the remaining gap was still concentrated in the curve-side Acutance branch. This follow-up uses the measured signed residual over relative viewing scale to test whether a descending curve-side shape can reduce the remaining curve error without moving the preset metrics.

## Residual signal

For the current `0.70` preset-only branch, the mean signed error on the Acutance curve stays positive across the full observable range and grows into the mid / high relative-scale region:

- `0.025`: `+0.00171`
- `0.100`: `+0.00475`
- `0.400`: `+0.02430`
- `0.800`: `+0.03210`
- `1.200`: `+0.02924`
- `2.400`: `+0.01879`

That residual pattern suggests that the curve-side direct anchor is still slightly too strong, especially past the low-scale region.

## Bounded shape search

All probes keep the preset-only phone-aware branch fixed and only change the curve-side direct Acutance-domain shape:

- `mild_trim`: `[0.70, 0.69, 0.66, 0.65, 0.64]`
- `gentle_down`: `[0.70, 0.69, 0.64, 0.62, 0.60]`
- `mid_trim`: `[0.70, 0.68, 0.62, 0.62, 0.62]`

Measured result:

- `mild_trim`: `curve_mae_mean = 0.03842461`
- `gentle_down`: `curve_mae_mean = 0.03842318`
- `mid_trim`: `curve_mae_mean = 0.03847233`

The preset metrics stayed fixed across all three probes because the preset-only branch remains unchanged.

## Tracked profile

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve_shape_gentle_down_profile.json`

Curve-side shape:

- `matched_ori_acutance_strength_curve_relative_scales = [0.0, 0.2, 0.8, 1.6, 2.5]`
- `matched_ori_acutance_strength_curve_values = [0.70, 0.69, 0.64, 0.62, 0.60]`

Preset-only phone-aware shape remains:

- `matched_ori_acutance_preset_strength_curve_relative_scales = [0.0, 3.0, 4.5, 5.8, 6.2]`
- `matched_ori_acutance_preset_strength_curve_values = [1.0, 1.0, 0.85, 0.45, 0.45]`

## Validation

```bash
python3 -m algo.benchmark_parity_psd_mtf \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve_shape_gentle_down_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve_shape_gentle_down_psd_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve_shape_gentle_down_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve_shape_gentle_down_benchmark.json
```

## Result

Compared with the earlier preset-only scalar `0.70` branch:

- `curve_mae_mean`: `0.03844714 -> 0.03842318`
- `acutance_focus_preset_mae_mean`: unchanged at `0.04375`
- `overall_quality_loss_mae_mean`: unchanged at `2.35463`
- `5.5" Phone Display Acutance` MAE: unchanged at `0.01919`
- `5.5" Phone Display Quality Loss` MAE: unchanged at `0.37906`

## Interpretation

This is another small but real improvement, and it is the first structured curve-side shape that beats the best local scalar branch.

The canonical README target is still not fully closed:

- `curve_mae_mean = 0.03842318` is still slightly above the earlier reference-refined branch (`0.03795`)
- `5.5" Phone Display Acutance` MAE `= 0.01919` is still slightly above the earlier mid-dip extreme (`0.01447`)

The remaining gap is now very narrow. If more curve gain is still needed, the next useful step should probably change the curve-side family again rather than spending more time on nearby local trims of this same descending shape.
