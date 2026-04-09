# Imatest parity direct acutance-curve anchor preset-side delta-power curve refinement follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The previous follow-up established the first winning preset-side `delta_power` curve:

- keep the non-phone preset region at `1.05`
- lift the phone region to `1.15`

This refinement tests whether that local neighborhood is already saturated or whether a slightly stronger phone-region branch can still improve the release-facing preset and Quality Loss metrics without moving the fixed curve branch.

## Change

Tracked winning refined profile:

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone125_profile.json`

Tracked winning refinement:

- `matched_ori_acutance_preset_correction_delta_power_values = [1.05, 1.05, 1.25, 1.25]`

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_refine_search.json`

Measured against the previous best tracked branch (`phone115`):

- baseline `phone115`
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04290`
  - `overall_quality_loss_mae_mean = 2.33720`
  - phone Acutance / Quality Loss MAE `= 0.01583 / 0.32045`
- phone-region `1.20`
  - `acutance_focus_preset_mae_mean = 0.04279`
  - `overall_quality_loss_mae_mean = 2.33577`
  - phone Acutance / Quality Loss MAE `= 0.01527 / 0.31328`
- phone-region `1.25`
  - `acutance_focus_preset_mae_mean = 0.04271`
  - `overall_quality_loss_mae_mean = 2.33488`
  - phone Acutance / Quality Loss MAE `= 0.01488 / 0.30881`
- tapered `1.02 / 1.03 / 1.05 / 1.15 / 1.20`
  - `acutance_focus_preset_mae_mean = 0.04290`
  - `overall_quality_loss_mae_mean = 2.33556`
  - phone Acutance / Quality Loss MAE `= 0.01583 / 0.32045`

Across the whole bounded refinement search, the observable curve branch stayed fixed:

- `curve_mae_mean = 0.03776865`

## Validation

```bash
python3 -m algo.benchmark_parity_psd_mtf \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone125_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_curve_phone125_psd_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone125_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_curve_phone125_benchmark.json
```

## Result

This is now the strongest overall issue-29 branch so far.

Compared with the previous `phone115` branch:

- `curve_mae_mean`: unchanged at `0.03776865`
- `acutance_focus_preset_mae_mean`: `0.04290 -> 0.04271`
- `overall_quality_loss_mae_mean`: `2.33720 -> 2.33488`
- `5.5" Phone Display Acutance` MAE: `0.01583 -> 0.01488`
- `5.5" Phone Display Quality Loss` MAE: `0.32045 -> 0.30881`

The reported-MTF branch remains fixed:

- `curve_mae_mean = 0.04306442`
- `mtf_abs_signed_rel_mean = 0.08692956`

## Interpretation

The local refinement is still directionally useful:

- stronger phone-region preset-side expansion continues to help through `1.25`
- the simple uniform phone-region lift is still better than the tapered variant tested here

So this local neighborhood is not yet saturated at the earlier `1.15` branch. The new tracked best branch is the stronger `1.25` phone-region preset-side nonlinear profile.

The canonical README target is still not fully closed:

- `curve_mae_mean = 0.03776865` is still above the release-facing README acceptance gate (`<= 0.020`)
- `acutance_focus_preset_mae_mean = 0.04271` is still above the release-facing README acceptance gate (`<= 0.030`)
- `overall_quality_loss_mae_mean = 2.33488` is still above the release-facing README acceptance gate (`<= 1.30`)

But the release-facing preset and Quality Loss metrics continue to improve without giving back the stronger curve branch already established earlier.
