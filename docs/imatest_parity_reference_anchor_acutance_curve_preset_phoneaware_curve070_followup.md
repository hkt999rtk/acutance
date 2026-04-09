# Imatest parity direct acutance-curve anchor preset-phone-aware curve-0.70 follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

After splitting the phone-aware shaping onto the preset-only path, the remaining open gap was the curve-side direct acutance-domain anchor itself. This follow-up checks whether a small scalar retune of that curve-side strength can reduce `curve_mae_mean` further without touching the now-stable preset metrics.

## Change

Keep the preset-only phone-aware branch unchanged on the preset side:

- `matched_ori_acutance_preset_strength_curve_relative_scales = [0.0, 3.0, 4.5, 5.8, 6.2]`
- `matched_ori_acutance_preset_strength_curve_values = [1.0, 1.0, 0.85, 0.45, 0.45]`

Then retune only the curve-side direct acutance-domain anchor strength:

- `matched_ori_acutance_correction_strength = 0.70`

Tracked profile:

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve070_profile.json`

## Bounded search

Bounded probes around the earlier `0.75` preset-only branch:

- `0.80`: `curve_mae_mean = 0.03859`
- `0.75`: `curve_mae_mean = 0.03849`
- `0.70`: `curve_mae_mean = 0.03845`
- `0.65`: `curve_mae_mean = 0.03846`

The preset metrics were unchanged across these probes because the preset-only strength curve stays fixed. That makes `0.70` the best local scalar in this bounded neighborhood.

## Validation

```bash
python3 -m pytest tests/test_dead_leaves_mtf_compensation.py tests/test_benchmark_parity_psd_mtf.py tests/test_benchmark_parity_acutance_quality_loss.py
python3 -m py_compile algo/parity_benchmark_common.py algo/benchmark_parity_psd_mtf.py algo/benchmark_parity_acutance_quality_loss.py
python3 -m algo.benchmark_parity_psd_mtf \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve070_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve070_psd_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve070_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_curve070_benchmark.json
```

## Result

Compared with the earlier preset-only phone-aware branch (`0.75` curve-side strength):

- `curve_mae_mean`: `0.03849 -> 0.03845`
- `acutance_focus_preset_mae_mean`: unchanged at `0.04375`
- `overall_quality_loss_mae_mean`: unchanged at `2.35463`
- `5.5" Phone Display Acutance` MAE: unchanged at `0.01919`
- `5.5" Phone Display Quality Loss` MAE: unchanged at `0.37906`

## Interpretation

This is a small but real improvement. The preset-only split remains the right structure, and the best bounded scalar retune inside that structure is slightly lower than the earlier `0.75` value.

The canonical README target is still not fully closed:

- `curve_mae_mean = 0.03845` is still slightly above the earlier reference-refined branch (`0.03795`)
- `5.5" Phone Display Acutance` MAE `= 0.01919` is still slightly above the earlier mid-dip extreme (`0.01447`)

So the next useful work is no longer another local scalar retune. It should keep this `0.70` preset-only branch as the current best branch and move to a more structured curve-side shape if further curve gain is needed.
