# Parity PSD/MTF Refit

This note records the issue `#11` PSD/MTF refit pass that follows the input-pipeline decision from [parity_input_pipeline_candidates.md](./parity_input_pipeline_candidates.md).

Locked input path from issue `#10`:

- `analysis_gamma = 1.0`
- `bayer_pattern = RGGB`
- `bayer_mode = demosaic_red`
- `roi_source = fixed`

The purpose of this pass is narrower than the full parity umbrella:

- improve the PSD/MTF core under the locked input path
- produce a parity-fit artifact that later validation issues can use as a stable baseline
- avoid release-profile claims until downstream Acutance / Quality Loss validation is complete

## Artifacts

- baseline profile:
  - [../algo/deadleaf_13b10_locked_input_baseline_profile.json](../algo/deadleaf_13b10_locked_input_baseline_profile.json)
- parity-fit profile:
  - [../algo/deadleaf_13b10_parity_psd_mtf_profile.json](../algo/deadleaf_13b10_parity_psd_mtf_profile.json)
- benchmark driver:
  - [../algo/benchmark_parity_psd_mtf.py](../algo/benchmark_parity_psd_mtf.py)
- benchmark result:
  - [../artifacts/parity_psd_mtf_benchmark.json](../artifacts/parity_psd_mtf_benchmark.json)

## What Changed

The selected parity-fit profile keeps the same locked input path and ideal-PSD calibration file as the locked-input baseline, but changes:

- `frequency_scale: 1.0 -> 1.17`

The scale value is not arbitrary:

- the current `demosaic_red` parity path prefers a larger global frequency scale than the older exploratory settings
- a dedicated sweep under the locked parity path selected approximately `1.17`
- this change is explainable as a frequency-axis fit, not an opaque post-hoc fudge term

No new signal-PSD correction was adopted in this pass:

- `signal_psd_correction_gain` remains `0.0`

No release profile is changed in this issue.

## Benchmark Summary

From [../artifacts/parity_psd_mtf_benchmark.json](../artifacts/parity_psd_mtf_benchmark.json):

| Profile | `curve_mae_mean` | mean abs band signed-rel | `MTF50` MAE |
| --- | --- | --- | --- |
| locked-input baseline | `0.04498` | `0.33020` | `0.03342` |
| parity-fit candidate | `0.01970` | `0.22759` | `0.01931` |

Band-wise signed relative MTF residuals also improve in every tracked band:

| Band | baseline | parity-fit |
| --- | --- | --- |
| low | `-0.09316` | `-0.02999` |
| mid | `-0.23805` | `-0.08461` |
| high | `-0.30393` | `-0.20922` |
| top | `-0.68565` | `-0.58655` |

Interpretation:

- the main residual shape is still biased low at high frequencies
- but the frequency-axis correction removes a large part of the earlier systematic underfit
- this is now a materially better PSD/MTF baseline than the locked-input pre-refit profile

## Scope Boundary

This issue intentionally stops at the PSD/MTF baseline.

Known follow-up work that remains outside this issue:

- issue `#12` must revalidate Acutance and Quality Loss on top of this new PSD/MTF baseline
- the `5.5\" Phone` preset error is worse under the new scaled profile even though the overall curve and MTF metrics improve, so downstream validation still matters
- issue `#13` should decide whether this profile is good enough for release-facing packaging only after that validation exists

## Reproduction

```bash
python3 -m algo.benchmark_parity_psd_mtf \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_locked_input_baseline_profile.json \
  algo/deadleaf_13b10_parity_psd_mtf_profile.json \
  --output artifacts/parity_psd_mtf_benchmark.json
```
