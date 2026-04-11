# Issue 63 Empirical Linearization Follow-up

Issue: `#63`  
Refs: `#29`, `#63`  
Context from: `#31`, `#32`, `#41`, `#52`, `#56`, `#58`, `#61`, `#62`

## Why this pass

Issue `#63` asked for one bounded empirical OECF / inverse-linearization family on top of the post-`PR #62` direct-method baseline.

The repo still lacks measured Stepchart / Colorcheck OECF artifacts, so this pass stays inside the smallest source-backed empirical branch already suggested by the repo evidence:

- the current direct-method baseline still uses the older `toe_power` proxy
- the historical linearization sweep under `demosaic_red` favored `gamma = 1.0` with a tighter white percentile rather than the literal `Gamma = 0.5` interpretation
- the parity benchmark profiles did not yet expose `black_percentile` / `white_percentile`, so this issue first adds that missing schema support

That enabler is the smallest viable prerequisite slice required to express an empirical percentile-based linearization family on the current branch.

## What changed

- Added `black_percentile` and `white_percentile` profile fields to:
  - `algo/benchmark_parity_psd_mtf.py`
  - `algo/benchmark_parity_acutance_quality_loss.py`
- Added focused tests covering the new profile fields in:
  - `tests/test_benchmark_parity_psd_mtf.py`
  - `tests/test_benchmark_parity_acutance_quality_loss.py`
- Added the bounded issue-63 candidate profile:
  - `algo/deadleaf_13b10_imatest_sensor_comp_power_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_empirical_linearization_profile.json`
- Added tracked benchmark artifacts:
  - `artifacts/issue63_empirical_linearization_psd_benchmark.json`
  - `artifacts/issue63_empirical_linearization_acutance_benchmark.json`

## Candidate

Baseline from `PR #62`:

- `gamma = 0.5`
- `linearization_mode = toe_power`
- `linearization_toe = 0.12`
- implicit percentile normalization defaults (`black_percentile = 0.1`, `white_percentile = 99.9`)

Issue-63 candidate:

- `gamma = 1.0`
- `linearization_mode = power`
- `linearization_toe = 0.0`
- `black_percentile = 0.1`
- `white_percentile = 99.5`

Everything else on the newer direct-method line stays fixed.

## Result

This is a bounded mixed result, not a new default direct-method path.

Compared with the current `PR #62` direct-method baseline:

- PSD `curve_mae_mean` regresses: `0.04231237 -> 0.04943691`
- PSD signed-relative residual regresses: `0.08483351 -> 0.10525592`
- threshold MAE regresses across all reported points:
  - `MTF20`: `0.02658848 -> 0.03805077`
  - `MTF30`: `0.02903115 -> 0.04422298`
  - `MTF50`: `0.00921053 -> 0.02158925`
- Acutance `curve_mae_mean` improves: `0.03679567 -> 0.03163068`
- `acutance_focus_preset_mae_mean` improves sharply: `0.04130714 -> 0.01309645`
- `overall_quality_loss_mae_mean` regresses materially: `1.26357125 -> 1.52185412`
- explicit Phone movement is mixed:
  - Phone Acutance improves slightly: `0.01290994 -> 0.01233973`
  - Phone Quality Loss regresses: `0.16991880 -> 0.31667489`

Compared with the umbrella README gate recorded in `planning/workgraph.yaml` (`PR #30`):

- Acutance-side metrics are lower:
  - `curve_mae_mean`: `0.03163068` vs `0.03683438`
  - `acutance_focus_preset_mae_mean`: `0.01309645` vs `0.04249131`
- but `overall_quality_loss_mae_mean` is still worse: `1.52185412` vs `1.22214341`
- and the PSD / threshold side is not competitive enough to justify replacing the current direct-method baseline

## Working conclusion

This pass narrows the post-`PR #62` empirical linearization family:

- the repo now supports percentile-based empirical linearization settings in the parity profile schema
- replacing the current toe proxy with the stronger `power + gamma=1.0 + white_percentile=99.5` branch does improve Acutance alignment substantially
- but it does so by sacrificing the current direct-method PSD / MTF fit and by worsening overall Quality Loss

So the remaining parity gap is not solved by this empirical linearization branch alone on the newer direct-method line.

## Validation

- `python3 -m pytest tests/test_benchmark_parity_psd_mtf.py tests/test_benchmark_parity_acutance_quality_loss.py`
- `python3 -m algo.benchmark_parity_psd_mtf 20260318_deadleaf_13b10 algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_profile.json algo/deadleaf_13b10_imatest_sensor_comp_power_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_empirical_linearization_profile.json --output artifacts/issue63_empirical_linearization_psd_benchmark.json`
- `python3 -m algo.benchmark_parity_acutance_quality_loss 20260318_deadleaf_13b10 algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_profile.json algo/deadleaf_13b10_imatest_sensor_comp_power_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_empirical_linearization_profile.json --output artifacts/issue63_empirical_linearization_acutance_benchmark.json`
