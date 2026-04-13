# Intrinsic After Issue 81 Next Slice

This note records the issue `#83` developer-discovery pass after issue `#81` / PR `#82` proved that the intrinsic line can preserve the phase-retained curve / focus gains while shrinking the downstream Quality Loss regression.

## Selected Slice

- Selected slice: `phase_retained_intrinsic_readout_reconnect_with_quality_loss_isolation`
- Summary: Keep the phase-retained intrinsic branch for both the acutance path and the reported-MTF/readout path, but leave the downstream Quality Loss path isolated on the non-intrinsic branch.
- Remaining gap location: the intrinsic branch now survives on the curve / acutance side, but the reported-MTF/readout path still diverges from that branch.

## Comparison Table

| Record | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel | Readout |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_best_pr30_branch | 0.03679 | 0.04249 | 1.22150 | 0.03301 | 0.03694 | 0.00933 | 0.08671 | Current best branch; best overall Quality Loss / readout balance. |
| issue34_intrinsic_full_reference | 0.03587 | 0.03165 | 4.56801 | 0.08284 | 0.03794 | 0.00503 | 0.20631 | First intrinsic baseline; curve and Acutance improve, Quality Loss regresses. |
| issue47_phase_retained_replace_all | 0.03280 | 0.02892 | 14.47576 | 0.08577 | 0.01789 | 0.00720 | 0.13994 | Strongest intrinsic upstream record before issue #81; Quality Loss is the blocker. |
| issue81_quality_loss_isolation_candidate | 0.03280 | 0.02892 | 8.02054 | 0.07456 | 0.07570 | 0.03462 | 0.37917 | Issue #81 keeps the intrinsic upstream gains and reduces Quality Loss, but readout metrics still lag. |

## Why The Gap Still Remains After Issue 81

- Issue #81 preserved the issue-47 intrinsic curve / focus-preset Acutance gains exactly while materially improving overall Quality Loss, so the unresolved gap is no longer the upstream intrinsic transfer itself.
- The remaining large gap versus PR #30 is concentrated in `mtf_abs_signed_rel_mean` and the MTF-threshold readouts, which means the next slice should target the readout boundary rather than reopening measured OECF or generic direct-method retunes.
- Issue #81 worsens `mtf_abs_signed_rel_mean` from 0.13994 to 0.37917 versus issue #47, even though its curve / focus metrics stay identical. That asymmetry points to the PSD/readout path rather than the intrinsic curve path.
- The quality-loss benchmark already keeps a separate `quality_loss_*` branch under `quality_loss_isolation`, so reconnecting the reported-MTF/readout path can stay bounded instead of replaying the whole intrinsic family.

## Runtime Boundary Evidence

### `algo/benchmark_parity_psd_mtf.py` (650-691)

- `compute_mtf_metrics(...)` derives the reported MTF thresholds from `compensated_mtf`.
- `acutance_curve_from_mtf(...)` and `acutance_presets_from_mtf(...)` derive curve/preset outputs from `compensated_mtf_for_acutance` instead.
- `resample_curve(...)` also publishes the PSD/readout comparison from `compensated_mtf`, so issue #81 can preserve curve/preset gains while leaving reported-MTF readouts on a different branch.

### `algo/benchmark_parity_acutance_quality_loss.py` (675-743, 920-936)

- `quality_loss_scaled_frequencies` and `quality_loss_compensated_mtf_for_acutance` are split out as a dedicated downstream Quality Loss branch.
- Under `quality_loss_isolation`, the intrinsic transfer is applied to the main acutance path, but the quality-loss-specific branch is only replaced for `replace_all`.
- That existing split means the next bounded implementation can reconnect the reported-MTF/readout path without forcing downstream Quality Loss back onto the intrinsic branch.

## Excluded Routes

### promote issue-81 scope as-is

- Issue #81 is a real positive bounded record, but its `overall_quality_loss_mae_mean` and reported-MTF/readout metrics are still far worse than the current PR #30 branch.
- Treating issue #81 as promotable without narrowing the remaining readout boundary would skip the exact unresolved technical gap this issue was created to isolate.

### reopen measured OECF

- Measured OECF already closed as a bounded negative in issue #77 / PR #78, and issue #83 explicitly forbids reopening that family.
- The issue-81 evidence points to an intrinsic-side readout boundary, not to missing measured-OECF data or retuning.

### rerun affine-registration intrinsic variant

- Affine registration was already dominated by the simpler intrinsic baseline and is explicitly out of scope for issue #83.
- The post-issue81 gap is narrower than registration choice: the surviving mismatch is the split between readout and downstream Quality Loss branches.

### restart an unbounded intrinsic family search

- Issue #83 is a developer-discovery narrowing pass, not a new multi-family search.
- The repo already contains enough evidence to name one bounded implementation slice directly, so broad family churn would be workflow regress rather than progress.

## Implementation Boundary

- Add one new intrinsic scope or equivalent code path that feeds the phase-retained intrinsic branch into `compensated_mtf` for reported-MTF/readout metrics.
- Keep the issue-81 `quality_loss_isolation` downstream routing so Quality Loss still evaluates on the non-intrinsic branch.
- Preserve `phase_correlation` registration and `radial_real_mean` transfer mode from issue #46 / PR #47 and issue #81 / PR #82.
- Do not reopen measured OECF, affine registration, or a generic intrinsic multi-family sweep in that implementation issue.

## Explicit Non-Changes

- Do not change the matched-ori anchor family or the PR #30 release-facing direct-method profile in this slice.
- Do not move fitted profiles, transfer tables, or benchmark outputs under `20260318_deadleaf_13b10` or `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`.
- Do not promote any intrinsic config into release-facing config until the next bounded implementation actually beats the current guardrails.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`
- Fitted artifact roots: `algo/*.json`, `artifacts/*.json`
- Release config roots: `release/deadleaf_13b10_release/config/*.json`
- Keep this issue's discovery outputs under `docs/` and `artifacts/` only.
- Do not write new fitted intrinsic profiles, transfer tables, or benchmark outputs under the golden/reference roots.
- Do not touch release-facing configs until a later bounded intrinsic implementation actually clears the current readme-facing guardrails.

## Acceptance For The Next Implementation Issue

- The next intrinsic scope preserves the issue-81 curve and focus-preset Acutance gains closely enough that `curve_mae_mean` and `focus_preset_acutance_mae_mean` are no worse than issue #81.
- The same implementation improves reported-MTF/readout metrics versus issue #81, with `mtf_abs_signed_rel_mean` reduced and the MTF-threshold errors moving materially toward the current PR #30 branch.
- The downstream `overall_quality_loss_mae_mean` does not regress versus issue #81.
- All new fitted intrinsic artifacts stay under `algo/` or `artifacts/`, not under golden/reference roots or release-facing config roots.

## Validation Plan For The Next Implementation Issue

- Run `python3 -m algo.benchmark_parity_psd_mtf ...` on the phase-retained intrinsic profile plus the new readout-reconnect scope.
- Run `python3 -m algo.benchmark_parity_acutance_quality_loss ...` on the same profile/scope pair to confirm Quality Loss remains isolated.
- Add focused tests around the split between `compensated_mtf`, `compensated_mtf_for_acutance`, and the quality-loss-specific branch.
