# Issue 39 Chart And Sensor Compensation Follow-up

This note records the first bounded prototype for issue `#39`.

It follows the direction set in issue `#39` after PR `#38`:

- move the search back down to the MTF layer
- test one source-backed chart / reference-model family
- judge the result on PSD / MTF metrics first against the current PR `#30` best branch

## Source Basis

The source-backed family used here is the chart / sensor compensation path already called out in
[dead_leaves_black_box_research.md](./dead_leaves_black_box_research.md):

- Imatest documentation models measured MTF as the product of chart, lens, sensor, and processing terms
- the repo already had a one-term `sensor_aperture_sinc` approximation
- this prototype extends that same family with a second aperture term for the chart medium instead of opening a new unrelated search axis

## Profiles Compared

Baseline, representing the current PR `#30` best branch:

- [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_profile.json)

Candidate prototype from this issue:

- [../algo/deadleaf_13b10_imatest_chart_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_profile.json](../algo/deadleaf_13b10_imatest_chart_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_profile.json)

Artifact:

- [../artifacts/issue39_chart_sensor_compensation_psd_benchmark.json](../artifacts/issue39_chart_sensor_compensation_psd_benchmark.json)

The candidate keeps the PR `#30` profile intact except for the MTF-layer family change:

- `mtf_compensation_mode: sensor_aperture_sinc -> chart_sensor_aperture_sinc`
- `chart_fill_factor: 0.15`

## PSD / MTF Result

Compared with the current PR `#30` best branch:

| Profile | `curve_mae_mean` | mean abs signed-rel | `MTF20` MAE | `MTF30` MAE | `MTF50` MAE |
| --- | --- | --- | --- | --- | --- |
| PR `#30` best branch | `0.04306442` | `0.08692956` | `0.03300903` | `0.03693524` | `0.00933262` |
| issue `#39` chart+sensor candidate | `0.04313186` | `0.08672250` | `0.03317034` | `0.03705447` | `0.00938074` |

Metric deltas from the PR `#30` best branch:

- `curve_mae_mean`: `+0.00006744` worse
- mean absolute signed-relative MTF residual: `-0.00020705` better
- `MTF20` MAE: `+0.00016132` worse
- `MTF30` MAE: `+0.00011924` worse
- `MTF50` MAE: `+0.00004813` worse

Band-wise signed-relative movement is also mixed rather than clearly better:

- `top`: `-0.16462715 -> -0.15981866` improves slightly
- `high`: `0.04964177 -> 0.05266795` worsens
- `mid`: `0.10965437 -> 0.11051854` worsens
- `low`: `0.02379494 -> 0.02388487` worsens slightly

## Working Conclusion

This prototype does **not** meet issue `#39`'s stricter lower-layer win condition.

Why:

- it does not improve `curve_mae_mean`
- it does not improve the threshold readouts at `MTF20`, `MTF30`, or `MTF50`
- the small win in mean absolute signed-relative residual is too weak and too mixed across bands to outweigh the curve and threshold losses

Because the candidate fails at the primary PSD / MTF gate, this pass stops here and does not claim any downstream Acutance or Quality-Loss success from this family.

## Outcome For Issue 39

The bounded chart-plus-sensor aperture prototype is another negative result, not a new main-line family.

That still narrows the search space usefully:

- the existing one-term sensor compensation path remains the better approximation in the current reduced model
- issue `#39` should not continue searching this exact chart-aperture variant unless a stronger source-backed chart-medium model justifies reopening the family
