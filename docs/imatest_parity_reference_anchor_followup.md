# Imatest Parity Matched-ORI Reference Anchor Follow-up

This note records the fifth issue `#29` follow-up pass.

It builds on the current best branch from
[imatest_parity_reference_refined_followup.md](./imatest_parity_reference_refined_followup.md):

- `toe_power` linearization proxy
- `sensor_aperture_sinc` compensation
- bounded `reference_refined` ROI placement

Motivation:

- the current best issue-29 branch still leaves preset Acutance MAE above the literal observable-parity baseline
- the repo research notes still leave room for a more faithful intrinsic / reference family instead of only changing the forward analysis path
- the dataset already contains matched `ori` captures for the same gain / exposure / scene keys

This pass therefore adds a benchmark-side matched-reference anchor:

- map each processed sample to the matched `OV13B10_AI_NR_OV13B10_ori` capture by capture key
- run the same analysis profile on that matched `ori` sample
- derive a bounded multiplicative correction curve from matched-reference MTF over estimated MTF
- apply that correction back onto the processed-sample estimate

The anchor is intentionally bounded rather than unconstrained:

- `matched_ori_reference_anchor = true`
- `matched_ori_correction_clip_lo = 0.5`
- `matched_ori_correction_clip_hi = 2.0`

That keeps this pass focused on testing whether a reference-anchored family helps close the README target, without claiming a fully solved intrinsic model.

## Profiles Compared

Benchmark artifacts:

- [../artifacts/imatest_parity_reference_anchor_psd_benchmark.json](../artifacts/imatest_parity_reference_anchor_psd_benchmark.json)
- [../artifacts/imatest_parity_reference_anchor_benchmark.json](../artifacts/imatest_parity_reference_anchor_benchmark.json)

Profiles:

1. current best toe-plus-sensor plus reference-refined branch
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_refined_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_refined_profile.json)
2. toe-plus-sensor plus reference-refined ROI and matched-ORI anchor
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_profile.json)

## PSD / MTF Result

Compared with the current best reference-refined branch:

- `curve_mae_mean`: `0.0379513 -> 0.0426246`
- mean absolute band signed-rel error: `0.0869296 -> 0.0860890`
- `high signed-rel mean`: `0.04964 -> 0.02006`
- `top signed-rel mean`: `-0.16463 -> -0.12883`

Interpretation:

- this anchor branch makes the overall curve residual worse, so it is not a clean replacement for the current best branch
- however, the signed-rel band errors improve, especially in the high and top bands
- that pattern suggests the matched-reference anchor is directionally useful but currently too strong for full-curve fidelity

## Acutance / Quality Loss Result

Compared with the current best reference-refined branch:

- `curve_mae_mean`: `0.0379513 -> 0.0438585`
- `acutance_focus_preset_mae_mean`: `0.0680820 -> 0.0505124`
- `overall_quality_loss_mae_mean`: `3.0020871 -> 2.7788753`

Interpretation:

- this is the first issue-29 branch to materially improve preset Acutance and overall Quality Loss together by a larger margin after the earlier small registration gains
- the gains are large enough to keep the matched-reference family alive as a serious candidate
- but the branch still loses too much curve fidelity to count as the new best overall parity branch

## Working Conclusion

This pass narrows the intrinsic / reference family for issue `#29`:

- a bounded matched-ORI anchor is promising for preset Acutance and overall Quality Loss
- the current implementation is still too aggressive on full-curve fidelity
- the family should be constrained or shaped further, not discarded

What remains:

- the README target is still not reached
- the best overall issue-29 branch is still the earlier toe-plus-sensor plus reference-refined path if curve fidelity is weighted highest
- the next useful step is to keep the matched-reference family and narrow it so the preset gains survive without giving back the curve
