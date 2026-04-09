# Imatest Parity Standard OETF Family Follow-up

This note records the third issue `#29` follow-up pass after the earlier:

- [imatest_parity_sensor_compensation_followup.md](./imatest_parity_sensor_compensation_followup.md)
- [imatest_parity_oecf_sensor_compensation_followup.md](./imatest_parity_oecf_sensor_compensation_followup.md)

Motivation:

- the toe-style OECF proxy improved literal-parity `curve_mae_mean` and `overall_quality_loss_mae_mean`
- but the toe term is still an engineering proxy rather than a standard measured OECF family
- the next useful question was whether a more constrained source-backed inverse-OETF family could replace that proxy

This pass therefore compares the current issue-29 branches against two standard inverse-OETF candidates:

- `sRGB`
- `Rec.709`

Both candidates keep the same sensor-compensation path as the earlier follow-ups and replace the toe proxy with a standard inverse transfer function.

## Profiles Compared

Benchmark artifacts:

- [../artifacts/imatest_parity_oetf_family_psd_benchmark.json](../artifacts/imatest_parity_oetf_family_psd_benchmark.json)
- [../artifacts/imatest_parity_oetf_family_benchmark.json](../artifacts/imatest_parity_oetf_family_benchmark.json)

Profiles:

1. literal observable-parity baseline
   - [../algo/deadleaf_13b10_imatest_parity_profile.json](../algo/deadleaf_13b10_imatest_parity_profile.json)
2. literal observable-parity plus sensor compensation
   - [../algo/deadleaf_13b10_imatest_sensor_comp_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_profile.json)
3. literal observable-parity plus sensor compensation and toe linearization
   - [../algo/deadleaf_13b10_imatest_sensor_comp_toe_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_toe_profile.json)
4. sensor compensation plus inverse `sRGB` OETF
   - [../algo/deadleaf_13b10_imatest_sensor_comp_srgb_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_srgb_profile.json)
5. sensor compensation plus inverse `Rec.709` OETF
   - [../algo/deadleaf_13b10_imatest_sensor_comp_rec709_profile.json](../algo/deadleaf_13b10_imatest_sensor_comp_rec709_profile.json)

The two standard-OETF candidates use:

- `linearization_mode = srgb` or `rec709`
- `gamma = 1.0`
- `mtf_compensation_mode = sensor_aperture_sinc`
- `sensor_fill_factor = 1.5`

## PSD / MTF Result

Compared with the current toe-proxy branch:

- toe proxy
  - `curve_mae_mean = 0.03812`
  - mean absolute band signed-rel error = `0.08703`
  - `high signed-rel mean = 0.04943`
  - `top signed-rel mean = -0.16446`
- `sRGB`
  - `curve_mae_mean = 0.09127`
  - mean absolute band signed-rel error = `0.16567`
  - `high signed-rel mean = 0.34186`
  - `top signed-rel mean = 0.09505`
- `Rec.709`
  - `curve_mae_mean = 0.08788`
  - mean absolute band signed-rel error = `0.14766`
  - `high signed-rel mean = 0.31186`
  - `top signed-rel mean = 0.07029`

Interpretation:

- both standard inverse-OETF candidates overshoot the high and top bands instead of just reducing the earlier underfit
- both are materially worse than the toe proxy on `curve_mae_mean`
- both are still somewhat better than the original literal baseline on mean absolute signed-rel error, but not in a way that supports replacing the toe branch

## Acutance / Quality Loss Result

Compared with the toe proxy:

- toe proxy
  - `acutance_focus_preset_mae_mean = 0.06823`
  - `overall_quality_loss_mae_mean = 3.01158`
- `sRGB`
  - `acutance_focus_preset_mae_mean = 0.09695`
  - `overall_quality_loss_mae_mean = 4.38993`
- `Rec.709`
  - `acutance_focus_preset_mae_mean = 0.09381`
  - `overall_quality_loss_mae_mean = 4.26083`

Interpretation:

- both standard inverse-OETF candidates are worse than the toe proxy on both preset Acutance and overall Quality Loss
- both are also worse than the literal observable-parity baseline itself

## Working Conclusion

This pass narrows the linearization family for issue `#29`:

- a standard inverse `sRGB` or `Rec.709` OETF is not a good replacement for the current toe-style OECF proxy on this dataset
- the toe proxy remains the best current OECF-related branch in the repo, even though it is still only a proxy
- the next useful parity step should not spend more time on generic standard-OETF swaps

What remains:

- the best current issue-29 branch is still the combined toe-plus-sensor-compensation path
- preset Acutance MAE still does not beat the literal baseline overall
- later work should refine the OECF family with stronger dataset-specific constraints, or add a different missing model family such as intrinsic/reference handling, instead of treating standard display/video OETF curves as the answer
