# A-model Gain Trend Experiment

This note records the issue `#20` experiment pass for the attached `A model` gain sweep.

The issue symptom was specific: the attached `Result_Amodel_Kevin.pdf` shows an Imatest `A model` comparison where Acutance stays flat or drops slightly as `AG` rises, while the current tool output tends to rise.

Reproduction artifact:

- [../artifacts/amodel_gain_trend_benchmark.json](../artifacts/amodel_gain_trend_benchmark.json)

Profiles compared:

1. [../release/deadleaf_13b10_release/config/parity_fit_profile.release.json](../release/deadleaf_13b10_release/config/parity_fit_profile.release.json)
2. [../release/deadleaf_13b10_release/config/recommended_profile.release.json](../release/deadleaf_13b10_release/config/recommended_profile.release.json)
3. [../release/deadleaf_13b10_release/config/experimental_shape_profile.release.json](../release/deadleaf_13b10_release/config/experimental_shape_profile.release.json)
4. [../release/deadleaf_13b10_release/config/imatest_parity_profile.release.json](../release/deadleaf_13b10_release/config/imatest_parity_profile.release.json)

Dataset scope:

- `20260318_deadleaf_13b10/output3_Amodel`
- four gain levels per mixup bucket: `AG = 1, 4, 8, 15.5`
- focus presets:
  - `Computer Monitor`
  - `5.5" Phone`
  - `UHDTV`
  - `Small Print`
  - `Large Print`

## Summary

The gain-trend mismatch is reproducible in the checked-in repo data.

For the print-style preset family highlighted by the issue attachment, Imatest is slightly down or nearly flat as gain rises, while the current parity-fit release profile still slopes upward:

- `Large Print` reported mean gain delta: about `-0.0065`
- `Large Print` parity-fit predicted mean gain delta: about `+0.0157`
- `Small Print` reported mean gain delta: about `-0.0068`
- `Small Print` parity-fit predicted mean gain delta: about `+0.0091`

This is not only a parity-fit release regression:

- the retained `recommended` workaround profile shows a very similar upward gain slope
- the literal `imatest_parity` profile flips too far the other way and drives every focus preset strongly downward

Among the current checked-in alternatives, `experimental_shape_profile.release.json` is the closest gain-trend hypothesis:

- it is the best of the shipped profiles on focus-preset gain-delta MAE
- it brings `Phone`, `Small Print`, and `Large Print` much closer to the observed flat/down trend
- it still leaves `Computer Monitor` sloping up too much, so it is not a complete fix

## Working Interpretation

Issue `#20` looks like a narrower unresolved model-assumption problem, not a simple one-knob release-profile bug.

Current evidence from this benchmark suggests:

- the `Phone` geometry fix from issue `#18` did not cause the A-model gain-trend mismatch
- the older split-workaround path also carries the same basic upward-with-gain behavior
- a shaped mid/high-frequency correction helps, which points more toward unresolved gain-dependent MTF/noise interaction than toward a pure viewing-geometry problem
- the literal `gamma = 0.5` hypothesis over-corrects and is not a practical replacement

So the next fitting work should stay in experiment space and target gain-dependent MTF / noise behavior directly instead of changing the release default blindly.

## Reproduction

```bash
python3 -m algo.benchmark_amodel_gain_trend \
  20260318_deadleaf_13b10/output3_Amodel \
  release/deadleaf_13b10_release/config/parity_fit_profile.release.json \
  release/deadleaf_13b10_release/config/recommended_profile.release.json \
  release/deadleaf_13b10_release/config/experimental_shape_profile.release.json \
  release/deadleaf_13b10_release/config/imatest_parity_profile.release.json \
  --output artifacts/amodel_gain_trend_benchmark.json
```
