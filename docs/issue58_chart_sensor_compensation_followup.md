# Issue 58 Chart And Sensor Compensation Follow-up

This note records the bounded chart/sensor compensation refresh for issue `#58`.

## Family

This pass revisits the chart/sensor compensation family from issue `#39` within the newer post-PR-`#57` direct-method context.

The checked-in issue-58 artifacts keep the current static-bin ROI-reference direct-method baseline intact:

- anchored high-frequency PSD calibration
- `roi_source = reference`
- static inferred reference-bin centers
- `frequency_scale = 1.0`
- unchanged matched-ORI, Acutance, and Quality Loss correction stack

That means this refresh is benchmarked against the PR-`#53` / current-static-bin default line, not against the PR-`#55` observable-bin candidate itself. PR `#55` remains in the comparison table because issue `#58` still needs to report whether the refreshed chart/sensor family is better or worse than that earlier observable-bin follow-up.

The only family change is the same source-backed lower-layer chart aperture term that issue `#39` introduced on the older branch:

- `mtf_compensation_mode: sensor_aperture_sinc -> chart_sensor_aperture_sinc`
- `chart_fill_factor: 0.15`

## Source Basis

This remains the same documented family identified in [dead_leaves_black_box_research.md](./dead_leaves_black_box_research.md):

- Imatest documentation decomposes measured MTF into chart, lens, sensor, and processing terms
- the repo already models the sensor aperture term
- this bounded refresh adds one chart-medium aperture term without reopening ROI policy, observable-bin frequency mapping, or empirical `frequency_scale`

## Profiles Compared

Current direct-method baseline used in the issue-58 artifacts, matching the post-PR-`#55` static-bin default line:

- [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_profile.json)

Issue `#58` refreshed chart/sensor candidate:

- [../algo/deadleaf_13b10_imatest_chart_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_profile.json](../algo/deadleaf_13b10_imatest_chart_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_profile.json)

Artifacts:

- [../artifacts/issue58_chart_sensor_compensation_psd_benchmark.json](../artifacts/issue58_chart_sensor_compensation_psd_benchmark.json)
- [../artifacts/issue58_chart_sensor_compensation_acutance_benchmark.json](../artifacts/issue58_chart_sensor_compensation_acutance_benchmark.json)

## Comparison Set

This pass compares against:

- PR `#30` current best merged canonical-target branch
- PR `#40` older-branch chart/sensor compensation result
- PR `#53` ROI-policy follow-up
- PR `#55` observable-bin frequency-mapping follow-up
- PR `#57` empirical `frequency_scale` follow-up

| Path | PSD `curve_mae_mean` | PSD signed-relative residual | `MTF20` | `MTF30` | `MTF50` | Acutance `curve_mae_mean` | `acutance_focus_preset_mae_mean` | `overall_quality_loss_mae_mean` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PR `#30` | `0.04497615` | `0.33019613` | `0.11418549` | `0.07118338` | `0.03341906` | `0.04497615` | `0.03479546` | `2.19874216` |
| PR `#40` | `0.04313186` | `0.08672250` | `0.03317034` | `0.03705447` | `0.00938074` | `0.05521880` | `0.06881027` | `3.37730101` |
| PR `#53` | `0.04231237` | `0.08483351` | `0.02658848` | `0.02903115` | `0.00921053` | `0.03679567` | `0.04130714` | `1.26357125` |
| PR `#55` | `0.04241564` | `0.08641068` | `0.02109366` | `0.02920596` | `0.00942858` | `0.03690674` | `0.04092806` | `1.27229004` |
| PR `#57` | `0.04810412` | `0.14593604` | `0.03158012` | `0.04783065` | `0.02157354` | `0.03666082` | `0.03699264` | `1.45822786` |
| issue `#58` refreshed chart/sensor candidate | `0.04237484` | `0.08462897` | `0.02678218` | `0.02913119` | `0.00922861` | `0.03683881` | `0.04126143` | `1.26266468` |

## Result

Relative to PR `#55`, the refreshed chart/sensor candidate is mixed:

- PSD `curve_mae_mean`: `0.04241564 -> 0.04237484`
- PSD signed-relative residual: `0.08641068 -> 0.08462897`
- `MTF20`: `0.02109366 -> 0.02678218`
- `MTF30`: `0.02920596 -> 0.02913119`
- `MTF50`: `0.00942858 -> 0.00922861`
- Acutance `curve_mae_mean`: `0.03690674 -> 0.03683881`
- `acutance_focus_preset_mae_mean`: `0.04092806 -> 0.04126143`
- `overall_quality_loss_mae_mean`: `1.27229004 -> 1.26266468`

Relative to PR `#53`, the same family is still nearly neutral but not a lower-layer win:

- PSD `curve_mae_mean`: `0.04231237 -> 0.04237484`
- PSD signed-relative residual: `0.08483351 -> 0.08462897`
- `MTF20`: `0.02658848 -> 0.02678218`
- `MTF30`: `0.02903115 -> 0.02913119`
- `MTF50`: `0.00921053 -> 0.00922861`
- Acutance `curve_mae_mean`: `0.03679567 -> 0.03683881`
- `acutance_focus_preset_mae_mean`: `0.04130714 -> 0.04126143`
- `overall_quality_loss_mae_mean`: `1.26357125 -> 1.26266468`

Relative to PR `#40`, the same chart/sensor family is much better on the newer direct-method branch:

- PSD `curve_mae_mean`: `0.04313186 -> 0.04237484`
- PSD signed-relative residual: `0.08672250 -> 0.08462897`
- `MTF20`: `0.03317034 -> 0.02678218`
- `MTF30`: `0.03705447 -> 0.02913119`
- `MTF50`: `0.00938074 -> 0.00922861`
- Acutance `curve_mae_mean`: `0.05521880 -> 0.03683881`
- `acutance_focus_preset_mae_mean`: `0.06881027 -> 0.04126143`
- `overall_quality_loss_mae_mean`: `3.37730101 -> 1.26266468`

Relative to PR `#57`, the refreshed chart/sensor candidate restores the lower-layer and Quality Loss behavior that the empirical `frequency_scale` candidate lost:

- PSD `curve_mae_mean`: `0.04810412 -> 0.04237484`
- PSD signed-relative residual: `0.14593604 -> 0.08462897`
- `MTF20`: `0.03158012 -> 0.02678218`
- `MTF30`: `0.04783065 -> 0.02913119`
- `MTF50`: `0.02157354 -> 0.00922861`
- Acutance `curve_mae_mean`: `0.03666082 -> 0.03683881`
- `acutance_focus_preset_mae_mean`: `0.03699264 -> 0.04126143`
- `overall_quality_loss_mae_mean`: `1.45822786 -> 1.26266468`

Relative to PR `#30`, the refreshed candidate is still far better on lower-layer residuals and downstream Quality Loss, but it still does not beat the older focus-preset Acutance aggregate:

- PSD `curve_mae_mean`: `0.04497615 -> 0.04237484`
- PSD signed-relative residual: `0.33019613 -> 0.08462897`
- `MTF20`: `0.11418549 -> 0.02678218`
- `MTF30`: `0.07118338 -> 0.02913119`
- `MTF50`: `0.03341906 -> 0.00922861`
- Acutance `curve_mae_mean`: `0.04497615 -> 0.03683881`
- `acutance_focus_preset_mae_mean`: `0.03479546 -> 0.04126143`
- `overall_quality_loss_mae_mean`: `2.19874216 -> 1.26266468`

## Conclusion

This is another bounded mixed result, not a new default direct-method path.

The newer direct-method branch does make the old chart/sensor compensation family look meaningfully healthier than it did in PR `#40`: the refreshed candidate materially improves the older chart/sensor result and slightly improves several PSD and Quality Loss metrics relative to PR `#55`. But the actual checked-in baseline for this issue is the static-bin ROI-reference line, and against that stricter PR-`#53` / current-default baseline it still fails the lower-layer gate because the primary PSD curve is slightly worse and `MTF20` regresses.

That means the updated chart-medium aperture term is no longer the clearly negative family it looked like in issue `#39`, but it is still not strong enough to replace the current direct-method baseline. The result is useful because it narrows the remaining gap further: later ROI and frequency-mapping refinements made this family less harmful, yet one fixed chart-aperture factor still does not produce a clean lower-layer win on the current dataset.

## Validation

- `python3 -m algo.benchmark_parity_psd_mtf 20260318_deadleaf_13b10 algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_profile.json algo/deadleaf_13b10_imatest_chart_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_profile.json --output artifacts/issue58_chart_sensor_compensation_psd_benchmark.json`
- `python3 -m algo.benchmark_parity_acutance_quality_loss 20260318_deadleaf_13b10 algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_profile.json algo/deadleaf_13b10_imatest_chart_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_profile.json --output artifacts/issue58_chart_sensor_compensation_acutance_benchmark.json`
- `python3 -m pytest tests/test_dead_leaves_mtf_compensation.py tests/test_benchmark_parity_psd_mtf.py tests/test_benchmark_parity_acutance_quality_loss.py`
