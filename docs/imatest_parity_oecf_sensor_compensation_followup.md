# Imatest Parity OECF And Sensor Compensation Follow-up

This note records the second source-backed model-family step for issue `#29`.

It builds on the earlier sensor-compensation pass in
[imatest_parity_sensor_compensation_followup.md](./imatest_parity_sensor_compensation_followup.md).

Motivation:

- the first sensor-compensation pass improved literal-parity MTF residuals and curve MAE
- but it still did not improve end-to-end preset Acutance or overall Quality Loss
- the repo research note also identifies OECF-driven linearization as another missing source-backed family

This pass combines both missing families in one narrowed experiment:

- sensor-aperture MTF compensation
- a toe-style inverse-OECF linearization proxy

The toe term is still an engineering proxy, not a measured Stepchart-derived OECF.
Its purpose is to test whether the remaining literal-parity miss is partly a tonal-state problem rather than only a blur-compensation problem.

## Profiles Compared

Benchmark artifacts:

- [../artifacts/imatest_parity_oecf_sensor_compensation_psd_benchmark.json](../artifacts/imatest_parity_oecf_sensor_compensation_psd_benchmark.json)
- [../artifacts/imatest_parity_oecf_sensor_compensation_benchmark.json](../artifacts/imatest_parity_oecf_sensor_compensation_benchmark.json)

Profiles:

1. literal observable-parity baseline
   - [../algo/deadleaf_13b10_imatest_parity_profile.json](../algo/deadleaf_13b10_imatest_parity_profile.json)
2. literal observable-parity plus sensor compensation
   - [../algo/deadleaf_13b10_imatest_sensor_comp_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_profile.json)
3. literal observable-parity plus sensor compensation and toe linearization
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_profile.json)

The third profile keeps the same observable report assumptions:

- `gamma = 0.5`
- `bayer_mode = demosaic_red`
- `texture_support_scale = true`

and adds:

- `mtf_compensation_mode = sensor_aperture_sinc`
- `sensor_fill_factor = 1.5`
- `linearization_mode = toe_power`
- `linearization_toe = 0.12`

## PSD / MTF Result

Compared with the literal observable-parity baseline, the combined candidate improves:

- `curve_mae_mean`: `0.06059 -> 0.03812`
- mean absolute band signed-rel error: `0.33627 -> 0.08703`
- `MTF20` threshold MAE: `0.11965 -> 0.02669`
- `MTF30` threshold MAE: `0.06395 -> 0.03691`
- `MTF50` threshold MAE: `0.01730 -> 0.00937`

Band-wise signed relative MTF residuals move much closer to zero:

- `high`: `-0.51145 -> 0.04943`
- `top`: `-0.80149 -> -0.16446`

Interpretation:

- the combined compensation-plus-linearization path materially reduces the literal-parity high-frequency underfit
- unlike the first compensation-only pass, this second step also removes most of the top-band suppression without needing another free-form shape correction

## Acutance / Quality Loss Result

Compared with the literal observable-parity baseline, the combined candidate changes:

- `curve_mae_mean`: `0.06059 -> 0.03812` improves materially
- `overall_quality_loss_mae_mean`: `3.31359 -> 3.01158` improves materially
- focus-preset Acutance MAE mean: `0.06480 -> 0.06823` still worsens

Compared with the compensation-only candidate:

- `curve_mae_mean`: `0.05522 -> 0.03812` improves again
- `overall_quality_loss_mae_mean`: `3.37730 -> 3.01158` improves again
- focus-preset Acutance MAE mean: `0.06881 -> 0.06823` improves slightly, but still not enough to beat the literal baseline

Interpretation:

- OECF-style toe linearization plus sensor compensation is the first issue-29 branch that improves both literal-parity curve MAE and overall Quality Loss together
- however, it still does not solve preset Acutance alignment overall
- this means the README target is still not reached, but the branch now has a more credible multi-family direction than either scalar-gamma-only or compensation-only experiments

## Working Conclusion

This pass establishes a more defensible current direction for issue `#29`:

- missing OECF-driven linearization and missing sensor compensation are both contributing factors in the literal observable-parity gap
- combining them moves the literal path materially closer on MTF residuals, threshold readouts, curve MAE, and overall Quality Loss
- the remaining weakness is now more concentrated in preset Acutance behavior rather than the earlier broad literal-parity MTF collapse

What remains:

- the toe proxy is still not a measured OECF from chart patches
- preset Acutance MAE still does not improve overall
- later work should either refine the linearization family with stronger source-backed constraints, or combine this branch with another missing family before claiming the canonical target is solved

For now, `imatest_parity_sensor_comp_toe_profile.release.json` should remain a reference experiment profile, not a release default.
