# Imatest parity direct acutance-curve anchor Quality Loss fit follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The previous preset-side and preset-definition follow-ups ruled out more local phone-oriented tuning on top of the current `phone185` Acutance branch.

This follow-up moves to the next quality-side model family:

- keep the current `phone185` Acutance branch fixed
- fit a branch-specific global quadratic Quality Loss mapping on top of those Acutance outputs
- check whether the remaining release-facing Quality Loss gap is partly in the mapping itself rather than only in the upstream Acutance branch

## Change

This pass adds an export path to `algo.benchmark_parity_acutance_quality_loss`:

- `--include-quality-loss-records`

That flag writes the per-sample predicted Acutance and reported Quality Loss rows needed to fit a branch-specific global quadratic.

Using the exported `phone185` records, two bounded variants were fit:

- fixed ceiling fit:
  - `quality_loss_om_ceiling = 0.8851`
  - `quality_loss_coefficients = [37.240228358776136, 26.54550669779819, 0.4538662637619741]`
- free ceiling fit:
  - `quality_loss_om_ceiling = 0.9819695909222319`
  - `quality_loss_coefficients = [37.24022835877618, 19.33061532386791, -1.7681343229066284]`

Tracked profile:

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_profile.json`

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_quality_loss_fit_search.json`

Measured against the current best tracked branch (`phone185`):

- baseline `phone185`
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 2.33309`
  - phone Quality Loss MAE `= 0.29987`
- fixed ceiling quality fit
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 1.85163`
  - phone Quality Loss MAE `= 0.38082`
- free ceiling quality fit
  - numerically the same benchmark result as the fixed-ceiling fit

## Validation

```bash
python3 -m pytest \
  tests/test_benchmark_parity_acutance_quality_loss.py \
  tests/test_benchmark_parity_psd_mtf.py \
  tests/test_dead_leaves_mtf_compensation.py
python3 -m py_compile algo/benchmark_parity_acutance_quality_loss.py
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_delta_curve_phone185_profile.json \
  --include-quality-loss-records \
  --output /tmp/phone185_quality_loss_records.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_qualityfit_benchmark.json
```

## Result

This is the strongest Quality Loss-side issue-29 branch so far.

Compared with the earlier `phone185` branch:

- `curve_mae_mean`: unchanged at `0.03776865`
- `acutance_focus_preset_mae_mean`: unchanged at `0.04249`
- `overall_quality_loss_mae_mean`: `2.33309 -> 1.85163`

The gain is not uniform:

- `Large Print`, `Small Print`, and `UHDTV` Quality Loss improve materially
- `Computer Monitor` Quality Loss gets slightly worse
- `5.5" Phone Display Quality Loss` also gets worse (`0.29987 -> 0.38082`)

## Interpretation

This establishes a new quality-side boundary:

- a branch-specific global quadratic remap can materially reduce the remaining overall Quality Loss gap without touching the current curve or Acutance branch
- freeing the OM ceiling is unnecessary here; the fixed-ceiling fit reaches the same benchmark result
- the remaining issue-29 work is now more clearly split:
  - the upstream curve / Acutance branch still controls the Acutance gates
  - the Quality Loss mapping itself still contains a real global error term that can be reduced

This branch still does not close the full README target:

- `curve_mae_mean = 0.03776865` is still above the release-facing gate (`<= 0.020`)
- `acutance_focus_preset_mae_mean = 0.04249` is still above the release-facing gate (`<= 0.030`)
- `overall_quality_loss_mae_mean = 1.85163` is improved materially but still above the release-facing gate (`<= 1.30`)
