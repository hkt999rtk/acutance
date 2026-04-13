# Intrinsic Literal Next Slice

This note records the issue `#79` developer-discovery narrowing pass after the bounded-negative measured-OECF result in issue `#77` / PR `#78`.

## Selected Slice

- Selected slice: `phase_retained_intrinsic_quality_loss_isolation`
- Summary: Advance one bounded intrinsic/full-reference implementation slice: keep the stronger phase-retained intrinsic transfer, but isolate only downstream Quality Loss exposure instead of replaying older intrinsic variants or reopening measured OECF.
- Issue #71 context: `literal/measured_oecf_on_sensor_comp` was selected ahead of intrinsic earlier, but issue #77 closed that family as `bounded_negative`, so intrinsic is now the next source-backed route to narrow.

## Comparison Table

| Record | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 | Key Readout |
| --- | --- | --- | --- | --- | --- | --- | --- |
| current_best_pr30_branch | 0.03679 | 0.04249 | 1.22150 | 0.03301 | 0.03694 | 0.00933 | Current release-facing best branch; strongest overall guardrail balance. |
| issue34_intrinsic_full_reference | 0.03587 | 0.03165 | 4.56801 | 0.08284 | 0.03794 | 0.00503 | First intrinsic baseline: better curve / Acutance, but Quality Loss regresses hard. |
| issue37_intrinsic_acutance_only_split | 0.09800 | 0.08663 | 1.22214 | - | - | - | Existing acutance_only split keeps Quality Loss but destroys the intrinsic gains. |
| issue44_intrinsic_affine_registration | 0.03710 | 0.03259 | 4.74250 | 0.08788 | 0.03859 | 0.00505 | Affine registration is dominated by the simpler intrinsic baseline. |
| issue47_intrinsic_phase_retained_real | 0.03280 | 0.02892 | 14.47576 | 0.08577 | 0.01789 | 0.00720 | Strongest intrinsic upstream record; Quality Loss is the remaining blocker. |
| issue78_measured_oecf_negative | 0.03779 | 0.06827 | 3.02431 | 0.02674 | 0.03690 | 0.00936 | Measured OECF is already a bounded negative and should not be reopened here. |

## Why This Slice

- Issue #46 / PR #47 is the strongest checked-in intrinsic branch on curve MAE and focus-preset Acutance MAE, so the next slice should build on that upstream evidence rather than restart from weaker intrinsic variants.
- Issue #33 / PR #34 already showed that the intrinsic family's blocker is downstream Quality Loss, which makes quality-loss boundary isolation the narrowest unresolved technical point.
- Issue #37 proved that the existing `acutance_only` split is too broad: it protects Quality Loss only by giving back the intrinsic curve and Acutance gains, so the missing boundary is narrower than the current scope enum.
- Issue #77 / PR #78 already closed measured OECF as a bounded negative family, so reopening measured OECF or generic direct-method retunes would ignore the current source-backed ranking.

## Excluded Routes

### replay the existing acutance_only intrinsic scope

- Issue #37 already showed that `acutance_only` protects Quality Loss only by losing the intrinsic family's curve and Acutance benefit, so replaying it would not narrow the unresolved boundary.
- Because this scope is already checked in, rerunning it would be workflow churn rather than a new bounded implementation slice.

### revisit the affine-registration intrinsic variant

- The affine-registration intrinsic variant is worse than the original issue-34 intrinsic baseline on curve and focus-preset Acutance while still regressing Quality Loss.
- That makes registration refinement a dominated branch rather than the next rational bounded slice.

### reopen measured OECF or generic direct-method retunes

- Issue #71 selected measured OECF before intrinsic, and issue #77 / PR #78 then closed that family as a bounded negative result.
- Without a new source basis, reopening measured OECF or generic direct-method retunes would contradict both issue #71 and issue #79 scope constraints.

## Implementation Boundary

- Add one new intrinsic scope or equivalent code path between `replace_all` and `acutance_only` in the parity benchmarks.
- Keep the issue-47 phase-retained intrinsic transfer active for PSD and Acutance evaluation.
- Route Quality Loss evaluation through the non-intrinsic compensated MTF path so the next issue isolates only the downstream Quality Loss exposure.
- Do not reopen measured OECF, affine registration, or generic direct-method retunes in that implementation issue.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`
- Fitted artifact roots: `algo/*.json`, `artifacts/*.json`
- Release config roots: `release/deadleaf_13b10_release/config/*.json`
- Do not write fitted intrinsic profiles, transfer tables, or benchmark outputs under the golden/reference roots.
- Keep issue-79 discovery outputs and the next intrinsic implementation artifacts under `algo/` and `artifacts/` only.
- Do not add or modify release-facing configs until an intrinsic slice beats the current tracked guards rather than only improving an internal sub-metric.

## Acceptance For The Next Implementation Issue

- The new scope leaves the phase-retained intrinsic curve / Acutance path intact enough that `curve_mae_mean` and `focus_preset_acutance_mae_mean` remain no worse than the older issue-34 intrinsic baseline.
- The same implementation materially reduces `overall_quality_loss_mae_mean` versus issue #46 / PR #47.
- All new fitted intrinsic artifacts remain under `algo/` or `artifacts/`, not under golden/reference roots.
- The implementation issue reruns focused PSD and acutance/quality-loss parity benchmarks for the selected intrinsic profile.

## Validation Plan For The Next Implementation Issue

- Run `python3 -m algo.benchmark_parity_psd_mtf ...` on the phase-retained intrinsic profile plus the new scope.
- Run `python3 -m algo.benchmark_parity_acutance_quality_loss ...` on the same profile/scope pair.
- Add focused tests around the new intrinsic scope so Quality Loss routing is isolated without regressing the PSD/Acutance path.
