# Imatest Parity Phone-Aware Acutance-Curve Anchor Follow-up

This note records the fourteenth issue `#29` follow-up pass.

It builds directly on the direct acutance-domain anchor branch from
[imatest_parity_reference_anchor_acutance_curve_followup.md](./imatest_parity_reference_anchor_acutance_curve_followup.md)
and the negative-result fade search from
[imatest_parity_reference_anchor_acutance_curve_fade_followup.md](./imatest_parity_reference_anchor_acutance_curve_fade_followup.md).

Motivation:

- the direct acutance-domain anchor became the strongest branch so far for the remaining canonical curve gap
- the fade-out search showed that a simple boundary taper above the observable curve range is not enough
- the remaining miss is now specifically the phone preset, which sits at a much larger relative viewing scale than the other presets

This pass therefore keeps the direct acutance-domain anchor but adds a high-scale strength curve:

- keep full strength through the observable curve range and the nearby preset scales
- only weaken the direct acutance-domain anchor in the phone-scale region
- leave the reported-MTF branch unchanged

The tracked profile uses:

- `matched_ori_acutance_strength_curve_relative_scales = [0.0, 3.0, 4.5, 5.8, 6.2]`
- `matched_ori_acutance_strength_curve_values = [1.0, 1.0, 0.85, 0.45, 0.45]`

## Profiles Compared

Benchmark artifacts:

- [../artifacts/imatest_parity_reference_anchor_acutance_only_curve_anchor_phoneaware_psd_benchmark.json](../artifacts/imatest_parity_reference_anchor_acutance_only_curve_anchor_phoneaware_psd_benchmark.json)
- [../artifacts/imatest_parity_reference_anchor_acutance_only_curve_anchor_phoneaware_benchmark.json](../artifacts/imatest_parity_reference_anchor_acutance_only_curve_anchor_phoneaware_benchmark.json)

Profiles:

1. current best reference-refined branch
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_refined_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_refined_profile.json)
2. current best mid-dip acutance-only branch
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_mid_dip_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_mid_dip_profile.json)
3. direct acutance-domain anchor branch
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_profile.json)
4. phone-aware direct acutance-domain anchor branch
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_phoneaware_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_phoneaware_profile.json)

## PSD / MTF Result

Compared with both the mid-dip branch and the earlier direct acutance-domain anchor:

- `curve_mae_mean`: unchanged at `0.0430644`
- mean absolute band signed-rel error: unchanged at `0.0869296`
- `high signed-rel mean`: unchanged at `0.04964`
- `top signed-rel mean`: unchanged at `-0.16463`

Interpretation:

- the reported-MTF branch remains fully fixed
- the new phone-aware shaping acts only in acutance space

## Acutance / Quality Loss Result

Compared with the earlier direct acutance-domain anchor:

- `curve_mae_mean`: `0.0384938 -> 0.0395264`
- `acutance_focus_preset_mae_mean`: `0.0459659 -> 0.0437495`
- `overall_quality_loss_mae_mean`: `2.4157875 -> 2.3546342`
- `5.5" Phone Display Acutance` MAE: `0.0292175 -> 0.0191923`
- `5.5" Phone Display Quality Loss` MAE: `0.5717982 -> 0.3790641`

Compared with the mid-dip branch:

- `curve_mae_mean`: `0.0430644 -> 0.0395264`
- `acutance_focus_preset_mae_mean`: `0.0494745 -> 0.0437495`
- `overall_quality_loss_mae_mean`: `2.7318693 -> 2.3546342`
- `5.5" Phone Display Acutance` MAE: `0.0144692 -> 0.0191923`
- `5.5" Phone Display Quality Loss` MAE: `0.3077102 -> 0.3790641`

Compared with the current best reference-refined branch:

- `curve_mae_mean`: `0.0381238 -> 0.0395264`
- `acutance_focus_preset_mae_mean`: `0.0682267 -> 0.0437495`
- `overall_quality_loss_mae_mean`: `3.0115812 -> 2.3546342`
- `5.5" Phone Display Acutance` MAE: `0.0978992 -> 0.0191923`
- `5.5" Phone Display Quality Loss` MAE: `1.0173264 -> 0.3790641`

Interpretation:

- this is the best overall compromise branch so far in issue `#29`
- it preserves most of the new curve gain from the direct acutance-domain anchor
- it materially recovers the phone preset relative to that earlier direct anchor
- it also improves the overall focus-preset and Quality Loss summaries further

## Working Conclusion

This pass materially advances the direct acutance-domain family:

- the phone regression can be reduced inside this family when the correction is weakened only in the high-scale phone region
- the reported-MTF branch remains fixed and validated
- the remaining trade-off is now much smaller than before

What remains:

- the canonical README target is still not fully reached because the curve residual is still slightly above the reference-refined branch, and the phone preset is still not quite as low as the earlier mid-dip branch
- however, this is the strongest overall issue-29 branch so far, and the next useful step should continue refining this phone-aware direct acutance-domain family rather than reverting to older local retunes
