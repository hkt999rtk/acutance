# Imatest parity direct acutance-curve anchor preset-side delta-power curve rollover follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The previous follow-up showed that the preset-side `delta_power` curve neighborhood was still improving through a phone-region lift of `1.70`.

This follow-up asks the next concrete question:

- does that same uniform phone-region branch keep improving into a wider outer range
- or does the local neighborhood finally show a turnover point

## Change

Tracked winning rollover profile:

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone185_profile.json`

Tracked winning rollover extension:

- `matched_ori_acutance_preset_correction_delta_power_values = [1.05, 1.05, 1.85, 1.85]`

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_rollover_search.json`

Measured against the previous best tracked branch (`phone170`):

- baseline `phone170`
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04250`
  - `overall_quality_loss_mae_mean = 2.33316`
  - phone Acutance / Quality Loss MAE `= 0.01383 / 0.30021`
- phone-region `1.85`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 2.33309`
  - phone Acutance / Quality Loss MAE `= 0.01380 / 0.29987`
- phone-region `2.00`
  - `acutance_focus_preset_mae_mean = 0.04250`
  - `overall_quality_loss_mae_mean = 2.33325`
  - phone Acutance / Quality Loss MAE `= 0.01384 / 0.30069`
- phone-region `2.25`
  - `acutance_focus_preset_mae_mean = 0.04254`
  - `overall_quality_loss_mae_mean = 2.33367`
  - phone Acutance / Quality Loss MAE `= 0.01407 / 0.30280`

Across the whole bounded rollover search, the observable curve branch stayed fixed:

- `curve_mae_mean = 0.03776865`

## Validation

```bash
python3 -m algo.benchmark_parity_psd_mtf \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone185_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_curve_phone185_psd_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone185_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_curve_phone185_benchmark.json
```

## Result

This is now the strongest overall issue-29 branch so far.

Compared with the previous `phone170` branch:

- `curve_mae_mean`: unchanged at `0.03776865`
- `acutance_focus_preset_mae_mean`: `0.04250 -> 0.04249`
- `overall_quality_loss_mae_mean`: `2.33316 -> 2.33309`
- `5.5" Phone Display Acutance` MAE: `0.01383 -> 0.01380`
- `5.5" Phone Display Quality Loss` MAE: `0.30021 -> 0.29987`

The reported-MTF branch remains fixed:

- `curve_mae_mean = 0.04306442`
- `mtf_abs_signed_rel_mean = 0.08692956`

## Interpretation

This preset-side neighborhood now shows the first bounded rollover:

- the uniform phone-region branch still improves a little more at `1.85`
- but `2.00` and `2.25` are both worse than `1.85`

So the local uniform phone-region family is no longer purely monotonic, and the current bounded best point is now `1.85`.

The canonical README target is still not fully closed:

- `curve_mae_mean = 0.03776865` is still above the release-facing README acceptance gate (`<= 0.020`)
- `acutance_focus_preset_mae_mean = 0.04249` is still above the release-facing README acceptance gate (`<= 0.030`)
- `overall_quality_loss_mae_mean = 2.33309` is still above the release-facing README acceptance gate (`<= 1.30`)

But the release-facing preset and Quality Loss metrics continue to improve without giving back the stronger curve branch already established earlier.
