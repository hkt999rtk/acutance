# Issue 41 Chart-Prior Slope Follow-up

This note records the re-scoped issue `#41` follow-up after PR `#42`.

The bounded family tested here stays inside the existing chart-prior / ideal-PSD path instead of reopening issue `#39`'s chart-plus-sensor compensation family or the unavailable measured chart-patch OECF scope that issue `#41` originally carried.

## Family Tested

The candidate uses one constrained high-frequency prior-slope change inside the ideal-PSD calibration:

- low-frequency segment stays on the current empirical quadratic calibration
- high-frequency segment keeps the same quadratic curvature but reduces the log-slope by `0.06`
- the two segments are joined with a narrow blend so the change stays bounded to the upper-frequency chart-prior region

Tracked files:

- [../algo/deadleaf_13b10_psd_calibration_chart_prior_slope_m006.json](../algo/deadleaf_13b10_psd_calibration_chart_prior_slope_m006.json)
- [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_chart_prior_slope_m006_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_chart_prior_slope_m006_profile.json)

Benchmark artifacts:

- [../artifacts/issue41_chart_prior_slope_psd_benchmark.json](../artifacts/issue41_chart_prior_slope_psd_benchmark.json)
- [../artifacts/issue41_chart_prior_slope_acutance_benchmark.json](../artifacts/issue41_chart_prior_slope_acutance_benchmark.json)

Comparison references:

- PR `#30` current best branch
- PR `#42` anchored-high-frequency chart-prior candidate

## Why This Is Source-Backed

This follows the same repo evidence that justified re-scoping issue `#41`:

- [dead_leaves_black_box_research.md](./dead_leaves_black_box_research.md) lists `chart ideal PSD / chart-MTF prior` as modeled but still partial
- the same note also lists `chart MTF exponent` as only partially modeled rather than explicitly exposed
- PR `#42` already showed that bounded chart-prior changes can move the lower-layer metrics without reopening unrelated families

That makes this pass a constrained prior-slope / chart-exponent-style audit inside the current data-supported ideal-PSD family.

## PSD / MTF Result

| Profile | `curve_mae_mean` | mean abs signed-rel | `MTF20` MAE | `MTF30` MAE | `MTF50` MAE |
| --- | --- | --- | --- | --- | --- |
| PR `#30` best branch | `0.04306442` | `0.08692956` | `0.03300903` | `0.03693524` | `0.00933262` |
| PR `#42` anchored HF PSD | `0.04300089` | `0.08671417` | `0.03301077` | `0.03693639` | `0.00933262` |
| issue `#41` chart-prior slope candidate | `0.02660758` | `0.33273968` | `0.03801027` | `0.05639194` | `0.03366694` |

Band movement for the new candidate:

- `low`: `0.02379494 -> -0.09534039`
- `mid`: `0.10965437 -> -0.27142747`
- `high`: `0.04964177 -> -0.32701824`
- `top`: `-0.16462715 -> -0.63717261`

Interpretation:

- aggregate curve MAE improves sharply
- the issue's primary lower-layer readouts get much worse
- the candidate no longer preserves the threshold behavior that PR `#30` and PR `#42` keep roughly stable

So this is not a viable next main-line chart-prior direction on the issue `#41` decision surface.

## Acutance / Quality-Loss Guardrails

| Profile | `curve_mae_mean` | focus-preset Acutance MAE mean | `overall_quality_loss_mae_mean` |
| --- | --- | --- | --- |
| PR `#30` best branch | `0.03683438` | `0.04249131` | `1.22214341` |
| PR `#42` anchored HF PSD | `0.03678903` | `0.04248683` | `1.22149895` |
| issue `#41` chart-prior slope candidate | `0.02681195` | `0.02882649` | `1.47355548` |

Additional preset movement for the new candidate:

- `5.5" Phone Display Acutance`: `0.01380215 -> 0.01246977` better
- `5.5" Phone Display Quality Loss`: `0.14297763 -> 0.22473581` worse

Interpretation:

- the same slope variant improves aggregate curve and Acutance fit materially
- but it regresses overall Quality Loss beyond the current branch and beyond the README quality-loss gate
- this confirms the family is another mixed result, not a safe upgrade over PR `#30` or PR `#42`

## Difference From PR 40

This issue does **not** reopen PR `#40`'s chart-plus-sensor aperture compensation family.

PR `#40` changed the compensation denominator with an explicit chart-medium aperture term.
This issue instead keeps the compensation path unchanged and only changes the chart-prior slope inside the ideal-PSD calibration.

That separation matters because the current result shows the failure mode is different:

- PR `#40` was a bounded lower-layer negative result with only small movement
- this slope variant moves the curve strongly, but it does so by destabilizing the threshold and quality-loss readouts

## Conclusion

The bounded chart-prior slope family is another mixed negative result.

What it proved:

- the chart-prior slope is a real signal-bearing lever inside the current reduced model
- that lever can improve aggregate curve and Acutance fit much more strongly than PR `#42`'s anchored residual

Why it still closes as a negative result:

- issue `#41` prioritizes PSD/MTF readouts first
- `MTF20`, `MTF30`, `MTF50`, and mean absolute signed-relative residual all regress badly
- overall Quality Loss also regresses from `1.22214341` to `1.47355548`

That means the family should be recorded, but not promoted as the next main-line chart-prior path.
