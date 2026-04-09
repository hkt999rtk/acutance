# Imatest Parity Mid-Dip Acutance-Only Reference Anchor Follow-up

This note records the tenth issue `#29` follow-up pass.

It builds on the earlier acutance-only branches from:

- [imatest_parity_reference_anchor_acutance_only_followup.md](./imatest_parity_reference_anchor_acutance_only_followup.md)
- [imatest_parity_reference_anchor_acutance_only_strength_followup.md](./imatest_parity_reference_anchor_acutance_only_strength_followup.md)

Motivation:

- the tuned `0.85` acutance-only branch is the current best checked-in compromise
- the remaining miss is still concentrated in the Acutance-curve residual
- the negative piecewise low/high result suggests the useful shape is not a crude two-band split, but it may still be frequency-dependent within the acutance-only family

This pass therefore adds a more flexible acutance-side strength curve:

- `matched_ori_anchor_mode = acutance_only`
- `matched_ori_strength_curve_frequencies = [0.0, 0.12, 0.22, 0.35, 0.5]`
- `matched_ori_strength_curve_values = [1.0, 1.0, 0.82, 0.95, 1.0]`

That keeps full correction at the low and highest ends, dips through the mid band, and lets the correction recover again by the upper frequencies instead of using a single scalar or a simple low/high split.

## Profiles Compared

Benchmark artifacts:

- [../artifacts/imatest_parity_reference_anchor_acutance_only_mid_dip_psd_benchmark.json](../artifacts/imatest_parity_reference_anchor_acutance_only_mid_dip_psd_benchmark.json)
- [../artifacts/imatest_parity_reference_anchor_acutance_only_mid_dip_benchmark.json](../artifacts/imatest_parity_reference_anchor_acutance_only_mid_dip_benchmark.json)

Profiles:

1. full-strength acutance-only matched-reference anchor
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_profile.json)
2. tuned `0.85` acutance-only matched-reference anchor
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_strength085_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_strength085_profile.json)
3. mid-dip acutance-only matched-reference anchor
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_mid_dip_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_mid_dip_profile.json)

## PSD / MTF Result

Compared with the tuned `0.85` branch:

- `curve_mae_mean`: `0.0423558 -> 0.0430644`
- mean absolute band signed-rel error: unchanged at `0.0869296`
- `high signed-rel mean`: unchanged at `0.04964`
- `top signed-rel mean`: unchanged at `-0.16463`

Compared with the full-strength acutance-only branch:

- `curve_mae_mean`: `0.0438585 -> 0.0430644`

Interpretation:

- the reported MTF residual bands remain fixed, as expected for the acutance-only family
- relative to the current `0.85` compromise, the mid-dip branch gives back a small amount of Acutance-curve fit
- but it is still meaningfully better than the earlier full-strength branch on the curve side

## Acutance / Quality Loss Result

Compared with the tuned `0.85` branch:

- `acutance_focus_preset_mae_mean`: `0.0526345 -> 0.0494745`
- `overall_quality_loss_mae_mean`: `2.8110723 -> 2.7318693`
- `5.5" Phone Display Acutance` MAE: `0.0257482 -> 0.0144692`
- `5.5" Phone Display Quality Loss` MAE: `0.4688160 -> 0.3077102`

Compared with the full-strength acutance-only branch:

- `curve_mae_mean`: `0.0438585 -> 0.0430644`
- `acutance_focus_preset_mae_mean`: `0.0505124 -> 0.0494745`
- `overall_quality_loss_mae_mean`: `2.7788753 -> 2.7318693`
- `5.5" Phone Display Acutance` MAE: `0.0145547 -> 0.0144692`
- `5.5" Phone Display Quality Loss` MAE: `0.3089123 -> 0.3077102`

Interpretation:

- this is the first structured acutance-side shaping method that beats both earlier acutance-only variants on the preset / quality side
- it also improves over the earlier full-strength branch on the Acutance-curve side, while keeping the reported-MTF side fixed
- the phone preset gains not only survive, they become slightly stronger than before

## Working Conclusion

This pass becomes the new best compromise inside the acutance-only reference-conditioned family for issue `#29`:

- it improves over the full-strength branch on curve, preset Acutance, and overall Quality Loss at the same time
- it improves over the tuned `0.85` scalar branch on preset Acutance and overall Quality Loss while preserving the fixed reported-MTF branch
- the first clearly useful structured shape is therefore a mid-band dip, not a simple global retune or a naive low/high split

What remains:

- the README target is still not reached because the Acutance-curve residual is still above the current best reference-refined branch (`0.0430644` vs `0.0379513`)
- however, the remaining gap is now narrower and better isolated within the acutance-side reference/perceptual family
- the next useful step should keep the reported-MTF branch fixed and continue refining this structured acutance-side family rather than returning to generic global strength tuning
