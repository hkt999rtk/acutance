# Imatest parity direct acutance-curve anchor preset-side delta-power curve extension follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The previous follow-up showed that the preset-side `delta_power` curve neighborhood was still improving through a phone-region lift of `1.25`.

This extension asks the next concrete question:

- does that same phone-region branch keep improving past `1.25`
- or is the current winning neighborhood already saturated

## Change

Tracked winning extended profile:

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone135_profile.json`

Tracked winning extension:

- `matched_ori_acutance_preset_correction_delta_power_values = [1.05, 1.05, 1.35, 1.35]`

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_extend_search.json`

Measured against the previous best tracked branch (`phone125`):

- baseline `phone125`
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04271`
  - `overall_quality_loss_mae_mean = 2.33488`
  - phone Acutance / Quality Loss MAE `= 0.01488 / 0.30881`
- phone-region `1.30`
  - `acutance_focus_preset_mae_mean = 0.04267`
  - `overall_quality_loss_mae_mean = 2.33453`
  - phone Acutance / Quality Loss MAE `= 0.01467 / 0.30707`
- phone-region `1.35`
  - `acutance_focus_preset_mae_mean = 0.04263`
  - `overall_quality_loss_mae_mean = 2.33421`
  - phone Acutance / Quality Loss MAE `= 0.01451 / 0.30549`
- tapered `1.02 / 1.03 / 1.05 / 1.20 / 1.30`
  - `acutance_focus_preset_mae_mean = 0.04279`
  - `overall_quality_loss_mae_mean = 2.33412`
  - phone Acutance / Quality Loss MAE `= 0.01527 / 0.31328`

Across the whole bounded extension search, the observable curve branch stayed fixed:

- `curve_mae_mean = 0.03776865`

## Validation

```bash
python3 -m algo.benchmark_parity_psd_mtf \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone135_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_curve_phone135_psd_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone135_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_curve_phone135_benchmark.json
```

## Result

This is now the strongest overall issue-29 branch so far.

Compared with the previous `phone125` branch:

- `curve_mae_mean`: unchanged at `0.03776865`
- `acutance_focus_preset_mae_mean`: `0.04271 -> 0.04263`
- `overall_quality_loss_mae_mean`: `2.33488 -> 2.33421`
- `5.5" Phone Display Acutance` MAE: `0.01488 -> 0.01451`
- `5.5" Phone Display Quality Loss` MAE: `0.30881 -> 0.30549`

The reported-MTF branch remains fixed:

- `curve_mae_mean = 0.04306442`
- `mtf_abs_signed_rel_mean = 0.08692956`

## Interpretation

This preset-side neighborhood is still directionally useful past `1.25`:

- a stronger uniform phone-region lift through `1.35` still improves focus preset, overall Quality Loss, and the phone preset together
- the tapered variant does edge slightly lower on overall Quality Loss alone, but it is clearly worse on focus preset and both phone metrics
- so the best current trade-off in this local neighborhood is still the uniform phone-region branch, now at `1.35`

The canonical README target is still not fully closed:

- `curve_mae_mean = 0.03776865` is still above the release-facing README acceptance gate (`<= 0.020`)
- `acutance_focus_preset_mae_mean = 0.04263` is still above the release-facing README acceptance gate (`<= 0.030`)
- `overall_quality_loss_mae_mean = 2.33421` is still above the release-facing README acceptance gate (`<= 1.30`)

But the release-facing preset and Quality Loss metrics continue to improve without giving back the stronger curve branch already established earlier.
