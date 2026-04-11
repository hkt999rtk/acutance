# Issue 52 Direct ROI Reference Follow-up

This note records the bounded direct-method ROI-policy follow-up for issue `#52`.

## Family

This pass stays inside the current direct-method branch from PR `#42` and changes only the ROI policy:

- start from the current anchored high-frequency direct-method profile from PR `#42`
- remove the latent `reference_refined` texture-support refinement around the observable crop
- use the observable Imatest `L R T B` crop directly with `roi_source = reference`

This is distinct from issue `#50` because it does not change chart scale or frequency mapping. It is also distinct from issue `#41` because it does not change the chart prior, ideal PSD, or OECF family.

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

PR `#51` captured-image-size negative:

- PSD `curve_mae_mean = 0.04325206`
- PSD `mtf_abs_signed_rel_mean = 0.08726213`
- PSD `MTF20 / MTF30 / MTF50 = 0.03310971 / 0.03698518 / 0.00940762`
- Acutance `curve_mae_mean = 0.03692861`
- `acutance_focus_preset_mae_mean = 0.04314809`
- `overall_quality_loss_mae_mean = 1.23268776`

Issue `#52` observable-reference ROI candidate:

- PSD `curve_mae_mean = 0.04231237`
- PSD `mtf_abs_signed_rel_mean = 0.08483351`
- PSD `MTF20 / MTF30 / MTF50 = 0.02658848 / 0.02903115 / 0.00921053`
- Acutance `curve_mae_mean = 0.03679567`
- `acutance_focus_preset_mae_mean = 0.04130714`
- `overall_quality_loss_mae_mean = 1.26357125`

## Result

Relative to PR `#42`, using the observable reference crop directly is a clear lower-layer improvement but a downstream Quality Loss regression:

- PSD `curve_mae_mean`: `0.04300089 -> 0.04231237`
- PSD signed-relative residual: `0.08671417 -> 0.08483351`
- `MTF20`: `0.03301077 -> 0.02658848`
- `MTF30`: `0.03693639 -> 0.02903115`
- `MTF50`: `0.00933262 -> 0.00921053`
- Acutance `curve_mae_mean`: `0.03678903 -> 0.03679567`
- `acutance_focus_preset_mae_mean`: `0.04248683 -> 0.04130714`
- `overall_quality_loss_mae_mean`: `1.22149895 -> 1.26357125`

Relative to PR `#30`, the same pattern holds:

- PSD `curve_mae_mean`: `0.04306442 -> 0.04231237`
- PSD signed-relative residual: `0.08692956 -> 0.08483351`
- `MTF20`: `0.03300903 -> 0.02658848`
- `MTF30`: `0.03693524 -> 0.02903115`
- `MTF50`: `0.00933262 -> 0.00921053`
- Acutance `curve_mae_mean`: `0.03683438 -> 0.03679567`
- `acutance_focus_preset_mae_mean`: `0.04249131 -> 0.04130714`
- `overall_quality_loss_mae_mean`: `1.22214341 -> 1.26357125`

Relative to PR `#51`, the observable-reference ROI candidate is better on every reported lower-layer and Acutance metric, but it still loses on overall Quality Loss:

- PSD `curve_mae_mean`: `0.04325206 -> 0.04231237`
- PSD signed-relative residual: `0.08726213 -> 0.08483351`
- `MTF20`: `0.03310971 -> 0.02658848`
- `MTF30`: `0.03698518 -> 0.02903115`
- `MTF50`: `0.00940762 -> 0.00921053`
- Acutance `curve_mae_mean`: `0.03692861 -> 0.03679567`
- `acutance_focus_preset_mae_mean`: `0.04314809 -> 0.04130714`
- `overall_quality_loss_mae_mean`: `1.23268776 -> 1.26357125`

The Quality Loss regression is broad rather than phone-only. The candidate lands at:

- `5.5" Phone Display Quality Loss` MAE `= 0.16991880`
- `Computer Monitor Quality Loss` MAE `= 2.98871588`
- `Large Print Quality Loss` MAE `= 0.97539649`
- `Small Print Quality Loss` MAE `= 0.64455985`
- `UHDTV Display Quality Loss` MAE `= 1.53926526`

## Conclusion

This is a bounded mixed result, not a drop-in replacement for the current direct-method branch.

Using the observable Imatest crop directly removes some lower-layer error introduced by the current latent texture-support ROI refinement, and it improves focus-preset Acutance MAE. But the downstream Quality Loss fit moves materially in the wrong direction, so this candidate does not become the new canonical path by itself.
