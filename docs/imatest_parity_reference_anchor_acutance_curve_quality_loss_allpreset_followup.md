# Imatest parity direct acutance-curve anchor Quality Loss all-preset follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The previous follow-up showed that a global Quality Loss fit plus a phone-only override can preserve the phone Quality Loss win while materially reducing the remaining overall Quality Loss gap.

This follow-up tests the next structured Quality Loss family:

- keep the current `phone185` Acutance branch fixed
- keep the same branch-specific fixed-ceiling Quality Loss fit family
- fit every Quality Loss preset separately instead of only overriding the phone preset
- check whether that reduces the remaining overall Quality Loss gap without giving back the current curve or Acutance branch

## Change

This pass reuses the existing per-preset Quality Loss override support and checks in a new tracked profile:

- `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_profile.json`

Preset overrides:

- `Computer Monitor Quality Loss`
  - `om_ceiling = 0.8851`
  - `coefficients = [529.6176898646592, -462.56071150600485, 118.11886744307627]`
- `5.5" Phone Display Quality Loss`
  - `om_ceiling = 0.8851`
  - `coefficients = [144.07521576080453, 7.994837720569423, 0.7144590420603076]`
- `UHDTV Display Quality Loss`
  - `om_ceiling = 0.8851`
  - `coefficients = [334.41091870576355, -167.11808057837578, 30.14801164894325]`
- `Small Print Quality Loss`
  - `om_ceiling = 0.8851`
  - `coefficients = [179.00943084893382, -78.21750380847473, 18.32377003439934]`
- `Large Print Quality Loss`
  - `om_ceiling = 0.8851`
  - `coefficients = [218.2035173980636, -117.60684300053121, 28.24969448658905]`

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_quality_loss_allpreset_search.json`

Measured against the earlier two Quality Loss-side branches:

- global quality fit
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 1.85163`
  - phone Quality Loss MAE `= 0.38082`
- phone-only override
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 1.80933`
  - phone Quality Loss MAE `= 0.16934`
- all-preset overrides
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 1.44753`
  - phone Quality Loss MAE `= 0.16934`

## Validation

```bash
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_profile.json \
  --output artifacts/imatest_parity_reference_anchor_acutance_curve_qualityfit_allpreset_benchmark.json
```

## Result

This is now the strongest Quality Loss-side issue-29 branch so far.

Compared with the earlier phone-only override branch:

- `curve_mae_mean`: unchanged at `0.03776865`
- `acutance_focus_preset_mae_mean`: unchanged at `0.04249`
- `overall_quality_loss_mae_mean`: `1.80933 -> 1.44753`
- `5.5" Phone Display Quality Loss` MAE: unchanged at `0.16934`

The extra gain comes from fitting the remaining non-phone presets separately:

- `Computer Monitor Quality Loss`: `3.78807 -> 3.13249`
- `Large Print Quality Loss`: `1.52335 -> 1.23701`
- `Small Print Quality Loss`: `1.24476 -> 0.90134`
- `UHDTV Display Quality Loss`: `2.32113 -> 1.79747`

## Interpretation

This is the first structured Quality Loss family in PR `#30` that materially improves the new overall Quality Loss branch again while fully preserving the phone Quality Loss win from the earlier phone-only override.

The README gates are still not fully closed:

- `curve_mae_mean = 0.03776865` is still above the release-facing gate (`<= 0.020`)
- `acutance_focus_preset_mae_mean = 0.04249` is still above the release-facing gate (`<= 0.030`)
- `overall_quality_loss_mae_mean = 1.44753` is much lower now, but still above the release-facing gate (`<= 1.30`)

So this pass moves the Quality Loss side substantially closer to the release target, but the full canonical target still remains open overall.
