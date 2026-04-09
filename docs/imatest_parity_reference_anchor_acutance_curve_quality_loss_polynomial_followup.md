# Imatest parity direct acutance-curve anchor Quality Loss polynomial follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The previous follow-up showed that fitting every Quality Loss preset separately with fixed-ceiling quadratics can reduce the remaining overall Quality Loss gap to `1.44753`, while preserving the current curve and Acutance branch.

This follow-up moves to the next quality-side model family:

- keep the same `phone185` Acutance branch fixed
- keep the same fixed objective-metric ceiling
- generalize the Quality Loss mapping from a fixed quadratic to a variable-degree polynomial
- check whether a higher-order per-preset fit lowers the remaining overall Quality Loss gap enough to justify a tracked branch

## Change

This pass generalizes the shared Quality Loss helper so `quality_loss_coefficients` can contain any polynomial degree instead of exactly three quadratic coefficients.

That change is wired through the existing shared path:

- `algo/dead_leaves.py`
- `release/deadleaf_13b10_release/algo/dead_leaves.py`

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_quality_loss_polynomial_search.json`

Tracked winning profile:

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_quartic_profile.json`

Tracked winning benchmark artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_qualityfit_allpreset_quartic_benchmark.json`

## Bounded search

Measured on top of the current all-preset quadratic branch:

- all-preset quadratic
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 1.44753`
  - phone Quality Loss MAE `= 0.16934`
- all-preset cubic
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 1.33955`
  - phone Quality Loss MAE `= 0.16772`
- all-preset quartic
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 1.30895`
  - phone Quality Loss MAE `= 0.16473`

## Validation

```bash
python3 -m pytest \
  tests/test_dead_leaves_mtf_compensation.py \
  tests/test_benchmark_parity_acutance_quality_loss.py \
  tests/test_benchmark_parity_psd_mtf.py
python3 -m py_compile \
  algo/dead_leaves.py \
  release/deadleaf_13b10_release/algo/dead_leaves.py \
  algo/benchmark_parity_acutance_quality_loss.py \
  release/deadleaf_13b10_release/scripts/run_release_batch.py
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_quartic_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_qualityfit_allpreset_quartic_benchmark.json
```

## Result

This is now the strongest Quality Loss-side issue-29 branch so far.

Compared with the earlier all-preset quadratic branch:

- `curve_mae_mean`: unchanged at `0.03776865`
- `acutance_focus_preset_mae_mean`: unchanged at `0.04249`
- `overall_quality_loss_mae_mean`: `1.44753 -> 1.30895`
- `5.5" Phone Display Quality Loss` MAE: `0.16934 -> 0.16473`

Compared with the earlier phone-only override branch:

- `overall_quality_loss_mae_mean`: `1.80933 -> 1.30895`
- `5.5" Phone Display Quality Loss` MAE: `0.16934 -> 0.16473`

## Interpretation

This establishes the next quality-side boundary clearly:

- moving from quadratic to higher-order per-preset Quality Loss fits is a real win on this branch
- cubic is already materially better than quadratic
- quartic improves again and is the best bounded branch tested here

The remaining README gates are still not fully closed:

- `curve_mae_mean = 0.03776865` is still above the release-facing gate (`<= 0.020`)
- `acutance_focus_preset_mae_mean = 0.04249` is still above the release-facing gate (`<= 0.030`)
- `overall_quality_loss_mae_mean = 1.30895` is now very close, but still above the release-facing gate (`<= 1.30`)

So this pass moves the Quality Loss side very close to the release target, but the full canonical target still remains open overall.
