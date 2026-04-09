# Imatest Parity Non-Phone Acutance Strength Follow-up

Issue: `#29`  
PR: `#30`

## What changed

- Benchmarked a new preset-side Acutance attenuation family on top of the current best branch:
  - `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_profile.json`
- The new family only changes the preset-side Acutance strength curve in the non-phone relative-scale band:
  - relative scales: `[0.0, 1.15, 1.35, 2.6, 3.0, 4.5, 5.8, 6.2]`
  - bounded plateau probes: `0.9`, `0.8`, `0.7`
- Checked in the bounded search summary:
  - `artifacts/imatest_parity_reference_anchor_acutance_nonphone_strength_search.json`

## Why this family

The exported Acutance records from the previous pass showed that the remaining miss is no longer phone-local:

- `5.5" Phone Display Acutance` is already the smallest preset error on the current best branch
- the remaining focus-preset blocker is concentrated in `Computer Monitor`, `UHDTV Display`, `Small Print`, and `Large Print`
- the curve residual is mostly positive and concentrated in the mid-scale region

So the next useful bounded probe was to attenuate the preset-side Acutance correction in the non-phone band without touching the phone tail.

## Result

This family is a bounded negative result.

Compared with the current sextic best branch:

- baseline:
  - `curve_mae_mean = 0.03776865`
  - `acutance_focus_preset_mae_mean = 0.04249`
  - `overall_quality_loss_mae_mean = 1.22214`

- `nonphone_strength_09`:
  - `acutance_focus_preset_mae_mean = 0.04267`
  - `overall_quality_loss_mae_mean = 1.22225`

- `nonphone_strength_08`:
  - `acutance_focus_preset_mae_mean = 0.04303`
  - `overall_quality_loss_mae_mean = 1.24027`

- `nonphone_strength_07`:
  - `acutance_focus_preset_mae_mean = 0.04349`
  - `overall_quality_loss_mae_mean = 1.26525`

The curve stays fixed for all three probes, but the non-phone attenuation branch still loses overall:

- `Computer Monitor` and `Large Print` get worse immediately
- `Small Print` also gets worse
- `UHDTV Display` improves slightly, but not enough to offset the rest
- the phone preset stays unchanged, as intended

## Conclusion

The remaining Acutance miss is not solved by a naive preset-side non-phone strength plateau.

That means the next upstream family should be more structured than a flat non-phone attenuation band, for example:

- a mid-scale curve-side attenuation family tied to the exported curve error region, or
- a more selective non-phone preset family that separates monitor / TV / print behavior instead of treating them as one plateau.
