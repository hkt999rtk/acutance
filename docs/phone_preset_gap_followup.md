# Issue 70 Phone Preset Gap Follow-up

This note records the bounded issue `#70` follow-up for the remaining `5.5" Phone Display` gap after the canonical scoreboard chain completed in issue `#69`.

## Why This Slice

The canonical scoreboard made two facts clear:

- the current best still-`parity-valid` direct-method row remains [issue `#29` anchored high-frequency PSD](./issue29_anchored_high_frequency_psd_followup.md)
- the best recent source-backed phone-improving family inside the current direct-method line is the bounded scene-/process-dependent ISP proxy from [issue `#61`](./issue61_isp_family_followup.md)

Issue `#70` therefore tested the narrowest source-backed next slice that still uses current repo evidence instead of a preset-side display patch:

- keep the issue-29 anchored-high-frequency PSD baseline intact
- carry over the existing `hf_noise_share_gated_bump` MTF-shape correction from issue `#61`
- do not change the release profile or any `Phone` preset display compensation

That keeps the change in the upstream `MTF / PSD` family rather than masking the residual with a downstream preset override.

## Profiles Compared

Baseline, representing the best current parity-valid direct-method row:

- [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_profile.json)

Issue `#70` candidate:

- [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_hf_noise_share_shape_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_hf_noise_share_shape_profile.json)

Checked-in artifacts:

- [../artifacts/issue70_phone_preset_gap_psd_benchmark.json](../artifacts/issue70_phone_preset_gap_psd_benchmark.json)
- [../artifacts/issue70_phone_preset_gap_acutance_benchmark.json](../artifacts/issue70_phone_preset_gap_acutance_benchmark.json)
- [../artifacts/phone_preset_gap_benchmark.json](../artifacts/phone_preset_gap_benchmark.json)

The candidate changes only one upstream family knob set relative to the baseline:

- `mtf_shape_correction_mode: none -> hf_noise_share_gated_bump`
- `mtf_shape_correction_gain = 0.035`
- `mtf_shape_correction_share_gate_lo / hi = 0.05 / 0.08`
- same issue-61 mid/high-band shape parameters

Everything else stays on the issue-29 anchored-high-frequency PSD line, including:

- anchored PSD calibration
- `roi_source = reference_refined`
- current matched-ORI correction stack
- current Acutance / Quality Loss correction stack

## Result

### Primary direct-method parity metrics

| Profile | `curve_mae_mean` | focus-preset Acutance MAE mean | `overall_quality_loss_mae_mean` | `Phone Acutance MAE` | `Phone Quality Loss MAE` |
| --- | --- | --- | --- | --- | --- |
| issue `#29` anchored-HF baseline | `0.03678903` | `0.04248683` | `1.22149895` | `0.01380225` | `0.14297991` |
| issue `#70` candidate | `0.03713142` | `0.04284080` | `1.23131857` | `0.01378537` | `0.14145355` |

Metric deltas from the baseline:

- `curve_mae_mean`: `+0.00034239` worse
- focus-preset Acutance MAE mean: `+0.00035397` worse
- `overall_quality_loss_mae_mean`: `+0.00981961` worse
- `Phone Acutance MAE`: `-0.00001688` better
- `Phone Quality Loss MAE`: `-0.00152636` better

### `MTF20 / MTF30 / MTF50` guardrail

| Profile | `MTF20` MAE | `MTF30` MAE | `MTF50` MAE |
| --- | --- | --- | --- |
| issue `#29` anchored-HF baseline | `0.03301077` | `0.03693639` | `0.00933262` |
| issue `#70` candidate | `0.03301077` | `0.03693639` | `0.00933262` |

Threshold readouts are unchanged to the checked precision:

- `MTF20`: unchanged
- `MTF30`: unchanged
- `MTF50`: unchanged

### Trend guard

Issue `#70` does not modify the tracked release profile, so the checked-in trend guard remains the current `release/parity_fit` row:

- trend correctness: `3/20 (0.150)`
- gain-trend series shape error: `0.01862826`
- gain-trend delta MAE mean: `0.01814888`

The machine-readable issue artifact records this explicitly as an unchanged release-side guard:

- [../artifacts/phone_preset_gap_benchmark.json](../artifacts/phone_preset_gap_benchmark.json)

## Acceptance Readout

Issue `#70` asked for simultaneous improvement, not a `Phone`-only win.

What improved:

- `Phone Acutance MAE`
- `Phone Quality Loss MAE`
- `MTF20 / MTF30 / MTF50` did not regress
- tracked release trend guard did not regress because the release path was unchanged

What failed the acceptance gate:

- `curve_mae_mean` regressed
- focus-preset Acutance MAE mean regressed
- `overall_quality_loss_mae_mean` regressed

So this branch does narrow the Phone preset gap, but it does not satisfy the issue requirement that the overall MAE improve at the same time.

## Source Attribution

The small phone gain here comes from the upstream `MTF / PSD` side, not from the display model:

- no `Phone` preset viewing-distance or display-MTF override changed
- no release profile changed
- the only delta is the source-backed `high_frequency_noise_share`-gated post-MTF shape correction already documented in issue `#61`

That makes this result useful even though it is not promotable: it shows that the bounded scene-/process-dependent ISP proxy can shave a little of the phone residual on the stronger anchored-HF baseline, but it still does not transfer into a simultaneous whole-surface MAE improvement.

## Conclusion

This is a bounded mixed negative result, not a new default path.

The issue-61 ISP proxy survives as a source-backed explanation line for part of the Phone residual, but on the current anchored-HF baseline it remains too weak and too mixed:

- `Phone` improves slightly
- threshold readouts stay flat
- aggregate parity metrics regress

So the repo should keep the issue-29 anchored-HF line as the stronger parity-valid direct-method branch, record this issue-70 result as another bounded negative/mixed family, and leave the next follow-up to a different source-backed family rather than a stronger version of the same phone-targeted shape tweak.

## Validation

- `python3 -m algo.benchmark_parity_psd_mtf 20260318_deadleaf_13b10 algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_profile.json algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_hf_noise_share_shape_profile.json --output artifacts/issue70_phone_preset_gap_psd_benchmark.json`
- `python3 -m algo.benchmark_parity_acutance_quality_loss 20260318_deadleaf_13b10 algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_profile.json algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_hf_noise_share_shape_profile.json --output artifacts/issue70_phone_preset_gap_acutance_benchmark.json`
- `python3 -m algo.build_phone_preset_gap_benchmark`
- `python3 -m pytest tests/test_build_phone_preset_gap_benchmark.py tests/test_benchmark_parity_psd_mtf.py tests/test_benchmark_parity_acutance_quality_loss.py`
