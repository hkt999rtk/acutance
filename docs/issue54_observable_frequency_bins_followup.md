# Issue 54 Observable Frequency-Bin Follow-up

This note records the bounded direct-method frequency-mapping follow-up for issue `#54`.

## Family

This pass stays inside the current direct-method branch from PR `#53` and changes only the frequency-axis formulation:

- start from the current anchored high-frequency direct-method profile with observable ROI from PR `#53`
- keep the current ROI policy, texture-support scaling, and matched-ORI anchor behavior
- replace the inferred static `IMATEST_REFERENCE_BINS` centers with the directly observed per-capture `Table of MTF` frequency bins from each golden CSV via `frequency_bin_source = observable_table`

This is distinct from issue `#50` because it does not alter captured-image-size or chart-scale assumptions. It is also distinct from issue `#52` because it keeps `roi_source = reference` fixed and changes only the frequency-bin mapping.

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

Issue `#54` observable-bin frequency candidate:

- PSD `curve_mae_mean = 0.04241564`
- PSD `mtf_abs_signed_rel_mean = 0.08641068`
- PSD `MTF20 / MTF30 / MTF50 = 0.02109366 / 0.02920596 / 0.00942858`
- Acutance `curve_mae_mean = 0.03690674`
- `acutance_focus_preset_mae_mean = 0.04092806`
- `overall_quality_loss_mae_mean = 1.27229004`

## Result

Relative to PR `#53`, switching from inferred static bin centers to the observable per-capture table is a narrow lower-layer tradeoff, not a clear net win:

- PSD `curve_mae_mean`: `0.04231237 -> 0.04241564`
- PSD signed-relative residual: `0.08483351 -> 0.08641068`
- `MTF20`: `0.02658848 -> 0.02109366`
- `MTF30`: `0.02903115 -> 0.02920596`
- `MTF50`: `0.00921053 -> 0.00942858`
- Acutance `curve_mae_mean`: `0.03679567 -> 0.03690674`
- `acutance_focus_preset_mae_mean`: `0.04130714 -> 0.04092806`
- `overall_quality_loss_mae_mean`: `1.26357125 -> 1.27229004`

Relative to PR `#42`, the observable-bin candidate still keeps most of the later direct-method gains, but it does not recover the top-line Quality Loss baseline:

- PSD `curve_mae_mean`: `0.04306442 -> 0.04241564`
- PSD signed-relative residual: `0.08692956 -> 0.08641068`
- `MTF20`: `0.03300903 -> 0.02109366`
- `MTF30`: `0.03693524 -> 0.02920596`
- `MTF50`: `0.00933262 -> 0.00942858`
- Acutance `curve_mae_mean`: `0.03683438 -> 0.03690674`
- `acutance_focus_preset_mae_mean`: `0.04249131 -> 0.04092806`
- `overall_quality_loss_mae_mean`: `1.22214341 -> 1.27229004`

Relative to PR `#30`, the candidate remains much better on PSD and overall Quality Loss, but it still does not beat the early focus-preset Acutance aggregate:

- PSD `curve_mae_mean`: `0.04497615 -> 0.04241564`
- PSD signed-relative residual: `0.33019613 -> 0.08641068`
- `MTF20`: `0.11418549 -> 0.02109366`
- `MTF30`: `0.07118338 -> 0.02920596`
- `MTF50`: `0.03341906 -> 0.00942858`
- Acutance `curve_mae_mean`: `0.04497615 -> 0.03690674`
- `acutance_focus_preset_mae_mean`: `0.03479546 -> 0.04092806`
- `overall_quality_loss_mae_mean`: `2.19874216 -> 1.27229004`

The Quality Loss regression versus PR `#53` is broad rather than concentrated in one preset:

- `5.5" Phone Display Quality Loss` MAE `= 0.17403968`
- `Computer Monitor Quality Loss` MAE `= 3.00554172`
- `Large Print Quality Loss` MAE `= 0.97973065`
- `Small Print Quality Loss` MAE `= 0.64639024`
- `UHDTV Display Quality Loss` MAE `= 1.55574790`

## Conclusion

This is a bounded mixed result, not a new default frequency-mapping path.

Using the observable frequency table directly is source-backed and it improves the `MTF20` threshold error while preserving the general post-PR-42 direct-method gains. But the rest of the lower-layer PSD summary slips versus PR `#53`, the Acutance curve regresses slightly, and overall Quality Loss moves further away from the current best direct-method path. The static inferred reference-bin centers therefore remain the better default on the current dataset.
