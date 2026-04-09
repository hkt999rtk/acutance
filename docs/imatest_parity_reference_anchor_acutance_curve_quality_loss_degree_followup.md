# Imatest parity direct acutance-curve anchor Quality Loss degree follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The previous follow-up showed that a quartic all-preset Quality Loss fit nearly closed the remaining release-facing Quality Loss gate:

- `overall_quality_loss_mae_mean = 1.30895`

This follow-up bounds the next degree step directly:

- keep the same fixed curve and Acutance branch
- keep the same fixed-ceiling per-preset Quality Loss family
- benchmark the next two polynomial degrees (`5` and `6`)
- check whether that remaining `1.30895 -> 1.30` gap can be closed inside the same family

## Change

This pass does not add a new mechanism. It reuses the new variable-degree Quality Loss helper and checks in the next bounded degree follow-up:

- tracked search artifact:
  - `artifacts/imatest_parity_reference_anchor_acutance_curve_quality_loss_degree_search.json`
- tracked winning profile:
  - `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_profile.json`
- tracked winning benchmark artifact:
  - `artifacts/imatest_parity_reference_anchor_acutance_curve_qualityfit_allpreset_sextic_benchmark.json`

## Bounded search

Measured against the earlier quartic branch:

- all-preset quartic
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 1.30895`
  - phone Quality Loss MAE `= 0.16473`
- all-preset quintic
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 1.28935`
  - phone Quality Loss MAE `= 0.14553`
- all-preset sextic
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 1.22214`
  - phone Quality Loss MAE `= 0.14298`

## Validation

```bash
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_qualityfit_allpreset_sextic_benchmark.json
```

## Result

This is now the strongest Quality Loss-side issue-29 branch so far.

Compared with the earlier quartic branch:

- `curve_mae_mean`: unchanged at `0.03776865`
- `acutance_focus_preset_mae_mean`: unchanged at `0.04249`
- `overall_quality_loss_mae_mean`: `1.30895 -> 1.22214`
- `5.5" Phone Display Quality Loss` MAE: `0.16473 -> 0.14298`

This means the release-facing Quality Loss gate is now closed on this branch:

- `overall_quality_loss_mae_mean = 1.22214 <= 1.30`

## Interpretation

This follow-up changes the issue-29 boundary materially:

- Quality Loss is no longer the limiting gate on the current best branch
- the remaining README misses are now upstream, not downstream:
  - `curve_mae_mean = 0.03776865` is still above the release-facing gate (`<= 0.020`)
  - `acutance_focus_preset_mae_mean = 0.04249` is still above the release-facing gate (`<= 0.030`)

So after this pass, the next useful work should move back to the curve and focus-preset Acutance branch rather than keep tuning the Quality Loss mapping family.
