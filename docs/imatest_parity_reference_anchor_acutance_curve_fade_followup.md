# Imatest Parity Acutance-Curve Fade Follow-up

This note records the thirteenth issue `#29` follow-up pass.

It builds directly on the new direct acutance-curve anchor branch from
[imatest_parity_reference_anchor_acutance_curve_followup.md](./imatest_parity_reference_anchor_acutance_curve_followup.md).

Motivation:

- the direct acutance-domain anchor became the strongest branch so far for the remaining canonical curve gap
- its remaining regression is concentrated in the phone preset
- the most concrete next hypothesis was that the phone regression comes from extrapolating the observable curve anchor beyond the measured curve range

This pass therefore tests a bounded fade-out:

- keep the direct acutance-domain anchor family
- fade the correction down between the observable curve endpoint and the phone-preset relative viewing scale
- leave the reported-MTF branch unchanged

## Search Artifact

Tracked search report:

- [../artifacts/imatest_parity_reference_anchor_acutance_curve_fade_search.json](../artifacts/imatest_parity_reference_anchor_acutance_curve_fade_search.json)

Baseline:

- [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_anchor_profile.json)

The search report records the current direct acutance-domain anchor baseline and three fade variants:

1. `blend_start_relative_scale = 2.0`, `blend_stop_relative_scale = 5.8`
2. `blend_start_relative_scale = 2.3`, `blend_stop_relative_scale = 5.8`
3. `blend_start_relative_scale = 2.5`, `blend_stop_relative_scale = 5.8`

## Result

Current direct acutance-domain anchor baseline:

- `curve_mae_mean = 0.0384938`
- `acutance_focus_preset_mae_mean = 0.0459659`
- `overall_quality_loss_mae_mean = 2.4157875`
- `5.5" Phone Display Acutance` MAE `= 0.0292175`
- `5.5" Phone Display Quality Loss` MAE `= 0.5717982`

Best fade candidate from the local search:

- `blend_start_relative_scale = 2.0`
- `blend_stop_relative_scale = 5.8`
- `curve_mae_mean = 0.0428655`
- `acutance_focus_preset_mae_mean = 0.0517633`
- `overall_quality_loss_mae_mean = 2.7560535`
- `5.5" Phone Display Acutance` MAE `= 0.0291079`
- `5.5" Phone Display Quality Loss` MAE `= 0.5696302`

Interpretation:

- the fade-out idea barely changes the phone term
- but it gives back too much of the new curve and overall Quality Loss gain
- that means the phone regression is not mainly explained by flat extrapolation beyond the observable curve endpoint

## Working Conclusion

This pass narrows the new acutance-domain family again:

- the direct acutance-domain anchor remains the best checked-in branch in this family
- bounded fade-outs above the observable curve range are a negative result
- the next useful step should keep the direct acutance-domain anchor family, but make it more preset-conditioned or phone-aware instead of only tapering the correction above the observable range
