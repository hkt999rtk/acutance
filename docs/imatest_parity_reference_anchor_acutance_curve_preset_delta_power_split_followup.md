# Imatest parity direct acutance-curve anchor preset-side delta-power split follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The previous follow-up showed that nonlinear `delta_power` becomes useful once it is restricted to the curve-side path. That closed the earlier curve gap further, but the release-facing preset and Quality Loss metrics still remained above the README gates.

This follow-up keeps the new best curve-side branch fixed and tests whether a preset-side-only `delta_power` can improve the release-facing preset metrics without giving back the curve gain.

## Change

Tracked profile:

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta105_profile.json`

Tracked preset-side setting:

- `matched_ori_acutance_preset_correction_delta_power = 1.05`

The curve-side branch stays fixed at the current best setting:

- `matched_ori_acutance_curve_correction_delta_power = 0.95`

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_split_search.json`

Measured against the current best curve-side branch:

- baseline curve-side `delta_power = 0.95`
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04375`
  - `overall_quality_loss_mae_mean = 2.35463`
- preset-side `delta_power = 0.95`
  - `acutance_focus_preset_mae_mean = 0.04479`
  - `overall_quality_loss_mae_mean = 2.39489`
- preset-side `delta_power = 1.05`
  - `acutance_focus_preset_mae_mean = 0.04328`
  - `overall_quality_loss_mae_mean = 2.34352`
- preset-side `delta_power = 1.10`
  - `acutance_focus_preset_mae_mean = 0.04330`
  - `overall_quality_loss_mae_mean = 2.35705`
- preset-side `delta_power = 1.15`
  - `acutance_focus_preset_mae_mean = 0.04354`
  - `overall_quality_loss_mae_mean = 2.38205`

Across the bounded search, the observable curve branch stayed fixed:

- `curve_mae_mean = 0.03776865`

## Validation

```bash
python3 -m algo.benchmark_parity_psd_mtf \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta105_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta105_psd_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta105_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta105_benchmark.json
```

## Result

Compared with the earlier curve-side-only `delta_power = 0.95` branch:

- `curve_mae_mean`: unchanged at `0.03776865`
- `acutance_focus_preset_mae_mean`: `0.04375 -> 0.04328`
- `overall_quality_loss_mae_mean`: `2.35463 -> 2.34352`
- `5.5" Phone Display Acutance` MAE: `0.01919 -> 0.01775`
- `5.5" Phone Display Quality Loss` MAE: `0.37906 -> 0.35204`

The reported-MTF branch remains fixed:

- `curve_mae_mean = 0.04306442`
- `mtf_abs_signed_rel_mean = 0.08692956`

## Interpretation

This is the strongest overall issue-29 branch so far.

The bounded preset-side search clarifies the remaining trade-off:

- preset-side `delta_power = 1.05` is the best overall point in this local neighborhood
- larger preset-side expansion (`1.10`, `1.15`) keeps improving the phone preset, but starts giving back too much overall Quality Loss and non-phone preset fit
- preset-side compression (`0.95`) is clearly harmful

So the useful split is now asymmetric:

- curve-side `delta_power < 1`
- preset-side `delta_power > 1`, but only mildly

The canonical README target is still not fully closed:

- `curve_mae_mean = 0.03776865` is still above the release-facing README acceptance gate (`<= 0.020`)
- `acutance_focus_preset_mae_mean = 0.04328` is still above the release-facing README acceptance gate (`<= 0.030`)
- `overall_quality_loss_mae_mean = 2.34352` is still above the release-facing README acceptance gate (`<= 1.30`)

But this branch now improves the release-facing preset and overall Quality Loss metrics without giving back the stronger curve branch established in the previous follow-up.
