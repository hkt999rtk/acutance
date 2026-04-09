# Imatest Parity Reference-Refined ROI Follow-up

This note records the fourth issue `#29` follow-up pass.

It builds on the current best branch from
[imatest_parity_oecf_sensor_compensation_followup.md](./imatest_parity_oecf_sensor_compensation_followup.md):

- `toe_power` linearization proxy
- `sensor_aperture_sinc` compensation

Motivation:

- the current toe-plus-sensor branch is the best issue-29 path so far
- the remaining missing families named in the repo docs still include registration / warp accuracy
- the repo already had a local texture-support ROI fine-search utility, but it had not yet been tested as a reference-guided follow-up on top of the issue-29 best branch

This pass therefore adds a narrow registration experiment:

- start from the Imatest-observed `LRTB` ROI for each CSV
- run a bounded texture-support refinement search around that reference ROI
- keep the same toe-plus-sensor analysis path otherwise

The search window is intentionally narrow:

- `roi_source = reference_refined`
- `search_radius = 4`
- `step = 2`

That keeps this pass focused on local registration / crop placement rather than reopening the whole ROI policy.

## Profiles Compared

Benchmark artifacts:

- [../artifacts/imatest_parity_reference_refined_r4_psd_benchmark.json](../artifacts/imatest_parity_reference_refined_r4_psd_benchmark.json)
- [../artifacts/imatest_parity_reference_refined_r4_benchmark.json](../artifacts/imatest_parity_reference_refined_r4_benchmark.json)

Profiles:

1. current best toe-plus-sensor branch
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_profile.json)
2. toe-plus-sensor plus reference-guided ROI refinement
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_refined_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_refined_profile.json)

## PSD / MTF Result

Compared with the current toe-plus-sensor branch:

- `curve_mae_mean`: `0.0381238 -> 0.0379513`
- mean absolute band signed-rel error: `0.0870316 -> 0.0869296`
- `high signed-rel mean`: `0.04943 -> 0.04964`
- `top signed-rel mean`: `-0.16446 -> -0.16463`

Interpretation:

- the registration-guided refinement is a small improvement, not a step change
- most of the gain comes from slight curve tightening rather than a different high/top-band shape
- this supports the idea that local ROI placement still matters, but it is not the dominant remaining issue-29 gap by itself

## Acutance / Quality Loss Result

Compared with the current toe-plus-sensor branch:

- `acutance_focus_preset_mae_mean`: `0.0682267 -> 0.0680820`
- `overall_quality_loss_mae_mean`: `3.0115812 -> 3.0020871`

Interpretation:

- this is another issue-29 branch that improves all three tracked aggregates together:
  - `curve_mae_mean`
  - `acutance_focus_preset_mae_mean`
  - `overall_quality_loss_mae_mean`
- however, the improvement is still small
- the branch still does not beat the literal observable-parity baseline on preset Acutance overall

## Working Conclusion

This pass narrows the registration family for issue `#29`:

- local reference-guided ROI refinement is directionally helpful on top of the toe-plus-sensor branch
- the effect size is much smaller than the earlier toe-plus-sensor jump
- registration accuracy is therefore a plausible contributing factor, but not enough by itself to close the README target gap

What remains:

- the current best issue-29 branch is now toe-plus-sensor plus reference-guided refinement
- preset Acutance MAE is still above the literal baseline
- later work should combine this branch with a stronger dataset-specific OECF family or a more faithful intrinsic/reference method if the goal is to actually reach the canonical target
