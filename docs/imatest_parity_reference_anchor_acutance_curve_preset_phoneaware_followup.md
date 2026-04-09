# Imatest parity direct acutance-curve anchor preset-phone-aware follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

Keep the stronger direct acutance-domain curve anchor from the earlier follow-up while recovering the phone-preset gain from the later phone-aware branch, without giving back the Acutance-curve improvement again.

## Change

The earlier shared phone-aware branch reused one relative-scale strength curve for both:

- the sampled Acutance curve, and
- the final report presets

This follow-up splits those two responsibilities.

The tracked profile keeps the direct acutance-domain anchor unchanged on the curve side:

- `matched_ori_acutance_correction_strength = 0.75`

Then it applies the phone-aware shaping only to the preset path:

- `matched_ori_acutance_preset_strength_curve_relative_scales = [0.0, 3.0, 4.5, 5.8, 6.2]`
- `matched_ori_acutance_preset_strength_curve_values = [1.0, 1.0, 0.85, 0.45, 0.45]`

Tracked profile:

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_profile.json`

## Validation

```bash
python3 -m pytest tests/test_dead_leaves_mtf_compensation.py tests/test_benchmark_parity_psd_mtf.py tests/test_benchmark_parity_acutance_quality_loss.py
python3 -m py_compile algo/parity_benchmark_common.py algo/benchmark_parity_psd_mtf.py algo/benchmark_parity_acutance_quality_loss.py
python3 -m algo.benchmark_parity_psd_mtf \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_psd_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_only_curve_anchor_preset_phoneaware_benchmark.json
```

## Result

This preset-only split is better than the earlier shared phone-aware branch.

Compared with the shared phone-aware branch:

- `curve_mae_mean`: `0.03953 -> 0.03849`
- `acutance_focus_preset_mae_mean`: unchanged at `0.04375`
- `overall_quality_loss_mae_mean`: unchanged at `2.35463`
- `5.5" Phone Display Acutance` MAE: unchanged at `0.01919`
- `5.5" Phone Display Quality Loss` MAE: unchanged at `0.37906`

Compared with the earlier direct curve-anchor branch:

- `curve_mae_mean`: unchanged at `0.03849`
- `acutance_focus_preset_mae_mean`: `0.04597 -> 0.04375`
- `overall_quality_loss_mae_mean`: `2.41579 -> 2.35463`
- `5.5" Phone Display Acutance` MAE: `0.02922 -> 0.01919`
- `5.5" Phone Display Quality Loss` MAE: `0.57180 -> 0.37906`

## Interpretation

This is the strongest overall issue-29 branch so far:

- it preserves the best current direct acutance-domain curve fit
- it preserves the phone-aware preset gain
- it removes the unnecessary curve giveback from the earlier shared phone-aware branch

The canonical README target is still not fully closed:

- `curve_mae_mean = 0.03849` is still slightly above the earlier reference-refined branch (`0.03795`)
- `5.5" Phone Display Acutance` MAE `= 0.01919` is still slightly above the earlier mid-dip extreme (`0.01447`)

That means the remaining work is now narrower again: keep this preset-only split as the current best branch, then refine the curve-side direct acutance-domain correction without reintroducing the earlier phone regression.
