# Imatest parity direct acutance-curve anchor curve-side delta-power split follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The earlier nonlinear `delta_power` experiment was only tested as a shared knob across both the observable Acutance curve path and the preset report path. That result was negative overall because it improved the phone preset only by making the curve worse.

The current best branch already splits curve-side and preset-side corrections. This follow-up tests whether the same nonlinear family becomes useful once it is restricted to the curve-side path only.

## Change

The benchmark path now supports separate direct Acutance correction delta-power controls for the two applications:

- `matched_ori_acutance_curve_correction_delta_power`
- `matched_ori_acutance_preset_correction_delta_power`

Tracked profile:

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve_delta095_profile.json`

Tracked curve-side setting:

- `matched_ori_acutance_curve_correction_delta_power = 0.95`

The preset-side path stays on the existing baseline:

- `matched_ori_acutance_preset_correction_delta_power = null`
- fallback shared `matched_ori_acutance_correction_delta_power = 1.0`

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_curve_delta_power_split_search.json`

Measured against the previous clip-shape branch:

- baseline clip-shape branch
  - `curve_mae_mean = 0.03803290`
- curve-side `delta_power = 1.05`
  - `curve_mae_mean = 0.03833543`
- curve-side `delta_power = 1.10`
  - `curve_mae_mean = 0.03866949`
- curve-side `delta_power = 0.95`
  - `curve_mae_mean = 0.03776865`

Across the full bounded search, the preset metrics stayed fixed:

- `acutance_focus_preset_mae_mean = 0.04375`
- `overall_quality_loss_mae_mean = 2.35463`
- `5.5" Phone Display Acutance` MAE `= 0.01919`
- `5.5" Phone Display Quality Loss` MAE `= 0.37906`

## Validation

```bash
python3 -m algo.benchmark_parity_psd_mtf \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve_delta095_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_curve_delta095_psd_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve_delta095_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_curve_delta095_benchmark.json
```

## Result

Compared with the earlier clip-shape branch:

- `curve_mae_mean`: `0.03803290 -> 0.03776865`
- `acutance_focus_preset_mae_mean`: unchanged at `0.04375`
- `overall_quality_loss_mae_mean`: unchanged at `2.35463`
- `5.5" Phone Display Acutance` MAE: unchanged at `0.01919`
- `5.5" Phone Display Quality Loss` MAE: unchanged at `0.37906`

The reported-MTF branch remains fixed:

- `curve_mae_mean = 0.04306442`
- `mtf_abs_signed_rel_mean = 0.08692956`

## Interpretation

This is the strongest overall issue-29 branch so far.

The bounded split search also clarifies the family behavior:

- `delta_power > 1` remains harmful even when restricted to the curve-side path
- `delta_power < 1` becomes useful once the preset path is held fixed

That means the earlier negative result was not enough to reject the nonlinear family entirely. The useful version is the curve-side-only expansion branch, not the shared compression branch.

The canonical README target is still not fully closed:

- `curve_mae_mean = 0.03776865` is still above the release-facing README acceptance gate (`<= 0.020`)
- `acutance_focus_preset_mae_mean = 0.04375` is still above the release-facing README acceptance gate (`<= 0.030`)
- `overall_quality_loss_mae_mean = 2.35463` is still above the release-facing README acceptance gate (`<= 1.30`)

But the remaining curve-side miss is smaller again, and this branch now also clears the earlier reference-refined curve mark (`0.03795`) while preserving the best current preset and Quality Loss metrics.
