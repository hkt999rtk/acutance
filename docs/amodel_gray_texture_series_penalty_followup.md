# A-model Gray+Texture Series-Penalty Follow-up

This note records the issue `#27` follow-up experiment on top of the merged issue `#25` gray-plus-texture benchmark.

Reproduction artifact:

- [../artifacts/amodel_gray_texture_series_penalty_benchmark.json](../artifacts/amodel_gray_texture_series_penalty_benchmark.json)

Profiles compared:

1. baseline: [../release/deadleaf_13b10_release/config/parity_fit_profile.release.json](../release/deadleaf_13b10_release/config/parity_fit_profile.release.json)
2. prior branch: [../release/deadleaf_13b10_release/config/parity_gray_texture_shape_profile.release.json](../release/deadleaf_13b10_release/config/parity_gray_texture_shape_profile.release.json)
3. narrowed variant: [../release/deadleaf_13b10_release/config/parity_gray_texture_shape_freq110_profile.release.json](../release/deadleaf_13b10_release/config/parity_gray_texture_shape_freq110_profile.release.json)
4. narrowed variant: [../release/deadleaf_13b10_release/config/parity_gray_texture_shape_freq105_profile.release.json](../release/deadleaf_13b10_release/config/parity_gray_texture_shape_freq105_profile.release.json)
5. narrowed variant: [../release/deadleaf_13b10_release/config/parity_gray_texture_shape_nofreq_profile.release.json](../release/deadleaf_13b10_release/config/parity_gray_texture_shape_nofreq_profile.release.json)
6. reference: [../release/deadleaf_13b10_release/config/experimental_shape_profile.release.json](../release/deadleaf_13b10_release/config/experimental_shape_profile.release.json)

## Summary

Issue `#27` asked which sub-factor inside the combined gray-plus-texture branch is driving the large series-MAE penalty.

The checked-in benchmark shows that the dominant penalty comes from the retained explicit `frequency_scale = 1.17`:

- `parity_gray_texture_shape`: gain-delta MAE `0.00506`, series MAE `0.06773`, direction matches `16 / 20`
- `freq110`: gain-delta MAE `0.00653`, series MAE `0.04818`, direction matches `14 / 20`
- `freq105`: gain-delta MAE `0.00712`, series MAE `0.03340`, direction matches `14 / 20`
- `nofreq`: gain-delta MAE `0.00792`, series MAE `0.02410`, direction matches `13 / 20`
- `experimental_shape`: gain-delta MAE `0.00788`, series MAE `0.03006`, direction matches `13 / 20`

So lowering or removing the explicit frequency scale inside the gray-plus-texture branch recovers most of the series-MAE loss while giving back only part of the gain-trend improvement. The best tradeoff in this narrowed sweep is `freq105`:

- it keeps `14 / 20` direction matches, down only two groups from the full gray-plus-texture branch
- it holds gain-delta MAE at `0.00712`, still materially better than the shipped `parity_fit` baseline (`0.01815`)
- it reduces series MAE from `0.06773` to `0.03340`, which is much closer to the `experimental_shape` reference (`0.03006`)

## Tradeoff

This means issue `#25`'s series penalty is not an unavoidable cost of gray-plus-texture itself. It is mostly tied to how aggressively that branch keeps the parity-fit `frequency_scale`.

The narrowed variants behave like this:

- `freq110` preserves more of the gray-plus-texture direction benefit, but its series MAE is still high at `0.04818`
- `nofreq` nearly matches `experimental_shape` on both gain-delta MAE and series MAE, but drops to the same `13 / 20` direction-match count
- `freq105` is the current best compromise inside this branch because it stays ahead of `experimental_shape` on both gain-delta MAE and direction matches while keeping series MAE much closer to the reference than the full issue #25 branch did

So the outcome for issue `#27` is: the explicit `frequency_scale` inside the gray-plus-texture branch is the main driver of the series-MAE penalty, and a narrowed `frequency_scale = 1.05` variant is the current best experiment-only candidate for a later release-facing comparison.

## Reproduction

```bash
python3 -m algo.benchmark_amodel_gain_hypotheses \
  20260318_deadleaf_13b10/output3_Amodel \
  release/deadleaf_13b10_release/config/parity_fit_profile.release.json \
  release/deadleaf_13b10_release/config/parity_gray_texture_shape_profile.release.json \
  release/deadleaf_13b10_release/config/parity_gray_texture_shape_freq110_profile.release.json \
  release/deadleaf_13b10_release/config/parity_gray_texture_shape_freq105_profile.release.json \
  release/deadleaf_13b10_release/config/parity_gray_texture_shape_nofreq_profile.release.json \
  release/deadleaf_13b10_release/config/experimental_shape_profile.release.json \
  --output artifacts/amodel_gray_texture_series_penalty_benchmark.json
```
