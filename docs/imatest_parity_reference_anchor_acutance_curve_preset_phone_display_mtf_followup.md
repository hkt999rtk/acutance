# Imatest parity direct acutance-curve anchor preset phone-display MTF follow-up

Issue: [#29](https://github.com/hkt999rtk/acutance/issues/29)

PR: [#30](https://github.com/hkt999rtk/acutance/pull/30)

## Goal

The previous follow-up bounded the local preset-side strength-curve neighborhood and showed that it only trades a tiny amount of phone Acutance against phone Quality Loss.

This follow-up moves to a different preset-side model family:

- keep the current `phone185` correction branch fixed
- keep the existing release-style phone viewing-distance override
- add a phone-display MTF assumption on the `5.5" Phone Display Acutance` preset itself

## Change

The benchmark path already supports per-preset overrides through `acutance_preset_overrides`.

This pass benchmarks three bounded phone-display MTF variants on top of the current `phone185` branch:

- `display_mtf_c50_cpd = 22`
- `display_mtf_c50_cpd = 20`
- `display_mtf_c50_cpd = 16`

Each variant also keeps:

- `5.5" Phone Display viewing_distance_cm = 25.55`

## Bounded search

Tracked search artifact:

- `artifacts/imatest_parity_reference_anchor_acutance_curve_preset_phone_display_mtf_search.json`

Measured against the current best tracked branch (`phone185`):

- baseline `phone185`
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 2.33309`
  - phone Acutance / Quality Loss MAE `= 0.01380 / 0.29987`
- phone display `22 cpd`
  - `acutance_focus_preset_mae_mean = 0.06090`
  - `overall_quality_loss_mae_mean = 2.79584`
  - phone Acutance / Quality Loss MAE `= 0.10582 / 2.61364`
- phone display `20 cpd`
  - `acutance_focus_preset_mae_mean = 0.06378`
  - `overall_quality_loss_mae_mean = 2.88990`
  - phone Acutance / Quality Loss MAE `= 0.12026 / 3.08394`
- phone display `16 cpd`
  - `acutance_focus_preset_mae_mean = 0.07209`
  - `overall_quality_loss_mae_mean = 3.19129`
  - phone Acutance / Quality Loss MAE `= 0.16179 / 4.59087`

Across the whole bounded search, the observable curve branch stayed fixed:

- `curve_mae_mean = 0.03776865`

## Validation

```bash
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  /tmp/acutance_phone_display_probe/phone185_display22.json \
  --output /tmp/acutance_phone_display_probe/phone185_display22_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  /tmp/acutance_phone_display_probe/phone185_display20.json \
  --output /tmp/acutance_phone_display_probe/phone185_display20_benchmark.json
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  /tmp/acutance_phone_display_probe/phone185_display16.json \
  --output /tmp/acutance_phone_display_probe/phone185_display16_benchmark.json
```

## Result

This is a strongly negative result.

Within this preset-definition family:

- every tested phone-display MTF override makes the phone preset much worse
- overall Quality Loss also gets materially worse
- even the mildest tested branch (`22 cpd`) is far worse than the current `phone185` baseline

So the best tracked branch for issue `#29` remains the earlier `phone185` preset-side `delta_power` branch.

## Interpretation

This rules out another preset-side family:

- the remaining release-facing gap is not explained by missing phone-display blur in the preset definition
- reintroducing phone display MTF on top of the current `phone185` branch strongly over-corrects the phone preset
- the next useful step should move away from local phone-preset definition tuning and toward a different Quality Loss or preset-side model family
