# Imatest parity direct acutance-curve anchor preset-side strength-curve follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The previous follow-up ruled out preset-side `clip_lo` shaping as a useful local explanation on top of the current `phone185` best branch.

This follow-up tests the next nearby preset-side family without adding new code:

- keep the `phone185` branch fixed
- reduce the preset-side phone-region direct Acutance anchor strength
- check whether that strength curve can improve the remaining phone and overall release-facing metrics without giving back too much Quality Loss

## Change

The current best tracked branch already carries a preset-side strength curve:

- `matched_ori_acutance_preset_strength_curve_values = [1.0, 1.0, 0.85, 0.45, 0.45]`

This pass benchmarks a bounded neighborhood around that phone-region tail:

- `0.43 / 0.43`
- `0.42 / 0.42`
- `0.42 / 0.42` with a slightly softer mid point `0.88`
- `0.40 / 0.40`
- `0.35 / 0.35`

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_preset_strength_curve_search.json`

Measured against the current best tracked branch (`phone185`):

- baseline `phone185`
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 2.33309`
  - phone Acutance / Quality Loss MAE `= 0.01380 / 0.29987`
- phone tail `0.43 / 0.43`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 2.33311`
  - phone Acutance / Quality Loss MAE `= 0.01380 / 0.29997`
- phone tail `0.42 / 0.42`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 2.33312`
  - phone Acutance / Quality Loss MAE `= 0.01380 / 0.30002`
- phone tail `0.42 / 0.42` with mid `0.88`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 2.33312`
  - phone Acutance / Quality Loss MAE `= 0.01380 / 0.30001`
- phone tail `0.40 / 0.40`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 2.33314`
  - phone Acutance / Quality Loss MAE `= 0.01379 / 0.30011`
- phone tail `0.35 / 0.35`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 2.33318`
  - phone Acutance / Quality Loss MAE `= 0.01380 / 0.30035`

Across the whole bounded search, the observable curve branch stayed fixed:

- `curve_mae_mean = 0.03776865`

## Validation

```bash
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  /tmp/acutance_strength_probe/phone185_strength043.json \
  --output /tmp/acutance_strength_probe/phone185_strength043_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  /tmp/acutance_strength_probe/phone185_strength042.json \
  --output /tmp/acutance_strength_probe/phone185_strength042_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  /tmp/acutance_strength_probe/phone185_strength042_mid088.json \
  --output /tmp/acutance_strength_probe/phone185_strength042_mid088_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  /tmp/acutance_strength_probe/phone185_strength040.json \
  --output /tmp/acutance_strength_probe/phone185_strength040_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  /tmp/acutance_strength_probe/phone185_strength035.json \
  --output /tmp/acutance_strength_probe/phone185_strength035_benchmark.json
```

## Result

This is another bounded negative result.

Within this preset-side strength-curve neighborhood:

- every phone-tail reduction improves phone Acutance slightly
- every phone-tail reduction worsens phone Quality Loss slightly
- none of the bounded probes beats the current `phone185` branch on the joint release-facing trade-off

So the best tracked branch for issue `#29` remains the earlier `phone185` preset-side `delta_power` branch.

## Interpretation

This rules out another nearby preset-side local explanation:

- the remaining release-facing gap is not solved by simply reducing the phone-region preset-side anchor strength
- this family behaves like a small one-dimensional trade between phone Acutance and phone Quality Loss
- the next useful step should move to a different preset-side or Quality Loss model family rather than more local preset-side strength retuning
