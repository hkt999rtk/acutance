# Imatest parity direct acutance-curve anchor preset-side delta-power curve outer follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The previous follow-up showed that the preset-side `delta_power` curve neighborhood was still improving through a phone-region lift of `1.50`.

This follow-up asks the next concrete question:

- does that same uniform phone-region branch keep improving beyond `1.50`
- or has the local neighborhood finally started to flatten out

## Change

Tracked winning outer profile:

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone170_profile.json`

Tracked winning outer extension:

- `matched_ori_acutance_preset_correction_delta_power_values = [1.05, 1.05, 1.70, 1.70]`

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_outer_search.json`

Measured against the previous best tracked branch (`phone150`):

- baseline `phone150`
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04256`
  - `overall_quality_loss_mae_mean = 2.33358`
  - phone Acutance / Quality Loss MAE `= 0.01414 / 0.30235`
- phone-region `1.55`
  - `acutance_focus_preset_mae_mean = 0.04254`
  - `overall_quality_loss_mae_mean = 2.33346`
  - phone Acutance / Quality Loss MAE `= 0.01404 / 0.30174`
- phone-region `1.60`
  - `acutance_focus_preset_mae_mean = 0.04252`
  - `overall_quality_loss_mae_mean = 2.33335`
  - phone Acutance / Quality Loss MAE `= 0.01395 / 0.30118`
- phone-region `1.70`
  - `acutance_focus_preset_mae_mean = 0.04250`
  - `overall_quality_loss_mae_mean = 2.33316`
  - phone Acutance / Quality Loss MAE `= 0.01383 / 0.30021`

Across the whole bounded outer search, the observable curve branch stayed fixed:

- `curve_mae_mean = 0.03776865`

## Validation

```bash
python3 -m algo.benchmark_parity_psd_mtf \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone170_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_curve_phone170_psd_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone170_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_curve_phone170_benchmark.json
```

## Result

This is now the strongest overall issue-29 branch so far.

Compared with the previous `phone150` branch:

- `curve_mae_mean`: unchanged at `0.03776865`
- `acutance_focus_preset_mae_mean`: `0.04256 -> 0.04250`
- `overall_quality_loss_mae_mean`: `2.33358 -> 2.33316`
- `5.5" Phone Display Acutance` MAE: `0.01414 -> 0.01383`
- `5.5" Phone Display Quality Loss` MAE: `0.30235 -> 0.30021`

The reported-MTF branch remains fixed:

- `curve_mae_mean = 0.04306442`
- `mtf_abs_signed_rel_mean = 0.08692956`

## Interpretation

This preset-side neighborhood still has not saturated:

- the uniform phone-region branch continues to improve monotonically through `1.55`, `1.60`, and `1.70`
- no rollback is visible yet in focus preset, overall Quality Loss, or the phone preset

So the best current trade-off in this local neighborhood is now the stronger `1.70` phone-region preset-side nonlinear branch.

The canonical README target is still not fully closed:

- `curve_mae_mean = 0.03776865` is still above the release-facing README acceptance gate (`<= 0.020`)
- `acutance_focus_preset_mae_mean = 0.04250` is still above the release-facing README acceptance gate (`<= 0.030`)
- `overall_quality_loss_mae_mean = 2.33316` is still above the release-facing README acceptance gate (`<= 1.30`)

But the release-facing preset and Quality Loss metrics continue to improve without giving back the stronger curve branch already established earlier.
