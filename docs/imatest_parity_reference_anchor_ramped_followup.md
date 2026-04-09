# Imatest Parity Ramped Reference Anchor Follow-up

This note records the sixth issue `#29` follow-up pass.

It builds directly on the earlier matched-reference branch from
[imatest_parity_reference_anchor_followup.md](./imatest_parity_reference_anchor_followup.md).

Motivation:

- the full matched-`ori` anchor materially improved preset Acutance and overall Quality Loss
- but it also made full-curve fidelity clearly worse
- the next obvious question was whether that trade-off came mostly from applying the anchor too strongly and too early across the whole frequency range

This pass therefore keeps the same matched-`ori` family but constrains it with a simple ramp:

- `matched_ori_correction_strength = 0.5`
- `matched_ori_blend_start_cpp = 0.1`
- `matched_ori_blend_stop_cpp = 0.3`

That means:

- the matched-reference multiplier is only half-strength overall
- it fades in gradually instead of affecting the whole curve equally
- the test is specifically checking whether a lighter high-frequency-biased anchor can keep the preset gains while recovering curve fidelity

## Profiles Compared

Benchmark artifacts:

- [../artifacts/imatest_parity_reference_anchor_ramped_psd_benchmark.json](../artifacts/imatest_parity_reference_anchor_ramped_psd_benchmark.json)
- [../artifacts/imatest_parity_reference_anchor_ramped_benchmark.json](../artifacts/imatest_parity_reference_anchor_ramped_benchmark.json)

Profiles:

1. current best toe-plus-sensor plus reference-refined branch
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_refined_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_refined_profile.json)
2. full matched-reference anchor
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_profile.json)
3. ramped matched-reference anchor
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_ramped_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_ramped_profile.json)

## PSD / MTF Result

Compared with the current best reference-refined branch:

- `curve_mae_mean`: `0.0379513 -> 0.0382989`
- mean absolute band signed-rel error: `0.0869296 -> 0.0800006`
- `high signed-rel mean`: `0.04964 -> 0.03661`
- `top signed-rel mean`: `-0.16463 -> -0.14673`

Compared with the full anchor branch:

- `curve_mae_mean`: `0.0426246 -> 0.0382989`

Interpretation:

- the simple ramp does recover most of the curve loss from the full anchor branch
- it also improves the signed-rel band errors beyond both earlier anchor variants
- so the shaping idea is directionally valid on the PSD / MTF side

## Acutance / Quality Loss Result

Compared with the current best reference-refined branch:

- `curve_mae_mean`: `0.0379513 -> 0.0409549`
- `acutance_focus_preset_mae_mean`: `0.0680820 -> 0.0700440`
- `overall_quality_loss_mae_mean`: `3.0020871 -> 3.0892216`

Compared with the full anchor branch:

- `acutance_focus_preset_mae_mean`: `0.0505124 -> 0.0700440`
- `overall_quality_loss_mae_mean`: `2.7788753 -> 3.0892216`

Interpretation:

- the same ramp that recovers curve fidelity also gives back the preset Acutance and overall Quality Loss gains
- this means the earlier anchor benefit is not explained by a simple overly strong full-band correction alone
- a naive frequency ramp is therefore not enough to close the issue-29 trade-off

## Working Conclusion

This pass narrows the matched-reference family for issue `#29`:

- a simple ramped anchor can mostly recover the curve side
- but it does so by losing the preset and quality improvements that made the full anchor interesting
- the next useful step is not another simple global strength/ramp retune

What remains:

- the README target is still not reached
- the best curve-oriented branch remains toe-plus-sensor plus reference-refined ROI
- the best preset / quality branch remains the stronger full anchor
- later work should try a more structured intrinsic/reference correction family, not just a globally weakened version of the current anchor
