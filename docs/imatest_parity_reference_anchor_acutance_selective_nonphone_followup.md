# Imatest Parity Selective Non-Phone Acutance Follow-up

Issue: `#29`  
PR: `#30`

## What changed

- Benchmarked a more selective preset-side non-phone Acutance family on top of the current best sextic branch:
  - `algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_profile.json`
- This follow-up split the earlier flat non-phone plateau into three narrower candidates:
  - `monitor_notch_085`
  - `print_tv_plateau_090`
  - `split_monitor_print_095_090`
- Checked in the bounded search summary:
  - `artifacts/imatest_parity_reference_anchor_acutance_selective_nonphone_search.json`

## Why this family

The previous Acutance-record export showed:

- the phone preset is no longer the main blocker
- the remaining Acutance miss is concentrated in `Computer Monitor`, `UHDTV Display`, `Small Print`, and `Large Print`

The previous flat non-phone plateau was too coarse, so this pass split that band into:

- a monitor-scale notch around relative scale `1.31`
- a print / TV plateau around relative scales `1.9` to `2.6`
- a combined split branch that attenuates both regions

## Result

This is another bounded trade-off result, not a new best branch.

Baseline:

- `curve_mae_mean = 0.03776865`
- `acutance_focus_preset_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22214`

Candidates:

- `monitor_notch_085`
  - `acutance_focus_preset_mae_mean = 0.04257`
  - `overall_quality_loss_mae_mean = 1.25226`
- `print_tv_plateau_090`
  - `acutance_focus_preset_mae_mean = 0.04266`
  - `overall_quality_loss_mae_mean = 1.20882`
- `split_monitor_print_095_090`
  - `acutance_focus_preset_mae_mean = 0.04266`
  - `overall_quality_loss_mae_mean = 1.21452`

Interpretation:

- the monitor notch is clearly worse on both remaining gates
- the print / TV plateau and the split branch improve overall Quality Loss slightly
- but both still make the still-open `acutance_focus_preset_mae_mean` gate worse
- none of the three candidates beats the current best branch on the remaining blocker

## Conclusion

The remaining issue-29 Acutance blocker is not solved by selective preset-side non-phone attenuation alone.

This narrows the next useful family further:

- move upstream to a curve-side attenuation family tied to the exported mid-scale curve residual, or
- add a more structured family than preset-side strength-only shaping if the goal is to improve focus-preset Acutance without giving back the current best branch.
