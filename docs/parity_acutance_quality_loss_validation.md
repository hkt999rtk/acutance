# Parity Acutance And Quality Loss Validation

This note records the issue `#12` validation pass on top of the parity PSD/MTF baseline from [parity_psd_mtf_refit.md](./parity_psd_mtf_refit.md).

Profiles compared in [../artifacts/parity_acutance_quality_loss_benchmark.json](../artifacts/parity_acutance_quality_loss_benchmark.json):

1. previous parity baseline
   - [../algo/deadleaf_13b10_locked_input_baseline_profile.json](../algo/deadleaf_13b10_locked_input_baseline_profile.json)
2. new parity-fit PSD/MTF baseline
   - [../algo/deadleaf_13b10_parity_psd_mtf_profile.json](../algo/deadleaf_13b10_parity_psd_mtf_profile.json)
3. retained split-workaround reference
   - [../algo/deadleaf_13b10_split_workaround_reference_profile.json](../algo/deadleaf_13b10_split_workaround_reference_profile.json)

All three profiles use the same locked parity input path:

- `analysis_gamma = 1.0`
- `bayer_pattern = RGGB`
- `bayer_mode = demosaic_red`
- fixed ROI

## Summary

The new parity-fit PSD/MTF baseline improves end-to-end Acutance and Quality Loss validation overall.

Compared with the previous parity baseline, it reduces:

- `curve_mae_mean`: `0.04498 -> 0.01970`
- Acutance focus-preset MAE mean: `0.03480 -> 0.02911`
- overall Quality Loss MAE mean: `2.19874 -> 1.27621`

Compared with the retained split-workaround reference, it also reduces:

- `curve_mae_mean`: `0.04691 -> 0.01970`
- Acutance focus-preset MAE mean: `0.03579 -> 0.02911`
- overall Quality Loss MAE mean: `2.27361 -> 1.27621`

So the parity-fit baseline is now the strongest overall profile in the repo's current benchmark frame.

## Acutance Preset Changes

Previous parity baseline vs parity-fit:

| Preset | previous parity | parity-fit | result |
| --- | --- | --- | --- |
| `5.5" Phone` | `0.00688` | `0.04825` | worse |
| `Computer Monitor` | `0.06497` | `0.02475` | better |
| `UHDTV` | `0.03750` | `0.02139` | better |
| `Small Print` | `0.03075` | `0.02895` | slightly better |
| `Large Print` | `0.03388` | `0.02223` | better |

Interpretation:

- the new parity-fit baseline materially improves the larger-display and print-oriented presets
- the `Phone` preset is the main regression that remains

## Quality Loss Changes

Previous parity baseline vs parity-fit:

| Preset | previous parity | parity-fit | result |
| --- | --- | --- | --- |
| `5.5" Phone` | `0.11741` | `0.73163` | much worse |
| `Computer Monitor` | `4.83734` | `1.76833` | much better |
| `UHDTV` | `1.99985` | `1.28238` | better |
| `Small Print` | `1.81196` | `1.39907` | better |
| `Large Print` | `2.22714` | `1.19961` | much better |

Interpretation:

- the parity-fit baseline improves four of the five Quality Loss presets
- the remaining weakness is concentrated in the `Phone` geometry path

## Comparison With The Split Workaround

The retained split-workaround reference was useful historically, but it is no longer the best overall validation result.

Why:

- its `curve_mae_mean` is still worse than the prior parity baseline
- its overall Quality Loss MAE is also worse than the prior parity baseline
- the new parity-fit baseline beats it by a wide margin on the overall curve and on most non-phone presets

This means the repo now has a parity-fit baseline that is better than the older workaround in the current measured frame, even though the `Phone` preset still needs follow-up attention.

## Working Conclusion

Issue `#12` does not block the parity-fit line.

The new parity-fit PSD/MTF baseline is now validated as:

- materially better than the previous parity baseline
- materially better than the retained split-workaround reference overall
- still carrying one clear downstream caveat:
  - `5.5" Phone` Acutance and Quality Loss regress relative to the old profiles

That caveat should be carried into the release-facing profile work instead of hidden.

## Reproduction

```bash
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_locked_input_baseline_profile.json \
  algo/deadleaf_13b10_parity_psd_mtf_profile.json \
  algo/deadleaf_13b10_split_workaround_reference_profile.json \
  --output artifacts/parity_acutance_quality_loss_benchmark.json
```
