# Parity Input Pipeline Candidates

This note locks the current parity input pipeline for golden-sample fitting work under issue `#10`.

The question here is narrower than the earlier Gamma and black-box research issues:

- hold the current analysis frame fixed
- compare the implemented input-pipeline candidates that act on the raw image before dead-leaves analysis
- choose one current best parity-valid path for downstream fitting

## Fixed Comparison Frame

The benchmark in [../artifacts/parity_input_pipeline_benchmark.json](../artifacts/parity_input_pipeline_benchmark.json) uses:

- dataset: `20260318_deadleaf_13b10`
- calibration: `algo/deadleaf_13b10_psd_calibration.json`
- observed report target still anchored to:
  - `Gamma = 0.5`
  - `Color channel = R`
- fixed analysis frame for this comparison:
  - `analysis_gamma = 1.0`
  - `bayer_pattern = RGGB`
  - `roi_source = fixed`

Why this frame:

- issue `#3` already showed that the observed CSV `Gamma = 0.5` field should not be treated as self-evidently identical to the prototype's analysis exponent
- issue `#10` is about locking the input path, not reopening Gamma semantics
- holding `analysis_gamma` fixed avoids mixing two latent-variable questions into one benchmark

## Candidate Set

Implemented candidates currently exercised in repo code:

| Candidate | Kept as parity-valid? | Meaning |
| --- | --- | --- |
| `gray` | no | diagnostic grayscale control using the raw plane directly |
| `demosaic_red` | yes | full Bayer demosaic, then use the red plane |
| `raw_red_upsampled` | yes | sample the raw red sites only, then upsample back to full size |

There is no third currently implemented, explainable R-channel path in the repo beyond `demosaic_red` and `raw_red_upsampled`.

## Full-Dataset Result Summary

| Candidate | `curve_mae_mean` | mean abs MTF signed-rel residual | `overall_quality_loss_mae_mean` | parity-valid |
| --- | --- | --- | --- | --- |
| `gray` | `0.04452` | `0.18127` | `1.14051` | no |
| `demosaic_red` | `0.04498` | `0.33266` | `2.23766` | yes |
| `raw_red_upsampled` | `0.07250` | `0.46990` | `3.67166` | yes |

Additional focus-preset averages from the same artifact:

- `gray`
  - Acutance focus-preset MAE mean: `0.02354`
  - Quality Loss focus-preset MAE mean: `1.39556`
- `demosaic_red`
  - Acutance focus-preset MAE mean: `0.04177`
  - Quality Loss focus-preset MAE mean: `2.76772`
- `raw_red_upsampled`
  - Acutance focus-preset MAE mean: `0.06748`
  - Quality Loss focus-preset MAE mean: `4.50894`

## Recommendation

The current best parity-valid input pipeline is:

- `bayer_mode = demosaic_red`
- `bayer_pattern = RGGB`

Reason:

- `gray` benchmarks better numerically, but it violates the observable target condition `Color channel = R`, so it cannot be the locked parity path
- among the parity-valid R-channel candidates, `demosaic_red` beats `raw_red_upsampled` on all three tracked global metrics:
  - lower `curve_mae_mean`
  - lower mean absolute band-wise MTF signed relative residual
  - lower overall Quality Loss MAE

## Rejected Candidates

### `gray`

Rejected for parity fitting even though it remains useful as a diagnostic control.

Reason:

- the golden CSVs explicitly report `Color channel = R`
- `gray` is therefore a non-parity baseline, not an acceptable locked input path for later parity-fit issues
- its stronger metrics are still useful evidence: the remaining parity gap is partly the cost of honoring the observed R-channel constraint rather than averaging everything into a grayscale surrogate

### `raw_red_upsampled`

Rejected as the locked parity path.

Reason:

- it preserves the R-only idea
- but it is materially worse than `demosaic_red` on the full dataset under the current analysis frame
- its larger high/top-frequency suppression makes it a weaker baseline for the later PSD/MTF refit issue

## Downstream Rule

Later parity-fit issues should treat the input path as fixed unless new source-backed evidence reopens the question:

- issue `#11` should use `demosaic_red + RGGB` as the parity input pipeline while re-fitting PSD/MTF
- issue `#12` should validate Acutance and Quality Loss on top of that same locked input path
- issue `#13` should not publish a release-facing parity-fit profile that silently swaps the input path again

## Reproduction

```bash
python3 -m algo.benchmark_parity_input_pipeline \
  20260318_deadleaf_13b10 \
  --calibration-file algo/deadleaf_13b10_psd_calibration.json \
  --analysis-gamma 1.0 \
  --roi-source fixed \
  --output artifacts/parity_input_pipeline_benchmark.json
```
