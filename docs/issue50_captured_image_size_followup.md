# Issue 50 Captured-Image-Size Follow-up

This note records the first bounded chart-scale / captured-image-size follow-up for issue `#50`.

## Family

This pass stays inside the current direct-method branch and tests one explicit captured-image-size correction derived from current repo evidence:

- start from the current direct-method lower-layer branch from PR `#42`
- replace the per-capture `texture_support_scale` heuristic with one fixed captured-image-size correction
- derive that fixed correction from the measured support statistics of the current dataset

Measured support statistics across the 40 `R_Random.csv` captures in `20260318_deadleaf_13b10`:

- min `texture_support_scale = 1.32244595`
- max `texture_support_scale = 1.33038222`
- mean `texture_support_scale = 1.32689400`
- median `texture_support_scale = 1.32666680`

The tracked candidate therefore uses:

- `texture_support_scale = false`
- `frequency_scale = 1.3268939965725617`

This is distinct from issue `#41` because it does not change the chart-prior slope or ideal-PSD calibration. It is also distinct from issue `#48` because it stays in the direct-method branch and changes only the chart-scale / frequency-mapping family.

## Comparison Set

PR `#30` baseline:

- PSD `curve_mae_mean = 0.04306442`
- PSD `mtf_abs_signed_rel_mean = 0.08692956`
- PSD `MTF20 / MTF30 / MTF50 = 0.03300903 / 0.03693524 / 0.00933262`
- Acutance `curve_mae_mean = 0.03683438`
- `acutance_focus_preset_mae_mean = 0.04249131`
- `overall_quality_loss_mae_mean = 1.22214341`

PR `#42` anchored high-frequency PSD follow-up:

- PSD `curve_mae_mean = 0.04300089`
- PSD `mtf_abs_signed_rel_mean = 0.08671417`
- PSD `MTF20 / MTF30 / MTF50 = 0.03301077 / 0.03693639 / 0.00933262`
- Acutance `curve_mae_mean = 0.03678903`
- `acutance_focus_preset_mae_mean = 0.04248683`
- `overall_quality_loss_mae_mean = 1.22149895`

PR `#43` chart-prior slope mixed negative:

- PSD `curve_mae_mean = 0.02660758`
- PSD `mtf_abs_signed_rel_mean = 0.33273968`
- PSD `MTF20 / MTF30 / MTF50 = 0.03801027 / 0.05639194 / 0.03366694`
- Acutance `curve_mae_mean = 0.02681195`
- `acutance_focus_preset_mae_mean = 0.02882649`
- `overall_quality_loss_mae_mean = 1.47355548`

Issue `#50` captured-image-size mean candidate:

- PSD `curve_mae_mean = 0.04325206`
- PSD `mtf_abs_signed_rel_mean = 0.08726213`
- PSD `MTF20 / MTF30 / MTF50 = 0.03310971 / 0.03698518 / 0.00940762`
- Acutance `curve_mae_mean = 0.03692861`
- `acutance_focus_preset_mae_mean = 0.04314809`
- `overall_quality_loss_mae_mean = 1.23268776`

## Result

Relative to PR `#42`, the explicit captured-image-size replacement is worse on every reported top-line metric:

- PSD `curve_mae_mean`: `0.04300089 -> 0.04325206`
- PSD signed-relative residual: `0.08671417 -> 0.08726213`
- `MTF20`: `0.03301077 -> 0.03310971`
- `MTF30`: `0.03693639 -> 0.03698518`
- `MTF50`: `0.00933262 -> 0.00940762`
- Acutance `curve_mae_mean`: `0.03678903 -> 0.03692861`
- `acutance_focus_preset_mae_mean`: `0.04248683 -> 0.04314809`
- `overall_quality_loss_mae_mean`: `1.22149895 -> 1.23268776`

Relative to PR `#30`, the candidate also regresses every reported top-line metric:

- PSD `curve_mae_mean`: `0.04306442 -> 0.04325206`
- PSD signed-relative residual: `0.08692956 -> 0.08726213`
- `MTF20`: `0.03300903 -> 0.03310971`
- `MTF30`: `0.03693524 -> 0.03698518`
- `MTF50`: `0.00933262 -> 0.00940762`
- Acutance `curve_mae_mean`: `0.03683438 -> 0.03692861`
- `acutance_focus_preset_mae_mean`: `0.04249131 -> 0.04314809`
- `overall_quality_loss_mae_mean`: `1.22214341 -> 1.23268776`

Relative to PR `#43`, this candidate avoids the catastrophic chart-prior slope failure, but it still does not become a viable direct-method improvement:

- the lower-layer threshold and signed-relative metrics remain close to the PR `#30` / PR `#42` branch rather than collapsing like PR `#43`
- but every reported top-line metric is still slightly worse than the current direct-method branch

## Conclusion

This is a bounded negative result, not a new main-line direction.

Replacing the current per-capture `texture_support_scale` heuristic with one explicit fixed captured-image-size correction derived from the dataset mean does not help. The effect is small but uniformly worse, which suggests the existing per-capture support estimate is a better approximation than this first explicit fixed-size substitute.
