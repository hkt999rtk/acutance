# Imatest parity direct acutance-curve anchor preset-side delta-power curve follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The previous best issue-29 branch already used:

- curve-side `delta_power = 0.95`
- preset-side scalar `delta_power = 1.05`

That improved the release-facing preset metrics while preserving the best current curve branch.

This follow-up tests a new preset-side family on top of that branch: keep the baseline scalar behavior across the non-phone region, but allow stronger preset-side nonlinear expansion only in the high-relative-scale phone region.

## Change

The benchmark path now supports preset-side relative-scale-shaped nonlinear `delta_power`:

- `matched_ori_acutance_preset_correction_delta_power_relative_scales`
- `matched_ori_acutance_preset_correction_delta_power_values`

Tracked winning profile:

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone115_profile.json`

Tracked winning setting:

- `matched_ori_acutance_preset_correction_delta_power_values = [1.05, 1.05, 1.15, 1.15]`

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_search.json`

Measured against the previous best tracked branch (`curve_delta095 + preset_delta105`):

- baseline
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04328`
  - `overall_quality_loss_mae_mean = 2.34352`
  - phone Acutance / Quality Loss MAE `= 0.01775 / 0.35204`
- phone-region `1.10`
  - `acutance_focus_preset_mae_mean = 0.04306`
  - `overall_quality_loss_mae_mean = 2.33954`
  - phone Acutance / Quality Loss MAE `= 0.01663 / 0.33214`
- phone-region `1.15`
  - `acutance_focus_preset_mae_mean = 0.04290`
  - `overall_quality_loss_mae_mean = 2.33720`
  - phone Acutance / Quality Loss MAE `= 0.01583 / 0.32045`
- tapered `1.02 / 1.03 / 1.05 / 1.10 / 1.10`
  - `acutance_focus_preset_mae_mean = 0.04306`
  - `overall_quality_loss_mae_mean = 2.33789`
  - phone Acutance / Quality Loss MAE `= 0.01663 / 0.33214`

Across the whole bounded search, the observable curve branch stayed fixed:

- `curve_mae_mean = 0.03776865`

## Validation

```bash
python3 -m pytest tests/test_benchmark_parity_acutance_quality_loss.py tests/test_benchmark_parity_psd_mtf.py tests/test_dead_leaves_mtf_compensation.py
python3 -m py_compile algo/parity_benchmark_common.py algo/benchmark_parity_psd_mtf.py algo/benchmark_parity_acutance_quality_loss.py
python3 -m algo.benchmark_parity_psd_mtf \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone115_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_curve_phone115_psd_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone115_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_preset_delta_curve_phone115_benchmark.json
```

## Result

This is now the strongest overall issue-29 branch so far.

Compared with the previous best tracked branch:

- `curve_mae_mean`: unchanged at `0.03776865`
- `acutance_focus_preset_mae_mean`: `0.04328 -> 0.04290`
- `overall_quality_loss_mae_mean`: `2.34352 -> 2.33720`
- `5.5" Phone Display Acutance` MAE: `0.01775 -> 0.01583`
- `5.5" Phone Display Quality Loss` MAE: `0.35204 -> 0.32045`

The reported-MTF branch remains fixed:

- `curve_mae_mean = 0.04306442`
- `mtf_abs_signed_rel_mean = 0.08692956`

## Interpretation

The useful preset-side nonlinear family is now clearer:

- keeping the non-phone region at the previous scalar `1.05` is still important
- the remaining win comes from stronger preset-side expansion only in the phone region
- the simple phone-region `1.15` branch is better than both the smaller `1.10` lift and the tapered variant tested here

The canonical README target is still not fully closed:

- `curve_mae_mean = 0.03776865` is still above the release-facing README acceptance gate (`<= 0.020`)
- `acutance_focus_preset_mae_mean = 0.04290` is still above the release-facing README acceptance gate (`<= 0.030`)
- `overall_quality_loss_mae_mean = 2.33720` is still above the release-facing README acceptance gate (`<= 1.30`)

But this branch improves the release-facing preset and overall Quality Loss metrics again without giving back the stronger curve branch already established earlier.
