# Intrinsic Phase-Retained Matched-Ori Graft Follow-up

Issue `#89` implements the bounded slice selected in issue `#87` / PR `#88`: graft PR30's matched-ori downstream correction / acutance-anchor family onto the issue-85 split topology.

## Scope

- New intrinsic scope: `readout_reconnect_quality_loss_isolation_matched_ori_graft`
- Basis profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_readout_reconnect_quality_loss_isolation_profile.json`
- Candidate profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_readout_reconnect_quality_loss_isolation_matched_ori_graft_profile.json`
- Difference from `readout_reconnect_quality_loss_isolation`: the main intrinsic curve/acutance path stays untouched, while the readout path and isolated downstream Quality Loss branch receive the bounded matched-ori graft.

## Result

Current PR `#30` branch:

- `curve_mae_mean = 0.03679`
- `focus_preset_acutance_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22150`
- `mtf_abs_signed_rel_mean = 0.08671`

Issue `#85` readout-reconnected baseline:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 8.02054`
- `mtf_abs_signed_rel_mean = 0.13994`

Issue `#89` matched-ori graft candidate:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 3.94743`
- `mtf_abs_signed_rel_mean = 0.74771`

## Comparison

- Versus issue `#85`, `curve_mae_mean` changes by `+0.00000` and `focus_preset_acutance_mae_mean` changes by `+0.00000`.
- Versus issue `#85`, `overall_quality_loss_mae_mean` changes by `-4.07311`.
- Versus issue `#85`, `mtf_abs_signed_rel_mean` changes by `+0.60778`.
- Thresholds closer to PR `#30` than issue `#85`: `mtf20=False`, `mtf30=False`, `mtf50=False`.

## Acceptance

- `curve_mae_mean` no worse than issue `#85`: `True`
- `focus_preset_acutance_mae_mean` no worse than issue `#85`: `True`
- `overall_quality_loss_mae_mean` improves versus issue `#85`: `True`
- `mtf20` closer to PR `#30` than issue `#85`: `False`
- `mtf_abs_signed_rel_mean` preserves issue-85 distance to PR `#30`: `False`
- All issue-89 gates pass: `False`

## Conclusion

- Status: `issue89_quality_loss_improved_but_readout_regressed`
- Summary: The bounded graft preserves issue #85's curve and focus-preset Acutance gains exactly and materially improves overall Quality Loss, but it dramatically over-corrects the reported-MTF/readout path. `mtf20`, `mtf30`, `mtf50`, and `mtf_abs_signed_rel_mean` all regress sharply versus issue #85, so the slice is not promotable.
- Next step: Keep this branch as the canonical issue-89 implementation record and hand the residual readout-vs-quality-loss tradeoff back to PM for the next bounded split.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`
- Fitted outputs for this issue stay under `algo/` and `artifacts/` only.
- No release-facing config is promoted in this issue.
