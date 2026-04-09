# Imatest Parity Piecewise Acutance-Only Reference Anchor Follow-up

This note records the ninth issue `#29` follow-up pass.

It builds on the earlier tuned `0.85` acutance-only branch from
[imatest_parity_reference_anchor_acutance_only_strength_followup.md](./imatest_parity_reference_anchor_acutance_only_strength_followup.md).

Motivation:

- the `0.85` acutance-only branch is the current best compromise in the reference-conditioned family
- the remaining miss is still the Acutance-curve residual
- a plausible next step was to keep full strength at the high-frequency end, where the phone-preset gains likely come from, while weakening only the lower acutance-side frequencies

This pass therefore adds a simple two-level piecewise strength shape:

- `matched_ori_anchor_mode = acutance_only`
- `matched_ori_strength_low = 0.75`
- `matched_ori_strength_high = 1.0`
- `matched_ori_strength_ramp_start_cpp = 0.12`
- `matched_ori_strength_ramp_stop_cpp = 0.30`

That means the anchor is weaker at lower acutance-side frequencies and ramps back up to full strength by the higher band.

## Profiles Compared

Benchmark artifacts:

- [../artifacts/imatest_parity_reference_anchor_acutance_only_piecewise_psd_benchmark.json](../artifacts/imatest_parity_reference_anchor_acutance_only_piecewise_psd_benchmark.json)
- [../artifacts/imatest_parity_reference_anchor_acutance_only_piecewise_benchmark.json](../artifacts/imatest_parity_reference_anchor_acutance_only_piecewise_benchmark.json)

Profiles:

1. full-strength acutance-only matched-reference anchor
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_profile.json)
2. tuned `0.85` acutance-only matched-reference anchor
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_strength085_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_strength085_profile.json)
3. piecewise low/high acutance-only anchor
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_piecewise_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_piecewise_profile.json)

## PSD / MTF Result

Compared with the tuned `0.85` branch:

- `curve_mae_mean`: `0.0423558 -> 0.0440986`
- mean absolute band signed-rel error: unchanged at `0.0869296`
- `high signed-rel mean`: unchanged at `0.04964`
- `top signed-rel mean`: unchanged at `-0.16463`

Interpretation:

- the reported MTF residuals stay fixed, as expected for the acutance-only family
- the Acutance-curve residual gets worse rather than better
- the simple low/high split is therefore not a better curve compromise than the scalar `0.85` branch

## Acutance / Quality Loss Result

Compared with the tuned `0.85` branch:

- `acutance_focus_preset_mae_mean`: `0.0526345 -> 0.0556187`
- `overall_quality_loss_mae_mean`: `2.8110723 -> 2.9027075`
- `5.5" Phone Display Acutance` MAE: `0.0257482 -> 0.0344200`
- `5.5" Phone Display Quality Loss` MAE: `0.4688160 -> 0.5931441`

Interpretation:

- the piecewise split is worse on both the curve side and the preset / quality side
- preserving full strength only at the higher frequencies is not enough to keep the earlier gains
- this is a negative result for the simplest two-band acutance-side shaping hypothesis

## Working Conclusion

This pass narrows the acutance-side family again for issue `#29`:

- the current best compromise remains the scalar `0.85` acutance-only branch
- a simple low/high piecewise strength split does not outperform it
- the remaining work now needs a more structured acutance-side shape than either a single scalar or a naive two-band split
