# A-model Gain-Dependent Hypothesis Follow-up

This note records the issue `#22` follow-up experiment on top of the issue `#20` gain-trend benchmark.

Reproduction artifact:

- [../artifacts/amodel_gain_hypothesis_benchmark.json](../artifacts/amodel_gain_hypothesis_benchmark.json)

Profiles compared:

1. baseline: [../release/deadleaf_13b10_release/config/parity_fit_profile.release.json](../release/deadleaf_13b10_release/config/parity_fit_profile.release.json)
2. hypothesis: [../release/deadleaf_13b10_release/config/parity_gain_noise_profile.release.json](../release/deadleaf_13b10_release/config/parity_gain_noise_profile.release.json)
3. hypothesis: [../release/deadleaf_13b10_release/config/parity_gain_shape_profile.release.json](../release/deadleaf_13b10_release/config/parity_gain_shape_profile.release.json)
4. reference: [../release/deadleaf_13b10_release/config/experimental_shape_profile.release.json](../release/deadleaf_13b10_release/config/experimental_shape_profile.release.json)

## Summary

Issue `#22` tested whether the unresolved A-model mismatch can be explained by gain-dependent noise-share scaling or by that scaling plus the gated high-frequency shape bump, while keeping the parity-fit release path fixed.

The benchmark shows only a modest improvement from those parity-path hypotheses:

- baseline `parity_fit`: focus-preset gain-delta MAE `0.01815`, series MAE `0.01863`, direction matches `3 / 20`
- `parity_gain_noise`: gain-delta MAE `0.01563`, series MAE `0.01804`, direction matches `3 / 20`
- `parity_gain_shape`: gain-delta MAE `0.01530`, series MAE `0.01877`, direction matches `3 / 20`
- `experimental_shape` reference: gain-delta MAE `0.00788`, series MAE `0.03006`, direction matches `13 / 20`

So the parity-path hypotheses do trim the gain-delta error by about `0.0025` to `0.0028`, but they do not change the overall trend direction result at all. The stronger `experimental_shape` reference remains clearly better on trend direction and gain-delta MAE, which means the missing effect is not captured by parity-fit gain-dependent noise/shape knobs alone.

The residual mismatch is still easy to see in the presets that motivated the original issue. For example:

- `Computer Monitor` reported mean gain delta is about `+0.00925`, while `parity_gain_shape` still predicts about `+0.02454`
- `UHDTV` reported mean gain delta is about `-0.00500`, while `parity_gain_shape` still predicts about `+0.01524`
- `Large Print` improves from baseline `+0.01566` to `+0.01263`, but that is still the wrong direction relative to the reported `-0.00650`

## Tradeoff

The parity gain-noise and parity gain-shape hypotheses are not strong enough to promote into the release default:

- they keep the same `3 / 20` focus-preset direction matches as the current parity-fit profile
- the gain-shape hypothesis slightly worsens overall focus-preset series MAE from `0.01863` to `0.01877` even while trimming gain-delta MAE
- the larger improvement still belongs to `experimental_shape`, but it pays for that with a much worse series MAE (`0.03006`) and changes more than the gain-dependent noise/shape knobs, so it does not isolate the issue the way this follow-up was intended to do

So the outcome for issue `#22` is: the tested gain-dependent MTF / noise hypotheses are directionally helpful but inconclusive as a release change. Further work should target the other factors that distinguish `experimental_shape`, especially the gray/texture-support path, if we want to explain the remaining `Computer Monitor` and `UHDTV` mismatch.

## Reproduction

```bash
python3 -m algo.benchmark_amodel_gain_hypotheses \
  20260318_deadleaf_13b10/output3_Amodel \
  release/deadleaf_13b10_release/config/parity_fit_profile.release.json \
  release/deadleaf_13b10_release/config/parity_gain_noise_profile.release.json \
  release/deadleaf_13b10_release/config/parity_gain_shape_profile.release.json \
  release/deadleaf_13b10_release/config/experimental_shape_profile.release.json \
  --output artifacts/amodel_gain_hypothesis_benchmark.json
```
