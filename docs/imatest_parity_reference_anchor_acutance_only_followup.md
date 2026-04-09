# Imatest Parity Acutance-Only Reference Anchor Follow-up

This note records the seventh issue `#29` follow-up pass.

It builds on the earlier matched-reference branches from:

- [imatest_parity_reference_anchor_followup.md](./imatest_parity_reference_anchor_followup.md)
- [imatest_parity_reference_anchor_ramped_followup.md](./imatest_parity_reference_anchor_ramped_followup.md)

Motivation:

- the full matched-`ori` anchor gave the best preset Acutance and overall Quality Loss result so far
- but it also changed the reported MTF path and worsened the Acutance-curve residual
- the ramped branch showed that simply weakening the whole anchor is not enough

This pass therefore tests a narrower interpretation:

- keep the matched-reference anchor on the acutance path
- leave the reported MTF path unchanged
- treat the reference anchor as an acutance-side correction family rather than a general reported-MTF correction

Concretely, the new profile uses:

- `matched_ori_reference_anchor = true`
- `matched_ori_anchor_mode = acutance_only`

That means the PSD / reported-MTF branch keeps the same reference-refined toe-plus-sensor estimate, while the Acutance / Quality Loss branch still gets the matched-reference correction.

## Profiles Compared

Benchmark artifacts:

- [../artifacts/imatest_parity_reference_anchor_acutance_only_psd_benchmark.json](../artifacts/imatest_parity_reference_anchor_acutance_only_psd_benchmark.json)
- [../artifacts/imatest_parity_reference_anchor_acutance_only_benchmark.json](../artifacts/imatest_parity_reference_anchor_acutance_only_benchmark.json)

Profiles:

1. current best toe-plus-sensor plus reference-refined branch
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_refined_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_refined_profile.json)
2. full matched-reference anchor
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_profile.json)
3. acutance-only matched-reference anchor
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_profile.json)

## PSD / MTF Result

Compared with the current best reference-refined branch:

- `curve_mae_mean`: `0.0379513 -> 0.0438585`
- mean absolute band signed-rel error: `0.0869296 -> 0.0869296`
- `high signed-rel mean`: `0.04964 -> 0.04964`
- `top signed-rel mean`: `-0.16463 -> -0.16463`

Interpretation:

- the reported MTF residual bands are unchanged from the reference-refined branch
- this confirms the new mode is not perturbing the PSD / reported-MTF side
- the higher `curve_mae_mean` here comes from the Acutance-curve side of the benchmark, not from a worse reported MTF fit

## Acutance / Quality Loss Result

Compared with the current best reference-refined branch:

- `curve_mae_mean`: `0.0379513 -> 0.0438585`
- `acutance_focus_preset_mae_mean`: `0.0680820 -> 0.0505124`
- `overall_quality_loss_mae_mean`: `3.0020871 -> 2.7788753`
- `5.5" Phone Display Acutance` MAE: `0.0978855 -> 0.0145547`
- `5.5" Phone Display Quality Loss` MAE: `1.0167156 -> 0.3089123`

Interpretation:

- the acutance-only branch preserves the strongest preset / quality gains from the full anchor branch
- the large phone-preset improvement survives intact
- the remaining miss is concentrated in the Acutance-curve residual rather than the reported MTF bands

## Working Conclusion

This pass narrows the matched-reference family for issue `#29`:

- the strongest reference-anchor signal is useful on the acutance side even when it should not be treated as a reported MTF correction
- the earlier trade-off is therefore not a single shared MTF problem
- the remaining gap is more specifically about how the reference-conditioned branch should shape the Acutance path

What remains:

- the README target is still not reached because the Acutance-curve residual is still materially above the reference-refined branch
- however, this is the first issue-29 branch that cleanly separates reported-MTF behavior from acutance-side gains
- the next useful step should focus on a more faithful acutance-side or perceptual/reference correction family instead of further changing the reported MTF branch
