# Imatest Parity Acutance-Curve Reference Anchor Follow-up

This note records the twelfth issue `#29` follow-up pass.

It builds on the current best mid-dip acutance-only branch from
[imatest_parity_reference_anchor_acutance_only_mid_dip_followup.md](./imatest_parity_reference_anchor_acutance_only_mid_dip_followup.md).

Motivation:

- the local acutance-side strength-curve neighborhood is now documented as saturated
- the remaining mismatch is specifically in the observable Acutance curve, not the reported-MTF branch
- the next useful family is therefore a direct acutance-domain reference anchor instead of another MTF-side strength retune

This pass keeps the existing mid-dip `acutance_only` MTF branch and adds a new downstream correction:

- derive a matched-`ori` correction curve in observable Acutance space
- parameterize that correction over relative viewing scale `viewing_distance_cm / print_height_cm`
- apply it only after the existing acutance-side MTF branch, leaving the reported-MTF path unchanged

The tracked profile uses:

- `matched_ori_acutance_reference_anchor = true`
- `matched_ori_acutance_correction_clip_lo = 0.9`
- `matched_ori_acutance_correction_clip_hi = 1.1`
- `matched_ori_acutance_correction_strength = 0.75`

## Profiles Compared

Benchmark artifacts:

- [../artifacts/imatest_parity_reference_anchor_acutance_only_curve_anchor_psd_benchmark.json](../artifacts/imatest_parity_reference_anchor_acutance_only_curve_anchor_psd_benchmark.json)
- [../artifacts/imatest_parity_reference_anchor_acutance_only_curve_anchor_benchmark.json](../artifacts/imatest_parity_reference_anchor_acutance_only_curve_anchor_benchmark.json)

Profiles:

1. current best reference-refined branch
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_refined_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_refined_profile.json)
2. current best mid-dip acutance-only branch
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_mid_dip_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_mid_dip_profile.json)
3. new acutance-curve anchor branch
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_profile.json)

## PSD / MTF Result

Compared with the current mid-dip branch:

- `curve_mae_mean`: unchanged at `0.0430644`
- mean absolute band signed-rel error: unchanged at `0.0869296`
- `high signed-rel mean`: unchanged at `0.04964`
- `top signed-rel mean`: unchanged at `-0.16463`

Interpretation:

- the reported-MTF branch is exactly unchanged
- this confirms the new family really is downstream-only and does not reopen the earlier PSD / MTF fit

## Acutance / Quality Loss Result

Compared with the current mid-dip branch:

- `curve_mae_mean`: `0.0430644 -> 0.0384938`
- `acutance_focus_preset_mae_mean`: `0.0494745 -> 0.0459659`
- `overall_quality_loss_mae_mean`: `2.7318693 -> 2.4157875`
- `5.5" Phone Display Acutance` MAE: `0.0144692 -> 0.0292175`
- `5.5" Phone Display Quality Loss` MAE: `0.3077102 -> 0.5717982`

Compared with the current best reference-refined branch:

- `curve_mae_mean`: `0.0381238 -> 0.0384938`
- `acutance_focus_preset_mae_mean`: `0.0682267 -> 0.0459659`
- `overall_quality_loss_mae_mean`: `3.0115812 -> 2.4157875`
- `5.5" Phone Display Acutance` MAE: `0.0978992 -> 0.0292175`
- `5.5" Phone Display Quality Loss` MAE: `1.0173264 -> 0.5717982`

Interpretation:

- this is the first post-mid-dip family that nearly closes the remaining curve gap while also improving the overall focus-preset and Quality Loss summaries
- the remaining trade-off is now much narrower and more explicit: the direct acutance-curve anchor gives back part of the earlier phone-specific win from the mid-dip branch
- even with that give-back, the phone preset remains materially better than the reference-refined branch

## Working Conclusion

This pass materially advances issue `#29`:

- the remaining curve gap versus the reference-refined branch is now very small
- the overall Acutance / Quality Loss summary is substantially better than the mid-dip branch
- the reported-MTF branch remains fixed and validated

What remains:

- the canonical README target is still not fully reached because this new branch reopens some of the phone-preset error that the mid-dip branch had nearly eliminated
- the next useful step should keep the direct acutance-domain anchor family, but make it more phone-preserving or preset-conditioned instead of reverting to another MTF-side local retune
