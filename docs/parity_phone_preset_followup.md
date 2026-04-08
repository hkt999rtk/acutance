# Parity Phone Preset Follow-Up

This note records the issue `#18` follow-up on top of the parity-fit baseline from [parity_acutance_quality_loss_validation.md](./parity_acutance_quality_loss_validation.md).

Profiles compared in [../artifacts/parity_phone_preset_benchmark.json](../artifacts/parity_phone_preset_benchmark.json):

1. parity-fit baseline
   - [../algo/deadleaf_13b10_parity_psd_mtf_profile.json](../algo/deadleaf_13b10_parity_psd_mtf_profile.json)
2. parity-fit baseline with a Phone-only preset override
   - [../algo/deadleaf_13b10_parity_psd_mtf_phone_profile.json](../algo/deadleaf_13b10_parity_psd_mtf_phone_profile.json)

Both profiles keep the same parity-fit analysis path:

- `analysis_gamma = 1.0`
- `bayer_pattern = RGGB`
- `bayer_mode = demosaic_red`
- fixed ROI
- `frequency_scale = 1.17`

The only change in the tuned profile is the `5.5" Phone` preset viewing distance:

- baseline: `29.5 cm`
- tuned: `25.55 cm`

## Summary

The current parity-fit line already had the best overall curve fit, but it overstated the `5.5" Phone` viewing magnification. Narrowing only that preset geometry reduces the Phone regression without moving the global parity-fit line.

Compared with the parity-fit baseline, the Phone-tuned profile reduces:

- `5.5" Phone` Acutance MAE: `0.04825 -> 0.00510`
- `5.5" Phone` Quality Loss MAE: `0.73163 -> 0.08143`
- Acutance focus-preset MAE mean: `0.02911 -> 0.02049`
- overall Quality Loss MAE mean: `1.27621 -> 1.14617`

The Acutance curve baseline is unchanged:

- `curve_mae_mean`: `0.01970 -> 0.01970`

## Interpretation

- the parity-fit baseline itself is still the right PSD/MTF line
- the residual gap was concentrated in the Phone preset magnification assumption, not in the shared curve fit
- the tuned `25.55 cm` viewing distance keeps the non-phone presets unchanged while bringing the Phone preset back below the older locked-input baseline on both Acutance and Quality Loss

## Release Impact

The release-facing parity-fit profile now carries the same Phone override through `config/parity_fit_profile.release.json`, so the default release run no longer needs to preserve the old Phone-regression caveat from issue `#12`.

## Reproduction

```bash
python3 -m algo.benchmark_parity_acutance_quality_loss \
  20260318_deadleaf_13b10 \
  algo/deadleaf_13b10_parity_psd_mtf_profile.json \
  algo/deadleaf_13b10_parity_psd_mtf_phone_profile.json \
  --output artifacts/parity_phone_preset_benchmark.json
```
