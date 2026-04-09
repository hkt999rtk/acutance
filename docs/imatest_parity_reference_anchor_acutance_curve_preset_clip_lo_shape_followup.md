# Imatest parity direct acutance-curve anchor preset-side clip-lo shape follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The previous follow-up established the first bounded local best point in the uniform phone-region preset-side `delta_power` family at `1.85`.

This follow-up tests a different preset-side model family:

- keep the `phone185` branch fixed
- add relative-scale-shaped preset-side lower clipping on the direct Acutance correction path
- check whether the remaining phone and Quality Loss gap is limited by the low side of the correction curve rather than by more `delta_power`

## Change

New code support:

- `clip_reference_correction_curve()` now supports relative-scale-shaped `clip_lo` curves in addition to the existing `clip_hi` support
- both parity benchmark profile schemas now accept:
  - `matched_ori_acutance_curve_correction_clip_lo_relative_scales`
  - `matched_ori_acutance_curve_correction_clip_lo_values`
  - `matched_ori_acutance_preset_correction_clip_lo_relative_scales`
  - `matched_ori_acutance_preset_correction_clip_lo_values`
- focused regression coverage was added for the new low-clip path

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_preset_clip_lo_shape_search.json`

Measured against the current best tracked branch (`phone185`):

- baseline `phone185`
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 2.33309`
  - phone Acutance / Quality Loss MAE `= 0.01380 / 0.29987`
- phone-region `clip_lo = 0.98`
  - exact no-op on all tracked summary metrics
- phone-region `clip_lo = 1.00`
  - exact no-op on all tracked summary metrics

Across the whole bounded search, the observable curve branch stayed fixed:

- `curve_mae_mean = 0.03776865`

## Validation

```bash
python3 -m pytest \
  tests/test_benchmark_parity_acutance_quality_loss.py \
  tests/test_benchmark_parity_psd_mtf.py \
  tests/test_dead_leaves_mtf_compensation.py
python3 -m py_compile \
  algo/parity_benchmark_common.py \
  algo/benchmark_parity_psd_mtf.py \
  algo/benchmark_parity_acutance_quality_loss.py
```

## Result

This is a bounded negative result.

The new preset-side `clip_lo` shape family does not improve the current best branch:

- both bounded phone-region floor probes (`0.98` and `1.00`) are exact no-ops
- the best tracked branch for issue `#29` remains the earlier `phone185` preset-side `delta_power` branch

## Interpretation

This rules out another nearby preset-side local explanation:

- the remaining phone and Quality Loss gap is not currently limited by the low side of the preset-side correction curve in this neighborhood
- the next useful step should move to a different preset/quality-side family instead of more preset-side low-clip tuning
