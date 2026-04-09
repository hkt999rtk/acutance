# Imatest Parity Sensor Compensation Follow-up

This note records a first source-backed compensation pass for issue `#29`.

Motivation:

- the literal observable-parity path still underfits mid/high/top-frequency MTF badly
- the repo research note already identifies missing chart/sensor compensation as one of the highest-priority omitted model families
- this pass adds a minimal sensor-aperture compensation term to test whether part of that underfit is explainable as missing sensor/OLPF blur compensation rather than another arbitrary retune

Source basis:

- [dead_leaves_black_box_research.md](./dead_leaves_black_box_research.md)
  - chart/sensor compensation is explicitly listed as a missing variable family
  - official Imatest documentation treats measured MTF as the product of chart, lens, sensor, and image-processing terms

## Profiles Compared

Benchmark artifacts:

- [../artifacts/imatest_parity_sensor_compensation_psd_benchmark.json](../artifacts/imatest_parity_sensor_compensation_psd_benchmark.json)
- [../artifacts/imatest_parity_sensor_compensation_benchmark.json](../artifacts/imatest_parity_sensor_compensation_benchmark.json)

Profiles:

1. literal observable-parity baseline
   - [../algo/deadleaf_13b10_imatest_parity_profile.json](../algo/deadleaf_13b10_imatest_parity_profile.json)
2. literal observable-parity plus sensor compensation
   - [../algo/deadleaf_13b10_imatest_sensor_comp_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_profile.json)

Both profiles keep the same observable-parity assumptions:

- `gamma = 0.5`
- `bayer_mode = demosaic_red`
- fixed ROI with `texture_support_scale = true`
- empirical noise PSD and the current parity acutance-noise settings

The only modeled change in this pass is:

- `mtf_compensation_mode = sensor_aperture_sinc`
- `sensor_fill_factor = 1.5`

## PSD / MTF Result

Compared with the literal observable-parity baseline, the sensor-compensated candidate improves:

- `curve_mae_mean`: `0.06059 -> 0.05522`
- mean absolute band signed-rel error: `0.33627 -> 0.24782`
- `MTF20` threshold MAE: `0.11965 -> 0.07101`
- `MTF30` threshold MAE: `0.06395 -> 0.05194`
- `MTF50` threshold MAE: `0.01730 -> 0.01630`

Band-wise signed relative MTF residuals also improve materially where the literal path was worst:

- `high`: `-0.51145 -> -0.35265`
- `top`: `-0.80149 -> -0.55687`

Interpretation:

- a simple source-backed sensor-compensation term removes a meaningful part of the literal-parity high-frequency underfit
- this is stronger evidence than the earlier same-family-free retunes because it changes the model family rather than only retuning frequency scale or ROI policy

## Acutance / Quality Loss Result

The same candidate does **not** improve the end-to-end parity story overall:

- `curve_mae_mean`: `0.06059 -> 0.05522` improves
- focus-preset Acutance MAE mean: `0.06480 -> 0.06881` worsens
- `overall_quality_loss_mae_mean`: `3.31359 -> 3.37730` worsens

Interpretation:

- the compensation helps the literal parity curve and MTF residuals
- but the current one-parameter sensor compensation is still incomplete for preset Acutance / Quality Loss
- this should be treated as a useful partial step, not as the final fix for issue `#29`

## Working Conclusion

This pass demonstrates one concrete point:

- the literal observable-parity miss is not only a scalar-gamma or small-retune problem
- adding a source-backed sensor-compensation family changes the result in the expected direction for MTF residuals and curve alignment

But it also leaves a clear next boundary:

- sensor compensation alone is not enough to reach the README target
- the next useful step should either:
  - tune or extend the compensation family more carefully, or
  - combine it with another missing family such as OECF-driven linearization instead of claiming parity is solved

For now, `imatest_parity_sensor_comp_profile.release.json` should remain a reference experiment profile, not a release default.
