# Issue 56 Empirical Frequency-Scale Follow-up

This note records the bounded direct-method empirical `frequency_scale` follow-up for issue `#56`.

## Family

This pass stays inside the current direct-method branch from PR `#55` and changes only the global empirical frequency scale:

- start from the current anchored high-frequency direct-method profile with `roi_source = reference`
- keep the better static inferred reference-bin centers from PR `#53`
- keep the observable ROI policy from PR `#53` and the matched-ORI / Acutance / Quality Loss correction stack unchanged
- replace `frequency_scale = 1.0` with one README-backed empirical global scale candidate

This is distinct from issue `#50` because it does not reuse captured-image-size correction. It is distinct from issue `#52` because it leaves ROI policy unchanged. It is distinct from issue `#54` because it keeps the static inferred reference-bin centers instead of switching to per-capture observable-bin centers.

## Calibration Slice

The current repo already documents stable empirical dataset-scale ranges around `1.095` to `1.135`. A fresh lower-layer sweep on the current ROI-reference / static-bin path pushed the threshold-only objective to the top of the tested range:

- `best_scale = 1.15`
- `source_count = 40`

That threshold-only sweep did not become the committed candidate by itself. Full direct-method parity benchmarks were then run at three bounded empirical values:

- `1.095`
- `1.135`
- `1.15`

Among those three, `1.095` was the least-bad full-pipeline candidate, so this note records that one as the bounded issue-56 result.

## Comparison Set

PR `#30` baseline:

- PSD `curve_mae_mean = 0.04497615`
- PSD `mtf_abs_signed_rel_mean = 0.33019613`
- PSD `MTF20 / MTF30 / MTF50 = 0.11418549 / 0.07118338 / 0.03341906`
- Acutance `curve_mae_mean = 0.04497615`
- `acutance_focus_preset_mae_mean = 0.03479546`
- `overall_quality_loss_mae_mean = 2.19874216`

PR `#42` anchored high-frequency PSD follow-up:

- PSD `curve_mae_mean = 0.04306442`
- PSD `mtf_abs_signed_rel_mean = 0.08692956`
- PSD `MTF20 / MTF30 / MTF50 = 0.03300903 / 0.03693524 / 0.00933262`
- Acutance `curve_mae_mean = 0.03683438`
- `acutance_focus_preset_mae_mean = 0.04249131`
- `overall_quality_loss_mae_mean = 1.22214341`

PR `#53` observable-reference ROI follow-up:

- PSD `curve_mae_mean = 0.04231237`
- PSD `mtf_abs_signed_rel_mean = 0.08483351`
- PSD `MTF20 / MTF30 / MTF50 = 0.02658848 / 0.02903115 / 0.00921053`
- Acutance `curve_mae_mean = 0.03679567`
- `acutance_focus_preset_mae_mean = 0.04130714`
- `overall_quality_loss_mae_mean = 1.26357125`

PR `#55` observable-bin frequency-mapping follow-up:

- PSD `curve_mae_mean = 0.04241564`
- PSD `mtf_abs_signed_rel_mean = 0.08641068`
- PSD `MTF20 / MTF30 / MTF50 = 0.02109366 / 0.02920596 / 0.00942858`
- Acutance `curve_mae_mean = 0.03690674`
- `acutance_focus_preset_mae_mean = 0.04092806`
- `overall_quality_loss_mae_mean = 1.27229004`

Issue `#56` empirical `frequency_scale = 1.095` candidate:

- PSD `curve_mae_mean = 0.04810412`
- PSD `mtf_abs_signed_rel_mean = 0.14593604`
- PSD `MTF20 / MTF30 / MTF50 = 0.03158012 / 0.04783065 / 0.02157354`
- Acutance `curve_mae_mean = 0.03666082`
- `acutance_focus_preset_mae_mean = 0.03699264`
- `overall_quality_loss_mae_mean = 1.45822786`

## Result

Relative to PR `#55`, the `frequency_scale = 1.095` candidate is a mixed result with a clear lower-layer and Quality Loss regression:

- PSD `curve_mae_mean`: `0.04241564 -> 0.04810412`
- PSD signed-relative residual: `0.08641068 -> 0.14593604`
- `MTF20`: `0.02109366 -> 0.03158012`
- `MTF30`: `0.02920596 -> 0.04783065`
- `MTF50`: `0.00942858 -> 0.02157354`
- Acutance `curve_mae_mean`: `0.03690674 -> 0.03666082`
- `acutance_focus_preset_mae_mean`: `0.04092806 -> 0.03699264`
- `overall_quality_loss_mae_mean`: `1.27229004 -> 1.45822786`

Relative to PR `#53`, the same pattern holds:

- PSD `curve_mae_mean`: `0.04231237 -> 0.04810412`
- PSD signed-relative residual: `0.08483351 -> 0.14593604`
- `MTF20`: `0.02658848 -> 0.03158012`
- `MTF30`: `0.02903115 -> 0.04783065`
- `MTF50`: `0.00921053 -> 0.02157354`
- Acutance `curve_mae_mean`: `0.03679567 -> 0.03666082`
- `acutance_focus_preset_mae_mean`: `0.04130714 -> 0.03699264`
- `overall_quality_loss_mae_mean`: `1.26357125 -> 1.45822786`

Relative to PR `#42`, the empirical-scale candidate keeps only the narrower Acutance-side gains while losing the earlier lower-layer and Quality Loss behavior:

- PSD `curve_mae_mean`: `0.04306442 -> 0.04810412`
- PSD signed-relative residual: `0.08692956 -> 0.14593604`
- `MTF20`: `0.03300903 -> 0.03158012`
- `MTF30`: `0.03693524 -> 0.04783065`
- `MTF50`: `0.00933262 -> 0.02157354`
- Acutance `curve_mae_mean`: `0.03683438 -> 0.03666082`
- `acutance_focus_preset_mae_mean`: `0.04249131 -> 0.03699264`
- `overall_quality_loss_mae_mean`: `1.22214341 -> 1.45822786`

Relative to PR `#30`, the empirical-scale candidate is still much better on total Quality Loss and on the overall PSD curve, but it does not beat the earlier focus-preset Acutance aggregate:

- PSD `curve_mae_mean`: `0.04497615 -> 0.04810412`
- PSD signed-relative residual: `0.33019613 -> 0.14593604`
- `MTF20`: `0.11418549 -> 0.03158012`
- `MTF30`: `0.07118338 -> 0.04783065`
- `MTF50`: `0.03341906 -> 0.02157354`
- Acutance `curve_mae_mean`: `0.04497615 -> 0.03666082`
- `acutance_focus_preset_mae_mean`: `0.03479546 -> 0.03699264`
- `overall_quality_loss_mae_mean`: `2.19874216 -> 1.45822786`

The broader empirical-scale sweep also did not uncover a better nearby full-pipeline candidate. The higher values backed by the lower-layer threshold-only sweep were worse on the PSD benchmark:

- `frequency_scale = 1.135`: PSD `curve_mae_mean = 0.05150720`, signed-relative residual `= 0.17177130`
- `frequency_scale = 1.15`: PSD `curve_mae_mean = 0.05308857`, signed-relative residual `= 0.18150411`

## Conclusion

This is another bounded mixed result, not a new default direct-method path.

Applying a global empirical `frequency_scale` around the repo's documented dataset-level range can improve the Acutance curve and focus-preset Acutance metrics on the current ROI-reference / static-bin path. But the same family materially worsens the lower-layer PSD summary and pushes overall Quality Loss farther away from the current best direct-method branch. The threshold-only calibration sweep therefore does not transfer cleanly to the full direct-method benchmark objective, and `frequency_scale = 1.0` remains the better default on the current direct-method line.
