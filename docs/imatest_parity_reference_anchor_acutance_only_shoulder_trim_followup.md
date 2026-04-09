# Imatest Parity Shoulder-Trim Acutance-Only Follow-up

This note records the eleventh issue `#29` follow-up pass.

It builds directly on the current best mid-dip acutance-only branch from
[imatest_parity_reference_anchor_acutance_only_mid_dip_followup.md](./imatest_parity_reference_anchor_acutance_only_mid_dip_followup.md).

Motivation:

- the mid-dip branch is the current best compromise inside the acutance-only reference-conditioned family
- the remaining miss is still the Acutance-curve residual
- the largest curve loss versus the reference-refined branch is still concentrated toward the lower mixup conditions

This pass therefore tests a narrow local hypothesis instead of opening another broad retune:

- keep the current mid-dip family
- trim the low-frequency shoulder slightly below `1.0`
- test whether that low-end trim can recover the remaining curve loss without discarding the preset / Quality Loss gains

## Search Artifact

Tracked search report:

- [../artifacts/imatest_parity_reference_anchor_acutance_only_shoulder_trim_search.json](../artifacts/imatest_parity_reference_anchor_acutance_only_shoulder_trim_search.json)

Baseline:

- [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_mid_dip_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_mid_dip_profile.json)

The search report records the current mid-dip baseline and three nearby shoulder-trim candidates:

1. `[0.92, 0.92, 0.82, 0.95, 1.0]`
2. `[0.96, 0.96, 0.80, 0.98, 1.0]`
3. `[0.98, 0.98, 0.80, 0.98, 1.0]`

These are the acutance-side strength-curve values evaluated over the same knot set:

- `[0.0, 0.12, 0.22, 0.35, 0.5]`

## Result

Current mid-dip baseline:

- `curve_mae_mean = 0.0430644`
- `acutance_focus_preset_mae_mean = 0.0494745`
- `overall_quality_loss_mae_mean = 2.7318693`
- `5.5" Phone Display Acutance` MAE `= 0.0144692`
- `5.5" Phone Display Quality Loss` MAE `= 0.3077102`

Best shoulder-trim candidate from the local search:

- strength curve values: `[0.98, 0.98, 0.80, 0.98, 1.0]`
- `curve_mae_mean = 0.0431195`
- `acutance_focus_preset_mae_mean = 0.0497691`
- `overall_quality_loss_mae_mean = 2.7395229`
- `5.5" Phone Display Acutance` MAE `= 0.0156296`
- `5.5" Phone Display Quality Loss` MAE `= 0.3238337`

Interpretation:

- the local shoulder-trim neighborhood does not beat the current mid-dip branch
- even the best nearby candidate is slightly worse on all tracked summary metrics
- that means the current mid-dip branch is not just a better preset / Quality Loss point; it is also the local best compromise in this specific acutance-only shaping neighborhood

## Working Conclusion

This pass narrows the remaining issue-29 work again:

- the current mid-dip branch remains the best checked-in compromise inside the acutance-only strength-curve family
- bounded low-shoulder trims around that branch are a negative result
- the remaining README target gap is therefore unlikely to close through another nearby shoulder retune alone

What remains:

- the canonical target is still open because the Acutance-curve residual remains above the reference-refined branch
- the next useful step should move to a different acutance-side reference / perceptual model family instead of continuing the same local strength-curve neighborhood
