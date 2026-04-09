# Imatest parity direct acutance-curve anchor delta-power follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

After the preset-only phone-aware split and the gentle-down curve-side shape, the next model-family question was whether the direct Acutance-domain correction should be compressed nonlinearly, rather than only scaled linearly.

This follow-up adds `correction_delta_power` support to the matched-`ori` reference-correction helper so larger correction deltas can be shrunk more than smaller ones.

## Change

New helper support in `algo/parity_benchmark_common.py`:

- `correction_delta_power`

Interpretation:

- `1.0` keeps the old linear correction behavior
- values greater than `1.0` compress large correction deltas toward `1.0`

The Acutance benchmark path now threads this through the curve and preset correction calls, and the PSD benchmark payload mirrors the new field for tracked profile compatibility.

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_delta_power_search.json`

Measured against the current best gentle-down branch:

- baseline `1.0`
  - `curve_mae_mean = 0.03842318`
  - `acutance_focus_preset_mae_mean = 0.04375`
  - `overall_quality_loss_mae_mean = 2.35463`
  - phone Acutance MAE `= 0.01919`
  - phone Quality Loss MAE `= 0.37906`
- `1.15`
  - `curve_mae_mean = 0.03904640`
  - `acutance_focus_preset_mae_mean = 0.04354`
  - `overall_quality_loss_mae_mean = 2.38205`
  - phone Acutance MAE `= 0.01582`
  - phone Quality Loss MAE `= 0.32024`
- `1.30`
  - `curve_mae_mean = 0.03998017`
  - `acutance_focus_preset_mae_mean = 0.04480`
  - `overall_quality_loss_mae_mean = 2.47198`
  - phone Acutance MAE `= 0.01466`
  - phone Quality Loss MAE `= 0.30697`

## Interpretation

This new nonlinear family is a negative result for the current remaining goal.

Increasing `correction_delta_power` does improve the phone preset, but it does so by giving back too much curve:

- `1.15` already degrades `curve_mae_mean` from `0.03842318` to `0.03904640`
- `1.30` degrades it further to `0.03998017`

That means nonlinear compression of the direct Acutance-domain correction is not a good next step if the priority is closing the remaining curve gap on top of the current best branch.

The branch therefore stays on the earlier gentle-down shape as the best current overall result.
