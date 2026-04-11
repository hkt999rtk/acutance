# Issue 29 Anchored High-Frequency Ideal-PSD Follow-up

This note records one bounded lower-layer follow-up under issue `#29` after the negative chart-plus-sensor compensation result in issue `#39`.

The family tested here stays on the same direct-method parity branch as PR `#30`, but changes the chart / reference PSD prior instead of the aperture compensation family.

## Source Basis

This follows the chart-prior direction already documented in [dead_leaves_black_box_research.md](./dead_leaves_black_box_research.md):

- Imatest's Random / Dead Leaves method depends on an assumed chart / reference PSD prior
- the repo already models this with a calibrated empirical ideal PSD
- `anchored_high_frequency` keeps the current low-frequency quadratic fit intact and only adds a constrained residual above a split frequency

That makes this a bounded lower-layer family instead of another downstream Acutance or Quality-Loss remap.

## Profiles Compared

Baseline, representing the current PR `#30` best branch:

- [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_profile.json)

Anchored high-frequency candidate from this follow-up:

- [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_profile.json)

Artifacts:

- [../artifacts/issue29_anchored_high_frequency_psd_benchmark.json](../artifacts/issue29_anchored_high_frequency_psd_benchmark.json)
- [../artifacts/issue29_anchored_high_frequency_acutance_benchmark.json](../artifacts/issue29_anchored_high_frequency_acutance_benchmark.json)

The candidate keeps the current best profile intact except for the ideal-PSD calibration:

- `calibration_file: algo/deadleaf_13b10_psd_calibration.json -> algo/deadleaf_13b10_psd_calibration_anchored.json`

## PSD / MTF Result

Compared with the current PR `#30` best branch:

| Profile | `curve_mae_mean` | mean abs signed-rel | `MTF20` MAE | `MTF30` MAE | `MTF50` MAE |
| --- | --- | --- | --- | --- | --- |
| PR `#30` best branch | `0.04306442` | `0.08692956` | `0.03300903` | `0.03693524` | `0.00933262` |
| anchored high-frequency PSD candidate | `0.04300089` | `0.08671417` | `0.03301077` | `0.03693639` | `0.00933262` |

Metric deltas from the PR `#30` best branch:

- `curve_mae_mean`: `-0.00006353` better
- mean absolute signed-relative MTF residual: `-0.00021539` better
- `MTF20` MAE: `+0.00000175` worse
- `MTF30` MAE: `+0.00000116` worse
- `MTF50` MAE: unchanged to the checked precision

Band movement stays concentrated in the upper half of the curve:

- `low`: unchanged
- `mid`: unchanged
- `high`: `0.04964177 -> 0.04982888` slightly worse
- `top`: `-0.16462715 -> -0.16357849` better

## Acutance / Quality-Loss Guardrails

Compared with the same baseline:

| Profile | `curve_mae_mean` | focus-preset Acutance MAE mean | `overall_quality_loss_mae_mean` |
| --- | --- | --- | --- |
| PR `#30` best branch | `0.03683438` | `0.04249131` | `1.22214341` |
| anchored high-frequency PSD candidate | `0.03678903` | `0.04248683` | `1.22149895` |

Guardrail deltas:

- `curve_mae_mean`: `-0.00004534` better
- focus-preset Acutance MAE mean: `-0.00000448` better
- `overall_quality_loss_mae_mean`: `-0.00064446` better
- `5.5" Phone Display Acutance` MAE: `+0.00000010` worse
- `5.5" Phone Display Quality Loss` MAE: `+0.00000229` worse

## Working Conclusion

This is a real but very small improvement, not a decisive new main-line replacement.

Why it is worth recording:

- it improves both primary lower-layer metrics together on the PSD / MTF benchmark
- it does not pay for that win with a downstream regression on the tracked aggregate guardrails
- it keeps the family source-backed and tightly bounded around the chart / reference PSD prior

Why issue `#29` still remains open:

- the effect size is small
- `MTF20` and `MTF30` do not improve materially
- the README canonical-target gates are still not met even on the improved branch

## Outcome For Issue 29

The constrained anchored high-frequency ideal-PSD family is a plausible next lower-layer direction, but only as a small incremental refinement on top of the current best branch.

It should be treated as:

- better than the current baseline on the aggregate PSD / MTF fit
- downstream-safe enough to keep as a tracked candidate
- not strong enough by itself to claim the canonical target is solved
