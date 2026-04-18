# Intrinsic After Issue 108 Next Slice

This note records the Issue `#111` developer-discovery pass after issue `#108` / PR `#109` grafted the PR `#30` observed-branch bundle onto the issue-102 topology.

## Selected Slice

- Selected slice: `issue108_computer_monitor_quality_loss_preset_boundary`
- Summary: Keep issue #108 reported-MTF parity, the issue #102 intrinsic main-acutance gains, and the existing PR #30 Quality Loss coefficients/ceilings. The next bounded implementation should isolate only the Computer Monitor downstream Quality Loss preset-family input branch, comparing an issue-108 Quality Loss input against a PR #30-compatible acutance-only/noise-share anchor input for that preset before changing any other preset family.
- Prior narrowing lineage: issue `#105` / PR `#106` / PR `#107` selected the PR30 observed-branch bundle, and issue `#108` / PR `#109` implemented it while preserving issue #102 curve/focus gains.
- Remaining gap location: reported-MTF is now equal to PR `#30`, Quality Loss coefficients are equal to PR `#30`, and the largest residual is the Computer Monitor Quality Loss preset-family input boundary.

## Comparison Table

| Record | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel | Reading |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_best_pr30_branch | 0.03679 | 0.04249 | 1.22150 | 0.03301 | 0.03694 | 0.00933 | 0.08671 | Current best PR30 branch. |
| issue108_pr30_observed_bundle_candidate | 0.03280 | 0.02892 | 1.40663 | 0.03301 | 0.03694 | 0.00933 | 0.08671 | Issue-108 bounded implementation from PR #109. |

## Residual Quality Loss Preset Deltas

| Preset | PR30 QL MAE | Issue108 QL MAE | Delta | Mean contribution |
| --- | --- | --- | --- | --- |
| Computer Monitor Quality Loss | 2.90291 | 3.56493 | +0.66202 | +0.13240 |
| Small Print Quality Loss | 0.60769 | 0.85450 | +0.24681 | +0.04936 |
| Large Print Quality Loss | 0.95482 | 1.06054 | +0.10572 | +0.02114 |
| 5.5" Phone Display Quality Loss | 0.14298 | 0.23804 | +0.09506 | +0.01901 |
| UHDTV Display Quality Loss | 1.49910 | 1.31515 | -0.18394 | -0.03679 |

## Residual Evidence

- Overall Quality Loss gap after issue #108: `+0.18513`.
- Top positive preset delta: `Computer Monitor Quality Loss` at `+0.66202`, contributing `+0.13240` to the mean gap.
- Top preset share of the net residual gap: `71.52%`.
- Reported-MTF parity with PR #30: `True`.
- Quality Loss coefficients, preset overrides, and `quality_loss_om_ceiling` match PR #30: `True`.
- Issue #108 keeps curve/focus better than PR #30: `True`.
- Computer Monitor Acutance MAE is already better than PR #30, but Computer Monitor Quality Loss MAE is worse. That separates the residual from a generic preset-acutance failure and points at the downstream Quality Loss input/mapping branch.
- UHDTV Quality Loss is already better than PR #30, so a blanket Quality Loss branch swap is not the next minimum slice.

## Remaining Pipeline Deltas

- `acutance_noise_scale_mode`: issue108='fixed', pr30='high_frequency_noise_share_quadratic'
- `intrinsic_full_reference_mode`: issue108='paired_ori_transfer', pr30='none'
- `intrinsic_full_reference_scope`: issue108='reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only', pr30='replace_all'
- `intrinsic_full_reference_transfer_mode`: issue108='radial_real_mean', pr30='magnitude_ratio'
- `matched_ori_anchor_mode`: issue108='all', pr30='acutance_only'
- `readout_mtf_compensation_mode`: issue108='sensor_aperture_sinc', pr30=None
- `readout_sensor_fill_factor`: issue108=1.5, pr30=None

## Selected Implementation Boundary

- Do not change reported-MTF/readout metrics or their issue-108 PR30 observed-branch bundle.
- Do not change the issue #102 intrinsic main-acutance branch used for curve and focus-preset Acutance.
- Do not change Quality Loss coefficients, preset overrides, or `quality_loss_om_ceiling`.
- Add only enough branch selection or instrumentation to route the Computer Monitor Quality Loss preset-family input through a PR #30-compatible downstream acutance/noise-anchor input while keeping the other Quality Loss presets on the issue-108 path for comparison.

## Excluded Routes

### `retune_quality_loss_coefficients_or_om_ceiling`

- Route: retune Quality Loss coefficients or ceilings
- Issue #108 and PR #30 already use identical global coefficients, identical preset overrides, and identical `quality_loss_om_ceiling`.
- The residual therefore comes from the Quality Loss input branch, not from a missing fitted coefficient record.

### `retune_reported_mtf_readout_again`

- Route: retune reported-MTF/readout after issue #108
- Issue #108 already matches PR #30 on `mtf_abs_signed_rel_mean`, `mtf20`, `mtf30`, and `mtf50`.
- Changing the reported-MTF branch would violate the issue-111 constraint to preserve issue-108 reported-MTF parity.

### `phone_preset_only_search`

- Route: reopen a Phone-only Quality Loss search
- Phone Quality Loss contributes only `+0.01901` to the residual mean gap, far less than the Computer Monitor contribution.
- Issue #111 explicitly excludes reopening Phone-preset-only searches.

### `uhdtv_quality_loss_preset_family`

- Route: target UHDTV Quality Loss first
- UHDTV Quality Loss is already better than PR #30 by `-0.18394`, so targeting it first would risk damaging an existing win.

### `restart_broad_intrinsic_or_observable_stack_search`

- Route: restart broad intrinsic, matched-ori, or observable-stack search
- The post-issue108 residual is already localized to downstream Quality Loss deltas after reported-MTF parity closed.
- The issue-111 handoff asks for one bounded slice from measured issue-108 deltas, not a broad family search.

## Validation Plan For The Next Implementation Issue

- Run the focused acutance/Quality Loss benchmark comparing PR #30, issue #108, and the Computer Monitor-only candidate.
- Require `Computer Monitor Quality Loss` MAE to improve materially versus issue #108 while `overall_quality_loss_mae_mean` also improves.
- Require `mtf_abs_signed_rel_mean`, `mtf20`, `mtf30`, and `mtf50` to remain equal to issue #108 / PR #30.
- Require `curve_mae_mean` and `focus_preset_acutance_mae_mean` to remain no worse than issue #108.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/config`
- Discovery outputs for this issue stay under `docs/` and `artifacts/` only.
- Do not write new fitted profiles, transfer tables, benchmark outputs, or release-facing configs under those roots.
