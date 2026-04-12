# Issue 67 Readout-Policy Follow-up

Issue: `#67`  
Refs: `#29`, `#67`  
Context from: `#52`, `#53`, `#54`, `#55`, `#56`, `#57`, `#65`, `#66`

## Why this pass

Issue `#67` asked for one bounded readout-policy family on top of the current direct-method branch after `PR #66`.

This is the cleanest last direct-method slice still explicitly named in `algo/README.md`:

- the README still lists the remaining direct-method gap as `frequency mapping / ROI policy / readout policy`
- the same README also records prior readout-policy benchmarking and warns that readout policy is not a good default repair path

So this issue tests the narrowest possible readout-policy family that the repo already called out:

- baseline: `readout_smoothing_window = 1`, `readout_interpolation = linear`
- candidate: `readout_smoothing_window = 7`, `readout_interpolation = linear`

No broader direct-method retuning is reopened here.

## What changed

- Added `readout_smoothing_window` / `readout_interpolation` profile-schema support to:
  - `algo/benchmark_parity_psd_mtf.py`
  - `algo/benchmark_parity_acutance_quality_loss.py`
- Wired those fields through the shared `estimate_dead_leaves_mtf(...)` readout path in `algo/dead_leaves.py`, so the issue-67 profile now exercises a real threshold-readout change instead of metadata-only profile fields.
- Added focused tests covering the new profile fields in:
  - `tests/test_benchmark_parity_psd_mtf.py`
  - `tests/test_benchmark_parity_acutance_quality_loss.py`
- Added the bounded issue-67 candidate profile:
  - `algo/deadleaf_13b10_imatest_sensor_comp_power_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_chart_prior_slope_m006_anchored_hf_psd_roi_reference_only_empirical_linearization_readout7_profile.json`
- Added tracked benchmark artifacts:
  - `artifacts/issue67_readout_policy_psd_benchmark.json`
  - `artifacts/issue67_readout_policy_acutance_benchmark.json`

## Candidate

Baseline from `PR #66`:

- current issue-65 direct-method profile
- `readout_smoothing_window = 1`
- `readout_interpolation = linear`

Issue-67 candidate:

- keeps the full `PR #66` profile fixed
- changes only:
  - `readout_smoothing_window = 7`
  - `readout_interpolation = linear`

This is the exact bounded readout-policy branch already highlighted in `algo/README.md`.

## Result Versus PR 66

This closes as a bounded negative result.

Compared with the merged `PR #66` profile:

- PSD `curve_mae_mean` is unchanged: `0.04982241 -> 0.04982241`
- PSD signed-relative residual is unchanged: `0.13670371 -> 0.13670371`
- threshold MAE gets worse across the board:
  - `MTF20`: `0.04277803 -> 0.04351442`
  - `MTF30`: `0.04902804 -> 0.04947438`
  - `MTF50`: `0.02158925 -> 0.02450493`
- Acutance `curve_mae_mean` is unchanged: `0.03189952 -> 0.03189952`
- `acutance_focus_preset_mae_mean` is unchanged: `0.01306828 -> 0.01306828`
- `overall_quality_loss_mae_mean` is unchanged: `1.53177498 -> 1.53177498`

So on the current direct-method branch, the bounded readout-policy change does not improve the lower-layer tradeoff at all. It only changes threshold extraction, and in this branch it changes it for the worse.

The unchanged PSD and Acutance / Quality Loss metrics are expected here because this family only changes threshold readout policy. After the code-path fix on this branch, the benchmark still reproduces the same issue-67 conclusion: the readout settings are exercised for threshold extraction, but they do not move the underlying PSD or Acutance-side fit.

## Relation To Existing README Evidence

The README already recorded a cautionary result on an older branch:

- `window=7, interpolation=linear` slightly improved `MTF50`
- but it also worsened `MTF20`

Issue `#67` was still worth testing because that earlier evidence lived on a different direct-method surface, before the current ROI / frequency-mapping / inverse-linearization descendants.

The current result is even weaker:

- the same bounded readout-policy family no longer improves `MTF50`
- it now regresses `MTF20`, `MTF30`, and `MTF50`
- and it leaves the Acutance / Quality Loss side completely unchanged

That makes the repo's prior caution stronger, not weaker.

## Result Versus Umbrella Gate

The umbrella README gate in `planning/workgraph.yaml` still points to `PR #30`:

- `curve_mae_mean = 0.03683438`
- `acutance_focus_preset_mae_mean = 0.04249131`
- `overall_quality_loss_mae_mean = 1.22214341`
- `phone_display_acutance_mae = 0.01380215`

Compared with that gate, the issue-67 candidate still has:

- lower Acutance-side metrics
  - `curve_mae_mean = 0.03189952`
  - `acutance_focus_preset_mae_mean = 0.01306828`
  - `5.5\" Phone Display Acutance = 0.01233877`
- but much worse overall Quality Loss:
  - `overall_quality_loss_mae_mean = 1.53177498`
- and a non-competitive PSD / threshold side

So this readout-policy family does not move the repo closer to the canonical observable target enough to justify more work inside the current direct-method line.

## Working Conclusion

This issue closes the remaining explicitly named readout-policy family inside the current direct-method branch:

- it is justified by existing repo evidence because `algo/README.md` names readout policy explicitly and already identifies the narrow `window=7, linear` branch
- the issue remains bounded because it changes only the threshold readout policy and leaves ROI, frequency mapping, chart/sensor, ISP, and inverse-linearization settings fixed
- the result is a bounded negative outcome

On the current branch, readout policy is not just a weak default repair path; it is effectively exhausted as a useful bounded direct-method follow-up.

## Validation

- `python3 -m pytest tests/test_benchmark_parity_psd_mtf.py tests/test_benchmark_parity_acutance_quality_loss.py`
- `python3 -m algo.benchmark_parity_psd_mtf 20260318_deadleaf_13b10 algo/deadleaf_13b10_imatest_sensor_comp_power_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_chart_prior_slope_m006_anchored_hf_psd_roi_reference_only_empirical_linearization_profile.json algo/deadleaf_13b10_imatest_sensor_comp_power_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_chart_prior_slope_m006_anchored_hf_psd_roi_reference_only_empirical_linearization_readout7_profile.json --output artifacts/issue67_readout_policy_psd_benchmark.json`
- `python3 -m algo.benchmark_parity_acutance_quality_loss 20260318_deadleaf_13b10 algo/deadleaf_13b10_imatest_sensor_comp_power_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_chart_prior_slope_m006_anchored_hf_psd_roi_reference_only_empirical_linearization_profile.json algo/deadleaf_13b10_imatest_sensor_comp_power_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_chart_prior_slope_m006_anchored_hf_psd_roi_reference_only_empirical_linearization_readout7_profile.json --output artifacts/issue67_readout_policy_acutance_benchmark.json`
