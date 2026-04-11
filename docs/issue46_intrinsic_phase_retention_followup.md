# Issue 46 Intrinsic Phase-Retention Follow-up

Issue: `#46`  
Parent: `#29`  
Context: `#33`, `#34`, `#44`, `#45`

## What changed

- Added a bounded intrinsic transfer mode, `radial_real_mean`, for the paired-`ori` full-reference path.
- Kept the existing intrinsic registration path fixed, then changed the transfer formulation to retain the in-phase component of the complex intrinsic transfer within each radial frequency bin instead of collapsing immediately to a magnitude-only ratio.
- Added focused tests showing the new mode stays near identity for registered translations and suppresses incoherent high-frequency gain in a synthetic phase-noise case.
- Checked in:
  - `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_profile.json`
  - `artifacts/issue46_intrinsic_phase_retention_psd_benchmark.json`
  - `artifacts/issue46_intrinsic_phase_retention_acutance_benchmark.json`

## Why this family

The research inventory still marks intrinsic phase retention as a missing method family even after issue `#44` ruled out a more faithful affine warp/alignment refinement.

The earlier intrinsic prototype in issue `#33` / PR `#34` aligned the paired-`ori` patch, then converted the complex cross-spectrum into a magnitude-only transfer before radial averaging. That means phase-incoherent energy is still turned into positive gain. This issue tests the bounded next slice that remains after PR `#45`: keep the warp/alignment path fixed and only change the intrinsic transfer to retain the in-phase component within each radial bin.

## Result

Current PR `#30` baseline:

- PSD `curve_mae_mean = 0.04306442`
- PSD `mtf_abs_signed_rel_mean = 0.08692956`
- PSD `MTF20 / MTF30 / MTF50 = 0.03300903 / 0.03693524 / 0.00933262`
- Acutance `curve_mae_mean = 0.03683438`
- `acutance_focus_preset_mae_mean = 0.04249131`
- `overall_quality_loss_mae_mean = 1.22214341`

PR `#34` intrinsic full-reference prototype:

- PSD `curve_mae_mean = 0.03587346`
- PSD `mtf_abs_signed_rel_mean = 0.20631329`
- PSD `MTF20 / MTF30 / MTF50 = 0.08283943 / 0.03793906 / 0.00502893`
- Acutance `curve_mae_mean = 0.03587346`
- `acutance_focus_preset_mae_mean = 0.03165223`
- `overall_quality_loss_mae_mean = 4.56800916`

PR `#45` affine warp/alignment follow-up:

- PSD `curve_mae_mean = 0.03710490`
- PSD `mtf_abs_signed_rel_mean = 0.21560308`
- PSD `MTF20 / MTF30 / MTF50 = 0.08788120 / 0.03858604 / 0.00504981`
- Acutance `curve_mae_mean = 0.03710490`
- `acutance_focus_preset_mae_mean = 0.03259058`
- `overall_quality_loss_mae_mean = 4.74249698`

This issue's phase-retention intrinsic candidate:

- PSD `curve_mae_mean = 0.03280181`
- PSD `mtf_abs_signed_rel_mean = 0.13993779`
- PSD `MTF20 / MTF30 / MTF50 = 0.08576635 / 0.01789155 / 0.00719609`
- Acutance `curve_mae_mean = 0.03280181`
- `acutance_focus_preset_mae_mean = 0.02892053`
- `overall_quality_loss_mae_mean = 14.47575885`

Relative to PR `#34`, this bounded phase-retention slice:

- improves PSD curve fit from `0.03587346` to `0.03280181`
- improves PSD signed-relative residual from `0.20631329` to `0.13993779`
- improves `MTF30` sharply from `0.03793906` to `0.01789155`
- improves focus-preset Acutance mean from `0.03165223` to `0.02892053`
- regresses `MTF20` slightly from `0.08283943` to `0.08576635`
- regresses `MTF50` from `0.00502893` to `0.00719609`
- regresses overall Quality Loss dramatically from `4.56800916` to `14.47575885`

Relative to PR `#45`, the new phase-retention slice is better on every reported PSD and Acutance aggregate, but still much worse on Quality Loss:

- PSD curve fit improves from `0.03710490` to `0.03280181`
- PSD signed-relative residual improves from `0.21560308` to `0.13993779`
- focus-preset Acutance mean improves from `0.03259058` to `0.02892053`
- overall Quality Loss worsens further from `4.74249698` to `14.47575885`

The Quality Loss regression is dominated by the phone preset:

- `5.5" Phone Display Quality Loss` MAE rises to `60.77410532`

## Conclusion

This is a bounded mixed result, not a new main-line replacement.

The phase-retention family is more promising than the affine warp/alignment follow-up because it materially improves curve fit, focus-preset Acutance, and PSD signed-relative residuals at the same time. But the current in-phase transfer formulation destabilizes the downstream Quality Loss mapping even more severely than PR `#34` and PR `#45`, so it should remain experiment-only.
