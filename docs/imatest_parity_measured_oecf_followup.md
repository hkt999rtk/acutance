# Imatest Parity Measured OECF Follow-up

This note records the bounded measured-OECF family follow-up for issue `#77`.

It builds on the family-selection result in issue `#71` / PR `#76`, which named `literal/measured_oecf_on_sensor_comp` as the next source-backed literal route.

## Source Basis

- Imatest gamma/OECF guidance still points to measured linearization as a missing family.
- The earlier toe branch is only an engineering OECF stand-in, not a separate measured family record.
- The repo already contains one source-backed matched-ORI quantile-transfer proxy from the earlier OECF audit, so issue `#77` reuses that same measured transfer formulation instead of reopening generic retunes.

## Family Boundary Change

- Toe-proxy baseline: `algo/deadleaf_13b10_imatest_sensor_comp_toe_profile.json`
- Measured-OECF candidate: `algo/deadleaf_13b10_imatest_sensor_comp_toe_measured_oecf_profile.json`
- Change: Keep the literal sensor-compensation plus toe linearization route intact, then add the matched-ORI quantile transfer as the smallest measured-OECF-driven family boundary that the current repo can derive without chart-patch OECF data.
- Artifact boundary note: The new candidate is still a fitted artifact rather than a golden/reference asset. It isolates the measured-OECF family boundary from the earlier toe-only stand-in.

## Profiles Compared

- current best branch from PR `#30`: `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_profile.json`
- literal toe-proxy baseline from issue `#71`: `algo/deadleaf_13b10_imatest_sensor_comp_toe_profile.json`
- issue `#77` measured-OECF candidate: `algo/deadleaf_13b10_imatest_sensor_comp_toe_measured_oecf_profile.json`
- inverse `sRGB` control: `algo/deadleaf_13b10_imatest_sensor_comp_srgb_profile.json`
- inverse `Rec.709` control: `algo/deadleaf_13b10_imatest_sensor_comp_rec709_profile.json`

Artifacts:

- `artifacts/issue77_measured_oecf_psd_benchmark.json`
- `artifacts/issue77_measured_oecf_acutance_benchmark.json`
- `artifacts/imatest_parity_measured_oecf_benchmark.json`

## Readout

| Profile | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 |
| --- | --- | --- | --- | --- | --- | --- |
| current_best_pr30_branch | 0.03679 | 0.04249 | 1.22150 | 0.03301 | 0.03694 | 0.00933 |
| literal_toe_proxy_baseline | 0.03812 | 0.06823 | 3.01158 | 0.02669 | 0.03691 | 0.00937 |
| measured_oecf_candidate | 0.03779 | 0.06827 | 3.02431 | 0.02674 | 0.03690 | 0.00936 |
| inverse_srgb_control | 0.09127 | 0.09695 | 4.38993 | 0.04616 | 0.05683 | 0.03328 |
| inverse_rec709_control | 0.08788 | 0.09381 | 4.26083 | 0.04430 | 0.05365 | 0.03188 |

## Measured OECF Versus Toe Proxy

- `curve_mae_mean`: `0.03812 -> 0.03779` (-0.00033)
- focus-preset Acutance MAE mean: `0.06823 -> 0.06827` (+0.00004)
- `overall_quality_loss_mae_mean`: `3.01158 -> 3.02431` (+0.01273)
- `MTF20` MAE: `0.02669 -> 0.02674` (+0.00006)
- `MTF30` MAE: `0.03691 -> 0.03690` (-0.00002)
- `MTF50` MAE: `0.00937 -> 0.00936` (-0.00001)

## Measured OECF Versus PR #30 Current Best

- `curve_mae_mean`: `0.03679 -> 0.03779` (+0.00100)
- focus-preset Acutance MAE mean: `0.04249 -> 0.06827` (+0.02578)
- `overall_quality_loss_mae_mean`: `1.22150 -> 3.02431` (+1.80281)

## Controls

- The measured-OECF candidate is benchmarked against the checked-in source-backed inverse-OETF controls rather than against a new free-form retune.
- Against `sRGB`: curve `0.09127`, focus Acutance `0.09695`, overall QL `4.38993`.
- Against `Rec.709`: curve `0.08788`, focus Acutance `0.09381`, overall QL `4.26083`.

## Storage Separation

- Golden/reference roots:
  - `20260318_deadleaf_13b10`
  - `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`
- New fitted artifacts:
  - `algo/deadleaf_13b10_imatest_sensor_comp_toe_measured_oecf_profile.json`
  - `artifacts/issue77_measured_oecf_psd_benchmark.json`
  - `artifacts/issue77_measured_oecf_acutance_benchmark.json`
  - `artifacts/imatest_parity_measured_oecf_benchmark.json`
- Rules:
  - Do not write fitted profiles, calibrations, or benchmark outputs under the golden/reference roots.
  - Keep issue-77 fitted artifacts under algo/ and artifacts/ only.
  - Do not promote a release-facing config until the measured-OECF family beats the current toe stand-in on the tracked guards.

## Working Conclusion

- The measured-OECF candidate does not beat the toe stand-in on the tracked primary guards, so this issue closes as a bounded measured-OECF record rather than as a new default path.
- Next step: Keep the issue as a bounded measured-OECF record only; the repo still lacks evidence that this family beats the toe stand-in.
