# Intrinsic Phase-Retained Reported-MTF Disconnect Follow-up

Issue `#97` implements the bounded slice selected in issue `#95` / PR `#96`: keep the issue-93 downstream-only matched-ori Quality Loss branch, but disconnect reported-MTF thresholds from the intrinsic reconnect path.

## Scope

- New intrinsic scope: `reported_mtf_disconnect_quality_loss_isolation_downstream_matched_ori_only`
- Basis profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_readout_reconnect_quality_loss_isolation_downstream_matched_ori_only_profile.json`
- Candidate profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_quality_loss_isolation_downstream_matched_ori_only_profile.json`
- Difference from issue `#93`: the main acutance branch and downstream Quality Loss branch stay on the issue-93 topology, but reported-MTF threshold extraction returns to the observed calibrated/compensated branch.

## Result

Current PR `#30` branch:

- `curve_mae_mean = 0.03679`
- `focus_preset_acutance_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22150`
- `mtf20 = 0.03301`
- `mtf_abs_signed_rel_mean = 0.08671`

Issue `#93` baseline:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 3.94743`
- `mtf20 = 0.08577`
- `mtf_abs_signed_rel_mean = 0.13994`

Issue `#97` reported-MTF disconnect candidate:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 3.94743`
- `mtf20 = 0.07448`
- `mtf_abs_signed_rel_mean = 0.37688`

## Comparison

- Versus issue `#93`, `curve_mae_mean` changes by `+0.00000` and `focus_preset_acutance_mae_mean` changes by `+0.00000`.
- Versus issue `#93`, `overall_quality_loss_mae_mean` changes by `+0.00000`.
- Versus issue `#93`, `mtf20` changes by `-0.01129` and `mtf_abs_signed_rel_mean` changes by `+0.23694`.
- Versus PR `#30`, `overall_quality_loss_mae_mean` changes by `+2.72593` and `mtf_abs_signed_rel_mean` changes by `+0.29016`.

## Acceptance

- `curve_mae_mean` no worse than issue `#93`: `True`
- `focus_preset_acutance_mae_mean` no worse than issue `#93`: `True`
- `overall_quality_loss_mae_mean` no worse than issue `#93`: `True`
- `mtf20` improves versus issue `#93`: `True`
- `mtf_abs_signed_rel_mean` improves versus issue `#93`: `False`
- All issue-97 gates pass: `False`

## Conclusion

- Status: `issue97_reported_mtf_disconnect_failed`
- Summary: Disconnecting reported-MTF thresholds from the intrinsic reconnect did not improve the readout metrics enough while preserving the issue-93 acutance and Quality Loss record, so this bounded slice closes as a negative or mixed result.
- Next step: Keep the result as the canonical issue-97 record and split the next bounded follow-up from the remaining failure mode.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`
- Fitted outputs for this issue stay under `algo/` and `artifacts/` only.
- No release-facing config is promoted in this issue.
