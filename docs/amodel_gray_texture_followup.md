# A-model Gray / Texture-Support Follow-up

This note records the issue `#25` follow-up experiment on top of the merged issue `#22` gain-hypothesis benchmark.

Reproduction artifact:

- [../artifacts/amodel_gray_texture_benchmark.json](../artifacts/amodel_gray_texture_benchmark.json)

Profiles compared:

1. baseline: [../release/deadleaf_13b10_release/config/parity_fit_profile.release.json](../release/deadleaf_13b10_release/config/parity_fit_profile.release.json)
2. prior hypothesis: [../release/deadleaf_13b10_release/config/parity_gain_shape_profile.release.json](../release/deadleaf_13b10_release/config/parity_gain_shape_profile.release.json)
3. factor isolate: [../release/deadleaf_13b10_release/config/parity_gray_shape_profile.release.json](../release/deadleaf_13b10_release/config/parity_gray_shape_profile.release.json)
4. factor isolate: [../release/deadleaf_13b10_release/config/parity_texture_shape_profile.release.json](../release/deadleaf_13b10_release/config/parity_texture_shape_profile.release.json)
5. factor isolate: [../release/deadleaf_13b10_release/config/parity_gray_texture_shape_profile.release.json](../release/deadleaf_13b10_release/config/parity_gray_texture_shape_profile.release.json)
6. reference: [../release/deadleaf_13b10_release/config/experimental_shape_profile.release.json](../release/deadleaf_13b10_release/config/experimental_shape_profile.release.json)

## Summary

Issue `#25` asked whether factors outside the already-tested parity gain-noise / gain-shape knobs explain more of the remaining A-model mismatch, especially the `Computer Monitor` and `UHDTV` presets.

The checked-in benchmark shows:

- baseline `parity_fit`: gain-delta MAE `0.01815`, series MAE `0.01863`, direction matches `3 / 20`
- prior `parity_gain_shape`: gain-delta MAE `0.01530`, series MAE `0.01877`, direction matches `3 / 20`
- `parity_gray_shape`: gain-delta MAE `0.01025`, series MAE `0.03119`, direction matches `3 / 20`
- `parity_texture_shape`: gain-delta MAE `0.01078`, series MAE `0.11212`, direction matches `3 / 20`
- `parity_gray_texture_shape`: gain-delta MAE `0.00506`, series MAE `0.06773`, direction matches `16 / 20`
- `experimental_shape` reference: gain-delta MAE `0.00788`, series MAE `0.03006`, direction matches `13 / 20`

So the meaningful explanatory factor is not `gray` alone or `texture_support_scale` alone. Each one trims gain-delta MAE, but both leave the direction result stuck at `3 / 20`. The combined `gray + texture_support_scale` path is the actual step change:

- it improves gain-delta MAE by about `0.01309` vs the shipped parity-fit baseline
- it improves direction matches by `+13`, reaching `16 / 20`
- it beats the existing `experimental_shape` reference on both gain-delta MAE and direction-match count

## Residual Mismatch

The combined `gray + texture_support_scale` path explains much more of the remaining trend direction problem, but not without cost.

Examples versus the shipped parity-fit baseline:

- `Computer Monitor` predicted mean gain delta drops from about `+0.02905` to `+0.01944`, moving closer to the reported `+0.00925`, but still not close enough
- `UHDTV` predicted mean gain delta drops from about `+0.01865` to `+0.00129`, much closer to the reported `-0.00500`, and direction matches improve by `2 / 4`
- `Large Print` predicted mean gain delta flips from about `+0.01566` to `-0.00384`, much closer to the reported `-0.00650`, and direction matches improve by `3 / 4`

## Tradeoff

The `gray + texture_support_scale` factor pair is strong enough to explain more of the remaining mismatch than issue `#22` did, but it is still experiment-only:

- its series MAE rises from `0.01863` on `parity_fit` to `0.06773`
- that series-MAE tradeoff is worse than the existing `experimental_shape` reference (`0.03006`) even though the combined factor pair wins on gain-delta MAE and direction count
- `gray` alone and `texture_support_scale` alone are both rejected as sufficient explanations because neither changes the direction-match ceiling

So the outcome for issue `#25` is: the combined gray / texture-support path explains substantially more of the remaining A-model gain-trend mismatch, but it is not release-safe in its current form because the overall series error gets much worse. The next fitting work should treat `gray + texture_support_scale` as the current best explanatory branch and then narrow down what part of that branch is driving the series-MAE penalty.

## Reproduction

```bash
python3 -m algo.benchmark_amodel_gain_hypotheses \
  20260318_deadleaf_13b10/output3_Amodel \
  release/deadleaf_13b10_release/config/parity_fit_profile.release.json \
  release/deadleaf_13b10_release/config/parity_gain_shape_profile.release.json \
  release/deadleaf_13b10_release/config/parity_gray_shape_profile.release.json \
  release/deadleaf_13b10_release/config/parity_texture_shape_profile.release.json \
  release/deadleaf_13b10_release/config/parity_gray_texture_shape_profile.release.json \
  release/deadleaf_13b10_release/config/experimental_shape_profile.release.json \
  --output artifacts/amodel_gray_texture_benchmark.json
```
