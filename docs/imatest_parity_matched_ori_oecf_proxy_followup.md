# Imatest Parity Matched-ORI OECF Proxy Follow-up

Issue: `#31`  
Refs: `#29`, PR `#30`

## Why this pass

Issue `#31` asked for the next source-backed family to test after the registration and reference-anchor sweep in PR `#30` plateaued short of the README gate.

The black-box research note still lists OECF-driven linearization as a missing family, but the repo had only ruled out:

- literal `analysis_gamma = 0.5`
- generic inverse `sRGB`
- generic inverse `Rec.709`
- a simple `toe_power` proxy

So this pass tested a stronger dataset-constrained OECF proxy instead of continuing local curve or preset retuning:

- keep the current best `#30` branch intact
- derive a bounded quantile-to-quantile tone curve from each processed capture to its matched `ori` capture
- apply that tone curve after the existing `toe_power` normalization and before dead-leaves estimation

## What changed

- Added matched-`ori` quantile transfer helpers in `algo/parity_benchmark_common.py`.
- Added new profile fields in both parity benchmark drivers:
  - `matched_ori_oecf_reference`
  - `matched_ori_oecf_strength`
  - `matched_ori_oecf_quantiles`
- Added unit coverage for the new transfer-curve helper and profile schema.
- Added tracked profile:
  - `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_matched_ori_oecf_proxy_profile.json`
- Added tracked benchmark artifact:
  - `artifacts/imatest_parity_matched_ori_oecf_proxy_benchmark.json`

## Result

The matched-`ori` OECF proxy does not improve the current best `#30` branch.

Current best branch from PR `#30`:

- `curve_mae_mean = 0.03683438`
- `acutance_focus_preset_mae_mean = 0.04249131`
- `overall_quality_loss_mae_mean = 1.22214341`

Matched-`ori` OECF proxy benchmark:

- `curve_mae_mean = 0.03683438`
- `acutance_focus_preset_mae_mean = 0.04249131`
- `overall_quality_loss_mae_mean = 1.22214341`

That means this formulation is a no-op for the end-to-end benchmark.

## Why it collapsed

A representative matched pair already shows why the benchmark does not move much after the existing `toe_power` normalization:

- processed quantiles:
  - `[0.327327, 0.493524, 0.696868, 0.756406, 0.803041, 0.852110, 0.898208, 0.938100]`
- matched `ori` quantiles:
  - `[0.327327, 0.503318, 0.689098, 0.753038, 0.799396, 0.848527, 0.894965, 0.939409]`
- deltas stay within about `-0.0078` to `+0.0098`

So once the current branch already applies percentile normalization plus `toe_power`, this quantile-matched proxy does not introduce a materially new tonal family. It mostly reproduces the same normalized ordering with tiny local shifts.

## Working conclusion

This is not the next useful family to keep pushing inside issue `#31`.

- It is more source-backed than a generic `sRGB` / `Rec.709` swap.
- But in this matched-`ori` quantile formulation it collapses to near-identity and does not move the README gate at all.
- That makes it a poor use of time compared with the remaining missing family that can still change the model materially: a stronger intrinsic / full-reference method with explicit reference-image warp and phase-retaining correction, rather than another bounded OECF proxy.

## Validation

- `python3 -m pytest tests/test_dead_leaves_mtf_compensation.py tests/test_benchmark_parity_acutance_quality_loss.py`
- `python3 -m py_compile algo/parity_benchmark_common.py algo/benchmark_parity_psd_mtf.py algo/benchmark_parity_acutance_quality_loss.py`
- `python3 -m algo.benchmark_parity_acutance_quality_loss 20260318_deadleaf_13b10 algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_matched_ori_oecf_proxy_profile.json --output artifacts/imatest_parity_matched_ori_oecf_proxy_benchmark.json`
