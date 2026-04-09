# Imatest Parity Tuned Acutance-Only Reference Anchor Follow-up

This note records the eighth issue `#29` follow-up pass.

It builds directly on the earlier acutance-only branch from
[imatest_parity_reference_anchor_acutance_only_followup.md](./imatest_parity_reference_anchor_acutance_only_followup.md).

Motivation:

- the full `acutance_only` anchor was the first branch to keep the reported MTF residuals stable while preserving the strong preset / Quality Loss gains
- but its Acutance-curve residual was still clearly above the current best reference-refined branch
- after the earlier global ramp test failed, the next narrow question was whether a simple strength retune works once the anchor is already restricted to the acutance path

This pass therefore keeps the same `acutance_only` branch and tests a lighter strength:

- `matched_ori_anchor_mode = acutance_only`
- `matched_ori_correction_strength = 0.85`

This is still a global retune, but now it acts only on the acutance side rather than on the reported MTF branch.

## Profiles Compared

Benchmark artifacts:

- [../artifacts/imatest_parity_reference_anchor_acutance_only_strength085_psd_benchmark.json](../artifacts/imatest_parity_reference_anchor_acutance_only_strength085_psd_benchmark.json)
- [../artifacts/imatest_parity_reference_anchor_acutance_only_strength085_benchmark.json](../artifacts/imatest_parity_reference_anchor_acutance_only_strength085_benchmark.json)

Profiles:

1. current best toe-plus-sensor plus reference-refined branch
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_refined_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_refined_profile.json)
2. full-strength acutance-only matched-reference anchor
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_profile.json)
3. tuned `0.85` acutance-only matched-reference anchor
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_strength085_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_strength085_profile.json)

## PSD / MTF Result

Compared with the full-strength acutance-only branch:

- `curve_mae_mean`: `0.0438585 -> 0.0423558`
- mean absolute band signed-rel error: unchanged at `0.0869296`
- `high signed-rel mean`: unchanged at `0.04964`
- `top signed-rel mean`: unchanged at `-0.16463`

Interpretation:

- the reported MTF residual bands remain unchanged, exactly as expected for the acutance-only family
- the Acutance-curve residual does improve modestly with the weaker strength
- this shows the remaining curve miss is at least somewhat tunable on the acutance side without reopening the reported MTF branch

## Acutance / Quality Loss Result

Compared with the full-strength acutance-only branch:

- `acutance_focus_preset_mae_mean`: `0.0505124 -> 0.0526345`
- `overall_quality_loss_mae_mean`: `2.7788753 -> 2.8110723`
- `5.5" Phone Display Acutance` MAE: `0.0145547 -> 0.0257482`
- `5.5" Phone Display Quality Loss` MAE: `0.3089123 -> 0.4688160`

Compared with the current best reference-refined branch:

- `curve_mae_mean`: `0.0379513 -> 0.0423558`
- `acutance_focus_preset_mae_mean`: `0.0680820 -> 0.0526345`
- `overall_quality_loss_mae_mean`: `3.0020871 -> 2.8110723`

Interpretation:

- the strength retune gives back a small amount of the preset / quality win from the full-strength acutance-only branch
- but it still remains materially better than the reference-refined branch on the focus presets and overall Quality Loss
- this is a better compromise than either the full-strength branch or the earlier ramped branch if the goal is to narrow the curve miss without discarding most of the acutance-side gain

## Working Conclusion

This pass further narrows the acutance-side reference family for issue `#29`:

- the remaining Acutance-curve miss is not fixed, but it can be reduced by retuning the acutance-only anchor
- that improvement does not require touching the reported MTF branch
- the trade-off is now smaller and better localized than before

What remains:

- the README target is still not reached because the Acutance-curve residual is still above the reference-refined branch
- however, the acutance-only family now has a documented compromise point instead of only two extremes
- the next useful step should focus on a more structured acutance-side shaping method than a single global strength scalar
