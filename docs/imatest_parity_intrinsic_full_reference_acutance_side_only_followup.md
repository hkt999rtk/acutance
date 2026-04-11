# Imatest Parity Intrinsic Full-Reference Acutance-Side-Only Follow-up

Issue: `#37`  
Parent: `#29`  
Follow-up from: `#33`  
Context: `#30`, `#34`, `#36`

## What changed

- Added `intrinsic_full_reference_scope` to the parity benchmark entrypoints.
- Kept the existing intrinsic behavior as `replace_all`.
- Added `acutance_only` so the intrinsic/full-reference transfer can be applied only to the acutance-side path while leaving the baseline reported-MTF and quality-loss path intact.
- Added `algo/deadleaf_13b10_imatest_intrinsic_full_reference_acutance_side_only_profile.json`.
- Checked in:
  - `artifacts/imatest_parity_intrinsic_full_reference_acutance_side_only_benchmark.json`
  - `artifacts/imatest_parity_intrinsic_full_reference_acutance_side_only_psd_benchmark.json`

## Why this follow-up existed

PR `#34` showed that the intrinsic/full-reference family was useful for the remaining curve and focus-preset acutance gap, but it also broke the quality-loss objective badly enough that it could not replace the whole parity path.

Issue `#37` tested the narrow next question: whether that intrinsic signal should be limited to the acutance side while keeping the PR `#30` baseline branch for reported-MTF and quality loss.

## Result

PR `#30` merged baseline:

- `curve_mae_mean = 0.03683438`
- `acutance_focus_preset_mae_mean = 0.04249131`
- `overall_quality_loss_mae_mean = 1.22214341`

PR `#34` intrinsic/full-reference replacement:

- `curve_mae_mean = 0.03587346`
- `acutance_focus_preset_mae_mean = 0.03165223`
- `overall_quality_loss_mae_mean = 4.56800916`

Issue `#37` acutance-side-only split:

- `curve_mae_mean = 0.09800462`
- `acutance_focus_preset_mae_mean = 0.08663407`
- `overall_quality_loss_mae_mean = 1.22214341`

Relative to PR `#30`, the issue `#37` split:

- preserves `overall_quality_loss_mae_mean` exactly
- regresses `curve_mae_mean` sharply
- regresses `acutance_focus_preset_mae_mean` sharply
- loses the PR `#34` non-Phone acutance gains instead of preserving them

Preset-level acutance comparison against PR `#30`:

- `5.5" Phone Display Acutance`: `0.01380 -> 0.07161`
- `Computer Monitor Acutance`: `0.05269 -> 0.15277`
- `UHDTV Display Acutance`: `0.04794 -> 0.08931`
- `Small Print Acutance`: `0.04670 -> 0.04490`
- `Large Print Acutance`: `0.05132 -> 0.07459`

The PSD benchmark shows the same direction:

PR `#30` baseline:

- `curve_mae_mean = 0.04306442`
- `mtf_abs_signed_rel_mean = 0.08692956`

PR `#34` intrinsic/full-reference replacement:

- `curve_mae_mean = 0.03587346`
- `mtf_abs_signed_rel_mean = 0.20631329`

Issue `#37` acutance-side-only split:

- `curve_mae_mean = 0.10133586`
- `mtf_abs_signed_rel_mean = 0.11528892`

That means the split lands in the worst available curve regime while only partially recovering the MTF regression from PR `#34`.

## Conclusion

This follow-up is a bounded negative result.

Constraining the intrinsic/full-reference signal to the acutance side does preserve the PR `#30` quality-loss branch, but it does not preserve the PR `#34` curve or focus-preset acutance gains. Instead, it produces a much worse curve fit than both PR `#30` and PR `#34`.

So the issue `#37` answer is no: the intrinsic/full-reference family does not become a viable next main-line family when it is limited to the acutance side only in this form.
