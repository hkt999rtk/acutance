# Issue 61 ISP Family Follow-up

This note records the bounded scene-/process-dependent ISP follow-up for issue `#61`.

## Family

This pass reuses the same measured high-frequency-noise-share ISP proxy from issue `#48`, but refreshes it on the newer direct-method baseline instead of the older intrinsic branch.

The checked-in issue-61 candidate keeps the current static-bin ROI-reference direct-method baseline intact:

- anchored high-frequency PSD calibration
- `roi_source = reference`
- static inferred reference-bin centers
- `frequency_scale = 1.0`
- sensor-only MTF compensation
- unchanged matched-ORI, Acutance, and Quality Loss correction stack

The only family change is one post-MTF scene-/process-dependent shape gate driven by the measured per-capture high-frequency noise share:

- `mtf_shape_correction_mode: none -> hf_noise_share_gated_bump`
- `gain = 0.035`
- `share_gate_lo / hi = 0.05 / 0.08`
- the same mid-band boost / high-band attenuation shape from issue `#48`

## Source Basis

This remains inside the source-backed ISP family identified in [dead_leaves_black_box_research.md](./dead_leaves_black_box_research.md):

- scene-/process-dependent ISP state remains a high-priority missing family
- denoising / sharpening can change texture measurements differently from edge response
- the repo already exposes measured `high_frequency_noise_share` from processed dead-leaves captures

So this pass tests the narrowest already-implemented proxy that is still tied to current processed-image evidence, without reopening ROI policy, frequency mapping, or chart/sensor compensation.

## Profiles Compared

Current direct-method baseline:

- [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_profile.json)

Issue `#61` ISP proxy candidate:

- [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_hf_noise_share_shape_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_hf_noise_share_shape_profile.json)

Artifacts:

- [../artifacts/issue61_isp_family_psd_benchmark.json](../artifacts/issue61_isp_family_psd_benchmark.json)
- [../artifacts/issue61_isp_family_acutance_benchmark.json](../artifacts/issue61_isp_family_acutance_benchmark.json)

## Comparison Set

This pass compares against:

- PR `#30` current best merged canonical-target branch
- PR `#49` older intrinsic-branch ISP proxy result
- PR `#57` empirical `frequency_scale` follow-up
- PR `#59` refreshed chart/sensor compensation result

| Path | PSD `curve_mae_mean` | PSD signed-relative residual | `MTF20` | `MTF30` | `MTF50` | Acutance `curve_mae_mean` | `acutance_focus_preset_mae_mean` | `overall_quality_loss_mae_mean` | `5.5\" Phone Display Acutance` | `5.5\" Phone Display Quality Loss` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PR `#30` | `0.04497615` | `0.33019613` | `0.11418549` | `0.07118338` | `0.03341906` | `0.04497615` | `0.03479546` | `2.19874216` | `0.01380215` | `0.14297763` |
| PR `#49` | `0.03280181` | `0.13993779` | `0.08576635` | `0.01789155` | `0.00719609` | `0.03283991` | `0.02890324` | `14.47328913` | `0.03513954` | `60.68418298` |
| PR `#57` | `0.04810412` | `0.14593604` | `0.03158012` | `0.04783065` | `0.02157354` | `0.03666082` | `0.03699264` | `1.45822786` | `0.01681051` | `0.20232388` |
| PR `#59` | `0.04237484` | `0.08462897` | `0.02678218` | `0.02913119` | `0.00922861` | `0.03683881` | `0.04126143` | `1.26266468` | `0.01290495` | `0.16998827` |
| issue `#61` direct-method ISP proxy candidate | `0.04231237` | `0.08483351` | `0.02658848` | `0.02903115` | `0.00921053` | `0.03710696` | `0.04159317` | `1.26114947` | `0.01288791` | `0.16715568` |

## Result

Relative to the current direct-method baseline, this ISP proxy is effectively a downstream-only tweak:

- PSD `curve_mae_mean`: unchanged at `0.04231237`
- PSD signed-relative residual: unchanged at `0.08483351`
- `MTF20 / MTF30 / MTF50`: unchanged at `0.02658848 / 0.02903115 / 0.00921053`
- Acutance `curve_mae_mean`: `0.03679567 -> 0.03710696`
- `acutance_focus_preset_mae_mean`: `0.04130714 -> 0.04159317`
- `overall_quality_loss_mae_mean`: `1.26357125 -> 1.26114947`
- `5.5" Phone Display Acutance`: `0.01290994 -> 0.01288791`
- `5.5" Phone Display Quality Loss`: `0.16991880 -> 0.16715568`

Relative to PR `#59`, the same pattern holds:

- PSD `curve_mae_mean`: `0.04237484 -> 0.04231237`
- PSD signed-relative residual: `0.08462897 -> 0.08483351`
- `MTF20`: `0.02678218 -> 0.02658848`
- `MTF30`: `0.02913119 -> 0.02903115`
- `MTF50`: `0.00922861 -> 0.00921053`
- Acutance `curve_mae_mean`: `0.03683881 -> 0.03710696`
- `acutance_focus_preset_mae_mean`: `0.04126143 -> 0.04159317`
- `overall_quality_loss_mae_mean`: `1.26266468 -> 1.26114947`
- `5.5" Phone Display Acutance`: `0.01290495 -> 0.01288791`
- `5.5" Phone Display Quality Loss`: `0.16998827 -> 0.16715568`

Relative to PR `#57`, the issue-61 candidate keeps the current direct-method lower-layer recovery and slightly reduces the phone-dominated downstream error:

- PSD `curve_mae_mean`: `0.04810412 -> 0.04231237`
- PSD signed-relative residual: `0.14593604 -> 0.08483351`
- `MTF20`: `0.03158012 -> 0.02658848`
- `MTF30`: `0.04783065 -> 0.02903115`
- `MTF50`: `0.02157354 -> 0.00921053`
- Acutance `curve_mae_mean`: `0.03666082 -> 0.03710696`
- `acutance_focus_preset_mae_mean`: `0.03699264 -> 0.04159317`
- `overall_quality_loss_mae_mean`: `1.45822786 -> 1.26114947`
- `5.5" Phone Display Acutance`: `0.01681051 -> 0.01288791`
- `5.5" Phone Display Quality Loss`: `0.20232388 -> 0.16715568`

Relative to PR `#49`, the newer direct-method branch dominates the older intrinsic ISP proxy on downstream failure even though the intrinsic branch still wins headline curve and focus-preset Acutance:

- PSD `curve_mae_mean`: `0.03280181 -> 0.04231237`
- PSD signed-relative residual: `0.13993779 -> 0.08483351`
- `MTF20`: `0.08576635 -> 0.02658848`
- `MTF30`: `0.01789155 -> 0.02903115`
- `MTF50`: `0.00719609 -> 0.00921053`
- Acutance `curve_mae_mean`: `0.03283991 -> 0.03710696`
- `acutance_focus_preset_mae_mean`: `0.02890324 -> 0.04159317`
- `overall_quality_loss_mae_mean`: `14.47328913 -> 1.26114947`
- `5.5" Phone Display Acutance`: `0.03513954 -> 0.01288791`
- `5.5" Phone Display Quality Loss`: `60.68418298 -> 0.16715568`

Relative to PR `#30`, the issue-61 candidate still does not beat the older focus-preset Acutance aggregate or the phone Quality Loss baseline:

- PSD `curve_mae_mean`: `0.04497615 -> 0.04231237`
- PSD signed-relative residual: `0.33019613 -> 0.08483351`
- `MTF20`: `0.11418549 -> 0.02658848`
- `MTF30`: `0.07118338 -> 0.02903115`
- `MTF50`: `0.03341906 -> 0.00921053`
- Acutance `curve_mae_mean`: `0.04497615 -> 0.03710696`
- `acutance_focus_preset_mae_mean`: `0.03479546 -> 0.04159317`
- `overall_quality_loss_mae_mean`: `2.19874216 -> 1.26114947`
- `5.5" Phone Display Acutance`: `0.01380215 -> 0.01288791`
- `5.5" Phone Display Quality Loss`: `0.14297763 -> 0.16715568`

## Conclusion

This is another bounded mixed result, not a new default direct-method path.

Refreshing the old `hf_noise_share_gated_bump` ISP proxy on the current direct-method baseline does exactly what the smaller direct-method hypothesis suggested: it leaves the PSD / MTF path unchanged in practice, slightly improves overall Quality Loss and the phone-preset downstream error, but slightly regresses the Acutance curve and focus-preset aggregate. That is useful as a source-backed negative because it says the remaining downstream gap is not solved by a small noise-share-gated shape tweak alone on the current direct-method line.

The family is still healthier on the newer direct-method branch than it was on the older intrinsic branch because the direct-method path avoids the catastrophic phone Quality Loss failure from PR `#49`. But the effect size of this ISP proxy is too small and too mixed to justify promoting it as the next default path.

## Validation

- `python3 -m algo.benchmark_parity_psd_mtf 20260318_deadleaf_13b10 algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_profile.json algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_hf_noise_share_shape_profile.json --output artifacts/issue61_isp_family_psd_benchmark.json`
- `python3 -m algo.benchmark_parity_acutance_quality_loss 20260318_deadleaf_13b10 algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_profile.json algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_hf_noise_share_shape_profile.json --output artifacts/issue61_isp_family_acutance_benchmark.json`
- `python3 -m pytest tests/test_benchmark_parity_psd_mtf.py tests/test_benchmark_parity_acutance_quality_loss.py`
