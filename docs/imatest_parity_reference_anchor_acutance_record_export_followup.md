# Imatest Parity Acutance Record Export Follow-up

Issue: `#29`  
PR: `#30`

## What changed

- Added `--include-acutance-records` to `algo.benchmark_parity_acutance_quality_loss`.
- Exported per-sample `curve` and `preset` Acutance records for the current best branch:
  - `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_profile.json`
- Checked in:
  - `artifacts/imatest_parity_reference_anchor_acutance_curve_qualityfit_allpreset_sextic_acutance_records.json`
  - `artifacts/imatest_parity_reference_anchor_acutance_curve_qualityfit_allpreset_sextic_acutance_record_summary.json`

## Current branch context

The current best branch keeps:

- `curve_mae_mean = 0.03776865`
- `acutance_focus_preset_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22214`

At this point Quality Loss is no longer the blocker. The remaining gates are upstream on the Acutance curve and focus presets.

## What the exported records show

### 1. The remaining Acutance miss is systematically positive

Every focus preset has a positive mean signed Acutance error on the current best branch:

- `5.5" Phone Display Acutance`: `+0.01124`
- `Computer Monitor Acutance`: `+0.01642`
- `UHDTV Display Acutance`: `+0.03603`
- `Small Print Acutance`: `+0.04544`
- `Large Print Acutance`: `+0.05103`

This means the branch is not oscillating around the target. It is still overpredicting Acutance almost everywhere, especially away from the phone preset.

### 2. The focus-preset blocker is now mostly non-phone

The preset MAE ranking is:

- `Computer Monitor Acutance`: `0.05269`
- `Large Print Acutance`: `0.05132`
- `UHDTV Display Acutance`: `0.04794`
- `Small Print Acutance`: `0.04670`
- `5.5" Phone Display Acutance`: `0.01380`

The earlier phone-heavy gap has largely been reduced. The remaining focus-preset blocker is now concentrated in the monitor / TV / print presets.

### 3. The curve miss is also mostly positive and peaks in the mid-distance region

The exported curve records are positive almost everywhere. The largest mean absolute errors land around:

- `h40.0_d24.0`: `0.05496`
- `h40.0_d25.0`: `0.05597`
- `h40.0_d26.0`: `0.05621`
- `h40.0_d29.0`: `0.05718`
- `h40.0_d30.0`: `0.05716`

So the remaining curve gate is not dominated by the phone tail. It is concentrated in the mid-scale region.

### 4. The worst curve residuals are concentrated in lower-mixup captures

Mean curve MAE by mixup from the exported records:

- `0.15`: `0.04588`
- `0.25`: `0.03701`
- `0.4`: `0.02940`
- `0.65`: `0.03326`
- `0.8`: `0.03845`
- `ori`: `0.04293`

The current branch is most biased on the lower-mixup captures, especially `0.15`, rather than on the high-mixup cases.

## Implication for the next step

The next useful Acutance-side follow-up should not be another phone-local tweak.

The exported records point to a narrower target:

- add a non-phone or mid-scale attenuation family on the preset side, or
- add a curve-side attenuation family that is strongest in the mid-distance region and/or lower-mixup captures.

The current evidence does not support prioritizing more phone-only tuning, because the phone preset is already the smallest Acutance error on the current best branch.
