## Issue

Issue `#48` asks for one bounded scene-/process-dependent ISP family after PR `#47`, using only source-backed proxies already supported by the dead-leaves repo contents.

## Family

This pass tests the narrowest currently source-backed proxy that still moves the post-PR-47 intrinsic branch:

- keep PR `#47`'s intrinsic phase-retained full-reference transfer fixed
- derive per-capture high-frequency noise share from the existing dead-leaves estimate
- gate one small MTF shape correction bump from that measured share

The initial attempt to reuse the existing `acutance_noise_scale_mode` plus `high_frequency_guard` settings from PR `#30` produced a no-op on the intrinsic `replace_all` path: those knobs are applied inside `estimate_dead_leaves_mtf()`, but issue `#48`'s active intrinsic branch later overwrites the MTF with the paired-`ori` transfer result. The moving part in this family is therefore the downstream `hf_noise_share_gated_bump` correction, which still uses the measured high-frequency noise share as its scene-/process-dependent gate.

## Result

Current PR `#30` baseline:

- PSD `curve_mae_mean = 0.04306442`
- PSD `mtf_abs_signed_rel_mean = 0.08692956`
- PSD `MTF20 / MTF30 / MTF50 = 0.03300903 / 0.03693524 / 0.00933262`
- Acutance `curve_mae_mean = 0.03683438`
- `acutance_focus_preset_mae_mean = 0.04249131`
- `overall_quality_loss_mae_mean = 1.22214341`
- `5.5" Phone Display Quality Loss` MAE = `0.14297763`
- `5.5" Phone Display Acutance` MAE = `0.01380215`

PR `#34` intrinsic full-reference prototype:

- PSD `curve_mae_mean = 0.03587346`
- PSD `mtf_abs_signed_rel_mean = 0.20631329`
- PSD `MTF20 / MTF30 / MTF50 = 0.08283943 / 0.03793906 / 0.00502893`
- Acutance `curve_mae_mean = 0.03587346`
- `acutance_focus_preset_mae_mean = 0.03165223`
- `overall_quality_loss_mae_mean = 4.56800916`
- `5.5" Phone Display Quality Loss` MAE = `10.62507645`
- `5.5" Phone Display Acutance` MAE = `0.01955014`

PR `#47` phase-retention follow-up:

- PSD `curve_mae_mean = 0.03280181`
- PSD `mtf_abs_signed_rel_mean = 0.13993779`
- PSD `MTF20 / MTF30 / MTF50 = 0.08576635 / 0.01789155 / 0.00719609`
- Acutance `curve_mae_mean = 0.03280181`
- `acutance_focus_preset_mae_mean = 0.02892053`
- `overall_quality_loss_mae_mean = 14.47575885`
- `5.5" Phone Display Quality Loss` MAE = `60.77410532`
- `5.5" Phone Display Acutance` MAE = `0.03525638`

Issue `#48` noise-share-gated shape candidate:

- PSD `curve_mae_mean = 0.03280181`
- PSD `mtf_abs_signed_rel_mean = 0.13993779`
- PSD `MTF20 / MTF30 / MTF50 = 0.08576635 / 0.01789155 / 0.00719609`
- Acutance `curve_mae_mean = 0.03283991`
- `acutance_focus_preset_mae_mean = 0.02890324`
- `overall_quality_loss_mae_mean = 14.47328913`
- `5.5" Phone Display Quality Loss` MAE = `60.68418298`
- `5.5" Phone Display Acutance` MAE = `0.03513954`

Relative to PR `#47`, this bounded ISP proxy:

- leaves the PSD / MTF path unchanged in practice
- regresses Acutance `curve_mae_mean` slightly from `0.03280181` to `0.03283991`
- improves `acutance_focus_preset_mae_mean` slightly from `0.02892053` to `0.02890324`
- improves `overall_quality_loss_mae_mean` slightly from `14.47575885` to `14.47328913`
- improves `5.5" Phone Display Quality Loss` MAE slightly from `60.77410532` to `60.68418298`
- improves `5.5" Phone Display Acutance` MAE slightly from `0.03525638` to `0.03513954`

Relative to PR `#34`, this candidate is still much better on curve fit and focus-preset Acutance, but it remains dramatically worse on downstream Quality Loss:

- `curve_mae_mean`: `0.03587346 -> 0.03283991`
- `acutance_focus_preset_mae_mean`: `0.03165223 -> 0.02890324`
- `overall_quality_loss_mae_mean`: `4.56800916 -> 14.47328913`
- `5.5" Phone Display Quality Loss` MAE: `10.62507645 -> 60.68418298`

Relative to PR `#30`, the candidate is still nowhere near the current merged branch on Quality Loss despite better curve fit:

- `curve_mae_mean`: `0.03683438 -> 0.03283991`
- `acutance_focus_preset_mae_mean`: `0.04249131 -> 0.02890324`
- `overall_quality_loss_mae_mean`: `1.22214341 -> 14.47328913`
- `5.5" Phone Display Quality Loss` MAE: `0.14297763 -> 60.68418298`

## Conclusion

This is a bounded mixed result, not a new main-line direction.

The measured high-frequency-noise-share gate does slightly improve the phone-dominated downstream failure that PR `#47` exposed, but the effect size is tiny and it does not materially reduce the intrinsic branch's Quality Loss regression. The family is still useful as a source-backed negative: the current missing latent variable is not solved by a small noise-share-gated shape tweak alone.
