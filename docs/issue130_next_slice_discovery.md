# Issue 130 Next-Slice Discovery

- Selected discovery: `post_issue128_curve_shape_or_small_print_preset_boundary`.
- Current best remains issue `#124` / PR `#125`.
- Selected next slice: `issue124_small_print_acutance_preset_only_boundary`.

## Current README Gate Status

| Gate | Value | Threshold | Delta | Status |
| --- | ---: | ---: | ---: | --- |
| curve_mae_mean | 0.02425 | 0.02000 | 0.00425 | miss |
| focus_preset_acutance_mae_mean | 0.02892 | 0.03000 | -0.00108 | pass |
| overall_quality_loss_mae_mean | 1.20436 | 1.30000 | -0.09564 | pass |
| non-phone Acutance max (Small Print Acutance) | 0.03173 | 0.03000 | 0.00173 | miss |
| 5.5" Phone Display Acutance | 0.03526 | 0.05000 | -0.01474 | pass |

## Curve Path Decision

- PR #129 curve delta versus PR #125: `+0.00122`.
- PR #129 `0.15` curve delta versus PR #125: `+0.00608`.
- Decision: do not continue broadening the issue #124 curve-only anchor mask.
- Future curve work requires a per-mixup or shape-family preflight proving `0.15` improves before a full benchmark candidate.

## Selected Next Slice

Stop direct curve-mask broadening for this handoff and split the deferred Small Print Acutance preset-only miss. The miss is small, isolated to the non-Phone Acutance gate, and can be tested without touching curve, Quality Loss coefficients, reported-MTF/readout, or release-facing configs.

- Target preset: `Small Print Acutance`.
- Current Small Print Acutance: `0.03173`.
- Gate delta: `+0.00173`.
- Slice type: `Small Print Acutance preset-only boundary`.

Minimum implementation boundary:

- Start from the issue #124 / PR #125 current-best profile.
- Restrict changes to the Small Print Acutance preset readout/input boundary.
- Do not change `curve_only_acutance_anchor_mixups` or any curve-shape branch.
- Do not change reported-MTF compensation/readout settings.
- Do not change Quality Loss coefficients or Quality Loss preset input overrides.
- Keep release-facing configs and golden/reference data untouched.

Promotion acceptance:

- `Small Print Acutance <= 0.030`, or record the slice as bounded negative/non-promotable.
- `focus_preset_acutance_mae_mean <= 0.030` remains true.
- `curve_mae_mean` remains equal to PR #125 unless the result is explicitly non-promotable.
- Reported-MTF metrics remain equal to PR #125 / PR #30.
- `overall_quality_loss_mae_mean <= 1.30` remains true and Quality Loss inputs stay unchanged.
- Release-facing configs and golden/reference data roots remain untouched.

Validation plan:

- Regenerate the Acutance/Quality Loss benchmark for the candidate profile.
- Regenerate the PSD/MTF benchmark to prove reported-MTF remains unchanged.
- Compare README gates, PR #125 deltas, and Small Print Acutance gate delta in a checked-in summary.
- Run focused summary tests plus `git diff --check`.

## Release Separation

This remains canonical-target discovery. The selected follow-up must not alter release-facing configs or write fitted outputs under golden/reference roots.
