# Issue 136 Curve Preflight Discovery

- Result: `technical_discovery_no_source_backed_next_curve_slice`.
- Current best: issue `#132` / PR `#135`.
- Current profile: `algo/issue132_small_print_acutance_parity_input_profile.json`.
- Decision: `no_source_backed_current_topology_015_preflight_found`.

## README Gate Status

| Gate | Value | Threshold | Delta | Status |
| --- | ---: | ---: | ---: | --- |
| curve_mae_mean | 0.02425 | 0.02000 | 0.00425 | miss |
| focus_preset_acutance_mae_mean | 0.02837 | 0.03000 | -0.00163 | pass |
| overall_quality_loss_mae_mean | 1.20436 | 1.30000 | -0.09564 | pass |
| non-phone Acutance max | 0.02895 | 0.03000 | -0.00105 | pass |

## 0.15 Preflight Evidence

- Current PR #135 `0.15` curve MAE: `0.02938`.
- PR #129 direct `0.15` anchor-mask broadening moved `0.15` to `0.03546` (`+0.00608`), so it remains negative evidence.

| Artifact | Profile | 0.15 MAE | Delta vs #135 | Curve MAE | QL MAE | Classification |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `artifacts/parity_acutance_quality_loss_benchmark.json` | `algo/deadleaf_13b10_parity_psd_mtf_profile.json` | 0.02567 | -0.00370 | 0.01970 | 1.27621 | `fitted_release_workaround_not_source_backed_current_topology` |
| `artifacts/issue63_empirical_linearization_acutance_benchmark.json` | `algo/deadleaf_13b10_imatest_sensor_comp_power_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_empirical_linearization_profile.json` | 0.01743 | -0.01195 | 0.03163 | 1.52185 | `historical_non_current_topology_with_protected_gate_regression` |

Rejected apparent improvements:

- The release parity-fit profile numerically improves `0.15`, but issue #29 explicitly keeps that profile separated as a workaround rather than a source-backed canonical model-family slice.
- The historical empirical-linearization profile improves `0.15`, but it is not a post-PR #135 current-topology preflight and fails the current overall Quality Loss gate.

## Decision

The only current-topology `0.15` implementation evidence is PR #129, which worsened `0.15`. Older apparent improvements are either fitted workaround profiles or non-current-topology artifacts that fail protected issue #136 constraints, so they do not satisfy the source-backed preflight gate.

Required evidence before curve work resumes:

- A post-PR #135 current-topology preflight artifact that lowers `0.15` versus 0.029378599163150443.
- A source-backed model-family explanation for that preflight, not a fitted release-workaround graft.
- Preservation, or explicitly measured bounded tradeoff, for reported-MTF, focus-preset Acutance, overall Quality Loss, non-Phone Acutance, and release separation.

## Release Separation

This discovery does not promote fitted outputs into golden/reference roots or release-facing configs.
