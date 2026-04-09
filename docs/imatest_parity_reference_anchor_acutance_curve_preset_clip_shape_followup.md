# Imatest parity direct acutance-curve anchor preset-side clip-shape follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The current best issue-29 branch already uses:

- curve-side `delta_power = 0.95`
- preset-side `delta_power = 1.05`

That improved the release-facing preset metrics while preserving the best current curve branch.

This follow-up tests a new preset/quality-side family on top of that branch: instead of changing preset-side strength or `delta_power`, allow the direct matched-`ori` Acutance correction `clip_hi` to vary with preset relative viewing scale so the phone region can receive extra headroom without disturbing the rest of the preset path.

## Change

The benchmark path now supports preset-side direct Acutance correction `clip_hi` shaping:

- `matched_ori_acutance_preset_correction_clip_hi_relative_scales`
- `matched_ori_acutance_preset_correction_clip_hi_values`

This pass also fixes the preset-side shaped-clip application path so the variable cap is applied on the correction-curve domain (`correction_positions`) before interpolation to the preset positions.

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_preset_clip_shape_search.json`

Measured against the current best tracked branch (`curve_delta095 + preset_delta105`):

- baseline
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04328`
  - `overall_quality_loss_mae_mean = 2.34352`
  - phone Acutance / Quality Loss MAE `= 0.01775 / 0.35204`
- preset phone clip `1.12`
  - `matched_ori_acutance_preset_correction_clip_hi_values = [1.10, 1.10, 1.12, 1.12]`
  - no change on any tracked summary metric
- preset phone clip `1.14`
  - `matched_ori_acutance_preset_correction_clip_hi_values = [1.10, 1.10, 1.14, 1.14]`
  - no change on any tracked summary metric

## Validation

```bash
python3 -m pytest tests/test_benchmark_parity_acutance_quality_loss.py tests/test_benchmark_parity_psd_mtf.py tests/test_dead_leaves_mtf_compensation.py
python3 -m py_compile algo/parity_benchmark_common.py algo/benchmark_parity_psd_mtf.py algo/benchmark_parity_acutance_quality_loss.py
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  /tmp/preset_clip_phone112.json \
  --output /tmp/preset_clip_phone112_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  /tmp/preset_clip_phone114.json \
  --output /tmp/preset_clip_phone114_benchmark.json
```

## Result

This is a bounded negative result.

The new preset-side clip-shape family is now correctly supported in code, but the first bounded phone-relief probes are exact no-ops on the tracked branch:

- `curve_mae_mean` stays at `0.03776865`
- `acutance_focus_preset_mae_mean` stays at `0.04328`
- `overall_quality_loss_mae_mean` stays at `2.34352`
- `5.5" Phone Display Acutance` MAE stays at `0.01775`
- `5.5" Phone Display Quality Loss` MAE stays at `0.35204`

## Interpretation

The useful conclusion is not just that two probes failed. It is narrower and stronger than that:

- the preset-side clip-shape path is now implemented correctly
- moderate extra phone-region clip headroom (`1.12` and `1.14`) does not activate any observable change on the current best branch

That means the remaining release-facing gap is not currently limited by the preset-side `clip_hi` cap in this local neighborhood.

So the next useful preset/quality-side step should not be another small preset clip-headroom retune. The remaining issue-29 work needs a different preset-side or Quality Loss model family.
