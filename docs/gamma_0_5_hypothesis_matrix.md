# Gamma 0.5 Hypothesis Matrix

This note clarifies what the project currently does and does not know about the `Gamma = 0.5` field reported in the golden Imatest `Random / Dead Leaves` CSV samples.

The key constraint from [observable_target_from_golden_samples.md](./observable_target_from_golden_samples.md) is:

- `Gamma = 0.5` is directly observable in the golden CSVs
- its internal meaning inside the Imatest black box is not directly observable

## Current Evidence

The repo already contains these concrete observations:

- golden CSVs report `Gamma = 0.5`
- golden CSVs report `Color channel = R`
- the release package has both:
  - a recommended split profile with `report gamma = 0.5` and `analysis_gamma = 1.0`
  - an Imatest-parity candidate profile with `analysis_gamma = 0.5`
- current benchmarks in `algo/EXPERIMENTS.md` show:
  - full-parity analysis `gamma=0.5 + demosaic_red` gives `curve_mae_mean = 0.13126`
  - the split profile `report gamma = 0.5`, `analysis gamma = 1.0`, `bayer_mode = demosaic_red` gives `curve_mae_mean = 0.04691`
  - a sample linearization sweep under `demosaic_red` preferred `gamma = 1.0`, not `0.5`

## Hypothesis Matrix

| Hypothesis | Meaning of the CSV `Gamma = 0.5` field | Status against current evidence | Reasoning |
| --- | --- | --- | --- |
| H1 | It is the exact analysis gamma exponent applied before dead-leaves PSD/MTF estimation | ruled out as the literal default interpretation | If this were the direct internal exponent, the full-parity run would be expected to be close. Instead it degrades the full 40-sample benchmark badly and suppresses mid/high-frequency MTF too strongly. |
| H2 | It is report metadata reflecting an Imatest setting or state, while the internal dead-leaves analysis path may use a different transform | plausible | This matches the observed split between report fields and the current best-performing analysis path. |
| H3 | It is tied to OECF / tonal encoding state rather than the exact Fourier-analysis exponent used in this module | plausible | Current evidence is consistent with `Gamma = 0.5` being related to an external tonal/OECF description rather than the literal exponent used in the dead-leaves fitting path. |
| H4 | It controls some intermediate normalization or rendering stage, but not the main texture-MTF exponent directly | plausible but unproven | The benchmark failure of literal `analysis_gamma = 0.5` leaves room for gamma to matter somewhere else in the pipeline. |
| H5 | It is effectively a report-side echo of chart / project configuration and may have weak or indirect coupling to the Random/Dead Leaves core math | possible but weakly supported | The field is clearly reported, but current repo evidence does not yet isolate whether it materially influences internal calculation or is mostly descriptive. |

## What Can Already Be Ruled Out

The team can already rule out one interpretation with confidence:

- `Gamma = 0.5` should not be treated as self-evidently identical to the prototype's `analysis_gamma` parameter.

That does not prove gamma is irrelevant. It only rules out the simplistic equation:

```text
golden CSV Gamma field == dead-leaves analysis exponent
```

## What Remains Plausible

The most defensible current interpretation is:

- `Gamma = 0.5` is an observable report field
- it likely reflects report metadata, OECF-related state, or another upstream tonal setting
- it is not yet proven to be the literal exponent for the internal dead-leaves PSD/MTF path

This is why the repo currently separates:

- `report.gamma`
- `shared.analysis_gamma`

## Additional Evidence Needed

To settle the remaining hypotheses, the next useful evidence would be:

1. Controlled Imatest exports where only OECF / gamma-related settings change while the same raw input and crop are held fixed.
2. Official Imatest documentation that explicitly states what the Random/Dead Leaves report `Gamma` row means.
3. Cross-module comparison showing whether the same `Gamma` field appears identically in other Imatest reports even when the underlying analysis path differs.
4. A targeted parity experiment set that varies only the prototype's linearization model while keeping every other parity assumption fixed.

## Working Conclusion

For follow-up fitting work, the project should continue to use this rule:

- match the observable CSV field `Gamma = 0.5` at the report layer
- do not assume that this alone fixes the internal analysis path
- treat `analysis_gamma = 0.5` as one tested hypothesis, not as an already-validated fact
