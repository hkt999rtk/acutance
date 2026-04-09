# Imatest parity direct acutance-curve anchor preset-side delta-power curve further follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The previous follow-up showed that the preset-side `delta_power` curve neighborhood was still improving through a phone-region lift of `1.35`.

This follow-up asks the next concrete question:

- does that same uniform phone-region branch keep improving through `1.40` to `1.50`
- or does the neighborhood finally start to saturate

## Change

Tracked winning further profile:

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone150_profile.json`

Tracked winning further extension:

- `matched_ori_acutance_preset_correction_delta_power_values = [1.05, 1.05, 1.50, 1.50]`

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_further_search.json`

Measured against the previous best tracked branch (`phone135`):

- baseline `phone135`
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04263`
  - `overall_quality_loss_mae_mean = 2.33421`
  - phone Acutance / Quality Loss MAE `= 0.01451 / 0.30549`
- phone-region `1.40`
  - `acutance_focus_preset_mae_mean = 0.04260`
  - `overall_quality_loss_mae_mean = 2.33393`
  - phone Acutance / Quality Loss MAE `= 0.01437 / 0.30407`
- phone-region `1.45`
  - `acutance_focus_preset_mae_mean = 0.04258`
  - `overall_quality_loss_mae_mean = 2.33372`
  - phone Acutance / Quality Loss MAE `= 0.01425 / 0.30303`
- phone-region `1.50`
  - `acutance_focus_preset_mae_mean = 0.04256`
  - `overall_quality_loss_mae_mean = 2.33358`
  - phone Acutance / Quality Loss MAE `= 0.01414 / 0.30235`

Across the whole bounded further search, the observable curve branch stayed fixed:

- `curve_mae_mean = 0.03776865`

## Validation

```bash
python3 -m algo.benchmark_parity_psd_mtf \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone150_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_curve_phone150_psd_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone150_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_curve_phone150_benchmark.json
```

## Result

This is now the strongest overall issue-29 branch so far.

Compared with the previous `phone135` branch:

- `curve_mae_mean`: unchanged at `0.03776865`
- `acutance_focus_preset_mae_mean`: `0.04263 -> 0.04256`
- `overall_quality_loss_mae_mean`: `2.33421 -> 2.33358`
- `5.5" Phone Display Acutance` MAE: `0.01451 -> 0.01414`
- `5.5" Phone Display Quality Loss` MAE: `0.30549 -> 0.30235`

The reported-MTF branch remains fixed:

- `curve_mae_mean = 0.04306442`
- `mtf_abs_signed_rel_mean = 0.08692956`

## Interpretation

This preset-side neighborhood is still not saturated:

- the uniform phone-region branch continues to improve monotonically through `1.40`, `1.45`, and `1.50`
- no rollback is visible yet in focus preset, overall Quality Loss, or the phone preset

So the best current trade-off in this local neighborhood is now the stronger `1.50` phone-region preset-side nonlinear branch.

The canonical README target is still not fully closed:

- `curve_mae_mean = 0.03776865` is still above the release-facing README acceptance gate (`<= 0.020`)
- `acutance_focus_preset_mae_mean = 0.04256` is still above the release-facing README acceptance gate (`<= 0.030`)
- `overall_quality_loss_mae_mean = 2.33358` is still above the release-facing README acceptance gate (`<= 1.30`)

But the release-facing preset and Quality Loss metrics continue to improve without giving back the stronger curve branch already established earlier.
