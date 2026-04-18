# Issue 132 Small Print Acutance Boundary Summary

- Result: `positive_targeted_not_full_canonical`.
- Candidate profile: `algo/issue132_small_print_acutance_parity_input_profile.json`.
- Target preset: `Small Print Acutance`.
- Override source profile: `algo/deadleaf_13b10_parity_psd_mtf_profile.json`.

## Metrics

| Metric | PR #125 | Issue #132 | Delta | Gate |
| --- | ---: | ---: | ---: | --- |
| curve_mae_mean | 0.02425 | 0.02425 | 0.00000 | <= 0.020 (miss) |
| focus_preset_acutance_mae_mean | 0.02892 | 0.02837 | -0.00055 | <= 0.030 (pass) |
| overall_quality_loss_mae_mean | 1.20436 | 1.20436 | 0.00000 | <= 1.30 (pass) |
| mtf_abs_signed_rel_mean | 0.08671 | 0.08671 | 0.00000 | preserve |
| Small Print Acutance | 0.03173 | 0.02895 | -0.00277 | <= 0.030 (pass) |

## Scope

- Changed profile keys: `acutance_preset_input_profile_overrides`.
- Only Small Print Acutance input override added: `True`.
- Quality Loss inputs preserved: `True`.
- Reported-MTF preserved: `True`.
- Curve MAE preserved versus PR #125: `True`.

## Result

The Small Print Acutance preset-only boundary passes the targeted non-Phone Acutance gate while preserving PR #125 curve MAE, reported-MTF, overall Quality Loss, Quality Loss inputs, and release separation.

The full canonical README target still misses only `curve_mae_mean <= 0.020`; future curve work remains gated on a separate `0.15` improvement preflight.

## Release Separation

This remains canonical-target research, not a release-facing config promotion. No fitted outputs are written under golden/reference data roots or release configs.
