# Issue 44 Intrinsic Phase-ECC Affine Follow-up

Issue: `#44`  
Parent: `#29`  
Context: `#33`, `#34`, `#38`, `#43`

## What changed

- Added a bounded intrinsic registration mode, `phase_ecc_affine`, for the paired-`ori` full-reference path.
- Kept the existing phase-correlation translation estimate as the initializer, then refined the alignment with an ECC affine warp.
- Added focused tests showing the affine mode improves small rotation/scale alignment while keeping the intrinsic transfer curve stable and clipped.
- Checked in:
  - `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_ecc_affine_profile.json`
  - `artifacts/issue44_intrinsic_phase_ecc_affine_psd_benchmark.json`
  - `artifacts/issue44_intrinsic_phase_ecc_affine_acutance_benchmark.json`

## Why this family

Issue `#33` / PR `#34` only implemented the minimum intrinsic registration slice: translation-only alignment via phase correlation.

The repo research inventory still marks reference-image warp/alignment as a major missing intrinsic family, so this issue tested one bounded refinement that stays inside the existing paired-`ori` source data: affine warp registration initialized from the current phase-correlation estimate.

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

This issue's phase-ECC affine intrinsic candidate:

- PSD `curve_mae_mean = 0.03710490`
- PSD `mtf_abs_signed_rel_mean = 0.21560308`
- PSD `MTF20 / MTF30 / MTF50 = 0.08788120 / 0.03858604 / 0.00504981`
- Acutance `curve_mae_mean = 0.03710490`
- `acutance_focus_preset_mae_mean = 0.03259058`
- `overall_quality_loss_mae_mean = 4.74249698`

Relative to PR `#30`, the affine-refined intrinsic path still improves curve fit and focus-preset Acutance, but it remains far outside the merged branch on overall Quality Loss and PSD signed-relative residuals.

Relative to PR `#34`, the affine refinement is worse on every reported top-line metric:

- PSD curve fit regresses from `0.03587346` to `0.03710490`
- PSD signed-relative residual regresses from `0.20631329` to `0.21560308`
- `MTF20 / MTF30 / MTF50` each worsen slightly
- focus-preset Acutance regresses from `0.03165223` to `0.03259058`
- overall Quality Loss regresses from `4.56800916` to `4.74249698`

## Conclusion

This is a bounded negative result, not a viable next main-line intrinsic registration direction.

Affine ECC warp refinement does not recover the PR `#34` intrinsic prototype's guardrail regressions. It preserves the same broad mixed shape as the earlier intrinsic family, then nudges the already-bad PSD and Quality Loss metrics slightly further away from the README-facing branch.
