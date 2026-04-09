# Imatest parity direct acutance-curve anchor Quality Loss phone-override follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The previous follow-up showed that a branch-specific global quadratic can materially reduce overall Quality Loss on top of the current `phone185` Acutance branch, but it gives back the earlier phone-specific Quality Loss win.

This follow-up keeps that new global fit and adds one structured refinement:

- keep the new global Quality Loss fit for every preset
- override only the `5.5" Phone Display Quality Loss` mapping with its own fitted quadratic
- check whether that preserves the new overall gain while recovering the phone regression

## Change

This pass adds per-preset Quality Loss overrides in the shared helper path:

- `quality_loss_presets_from_acutance(..., preset_overrides=...)`

That support is wired through:

- `algo/dead_leaves.py`
- `release/deadleaf_13b10_release/algo/dead_leaves.py`
- `algo/benchmark_parity_acutance_quality_loss.py`
- `release/deadleaf_13b10_release/scripts/run_release_batch.py`

Tracked profile:

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_phoneoverride_profile.json`

Phone-only override:

- `quality_loss_preset_overrides["5.5\" Phone Display Quality Loss"]`
  - `om_ceiling = 0.8851`
  - `coefficients = [144.07521576080453, 7.994837720569423, 0.7144590420603076]`

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_quality_loss_phoneoverride_search.json`

Measured against the previous global Quality Loss fit:

- global quality fit
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 1.85163`
  - phone Quality Loss MAE `= 0.38082`
- phone-only override on top of the same branch
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 1.80933`
  - phone Quality Loss MAE `= 0.16934`

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
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_phoneoverride_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_qualityfit_phoneoverride_benchmark.json
```

## Result

This is now the strongest Quality Loss-side issue-29 branch so far.

Compared with the previous global quality-fit branch:

- `curve_mae_mean`: unchanged at `0.03776865`
- `acutance_focus_preset_mae_mean`: unchanged at `0.04249`
- `overall_quality_loss_mae_mean`: `1.85163 -> 1.80933`
- `5.5" Phone Display Quality Loss` MAE: `0.38082 -> 0.16934`

No other preset changes:

- `Computer Monitor`, `Large Print`, `Small Print`, and `UHDTV` Quality Loss MAE all stay fixed

## Interpretation

This is the first structured Quality Loss family in PR `#30` that improves the new global Quality Loss branch without giving back the phone win.

The remaining README gates are still not fully closed:

- `curve_mae_mean = 0.03776865` is still above the release-facing gate (`<= 0.020`)
- `acutance_focus_preset_mae_mean = 0.04249` is still above the release-facing gate (`<= 0.030`)
- `overall_quality_loss_mae_mean = 1.80933` is improved again but still above the release-facing gate (`<= 1.30`)

So the Quality Loss side is materially better than before, but the full canonical target still remains open overall.
