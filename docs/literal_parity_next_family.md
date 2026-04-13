# Literal Parity Next Family

This note records the issue `#71` selection of the next source-backed literal parity family.

## Selected Route

- Selected family: `literal/measured_oecf_on_sensor_comp`
- Summary: Advance the measured OECF-driven linearization family on top of the literal sensor-compensation route, keep intrinsic/full-reference as a later family, and do not reopen generic direct-method retunes or generic standard-OETF swaps.

## Candidate Table

| Rank | Family | Decision | Source Types | Curve MAE | Focus Acu MAE | Overall QL | Key Reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | literal/measured_oecf_on_sensor_comp | advance | official_imatest_doc, peer_reviewed_paper | 0.03812 | 0.06823 | 3.01158 | The literal parity sensor-plus-toe proxy branch is the strongest checked-in literal route on curve and overall Quality Loss metrics. |
| 2 | literal/intrinsic_full_reference | defer | official_imatest_doc, peer_reviewed_paper | 0.03587 | 0.03165 | 4.56801 | The current intrinsic implementations still break downstream Quality Loss too severely to be the next literal route. |
| 3 | literal/chart_sensor_compensation_only | defer | official_imatest_doc, peer_reviewed_paper | 0.05522 | 0.06881 | 3.37730 | Compensation alone regresses focus-preset Acutance and overall Quality Loss. |

## Candidate Readout

### literal/measured_oecf_on_sensor_comp

- Decision: `advance`
- Source types: `official_imatest_doc`, `peer_reviewed_paper`
- Source summary: Imatest gamma/OECF guidance plus the dead-leaves literature both point to measured linearization as a missing family; the checked-in toe proxy is only an engineering stand-in for that missing measured OECF.
- Adopt reason: The literal parity sensor-plus-toe proxy branch is the strongest checked-in literal route on curve and overall Quality Loss metrics.
- Adopt reason: The standard inverse-OETF controls are already checked in and are materially worse, so the open path is a measured OECF family rather than another generic OETF swap.
- Adopt reason: This family naturally supports strict separation between golden/reference data and new fitted OECF artifacts.
- Evidence:
  `algo/deadleaf_13b10_imatest_sensor_comp_toe_profile.json` from `artifacts/imatest_parity_oecf_sensor_compensation_benchmark.json`: `curve_mae_mean=0.03812`, `focus_acu_mae=0.06823`, `overall_ql=3.01158`, `MTF20/30/50=-/-/-`
  `algo/deadleaf_13b10_imatest_sensor_comp_srgb_profile.json` from `artifacts/imatest_parity_oetf_family_benchmark.json`: `curve_mae_mean=0.09127`, `focus_acu_mae=0.09695`, `overall_ql=4.38993`, `MTF20/30/50=-/-/-`
  `algo/deadleaf_13b10_imatest_sensor_comp_rec709_profile.json` from `artifacts/imatest_parity_oetf_family_benchmark.json`: `curve_mae_mean=0.08788`, `focus_acu_mae=0.09381`, `overall_ql=4.26083`, `MTF20/30/50=-/-/-`
- Fitted profiles: `algo/deadleaf_13b10_imatest_sensor_comp_toe_profile.json`
- Release-facing configs: `release/deadleaf_13b10_release/config/imatest_parity_sensor_comp_toe_profile.release.json`

### literal/intrinsic_full_reference

- Decision: `defer`
- Source types: `official_imatest_doc`, `peer_reviewed_paper`
- Source summary: Imatest Random-Cross and the intrinsic dead-leaves literature make the full-reference path a real source-backed family rather than a free-form retune.
- Adopt reason: Intrinsic/full-reference is still a legitimate missing family in the repo's source inventory.
- Adopt reason: It materially improves curve fit and non-Phone/focus-preset Acutance on the checked-in experiments.
- Exclude/defer reason: The current intrinsic implementations still break downstream Quality Loss too severely to be the next literal route.
- Exclude/defer reason: The remaining work is more naturally a later family once the literal linearization boundary and fitted-artifact separation are fixed.
- Evidence:
  `algo/deadleaf_13b10_imatest_intrinsic_full_reference_profile.json` from `artifacts/imatest_parity_intrinsic_full_reference_benchmark.json`: `curve_mae_mean=0.03587`, `focus_acu_mae=0.03165`, `overall_ql=4.56801`, `MTF20/30/50=-/-/-`
  `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_profile.json` from `artifacts/issue46_intrinsic_phase_retention_acutance_benchmark.json`: `curve_mae_mean=0.03280`, `focus_acu_mae=0.02892`, `overall_ql=14.47576`, `MTF20/30/50=-/-/-`
- Fitted profiles: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_profile.json`, `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_profile.json`

### literal/chart_sensor_compensation_only

- Decision: `defer`
- Source types: `official_imatest_doc`, `peer_reviewed_paper`
- Source summary: Imatest MTF-compensation guidance and the dead-leaves literature both support chart and sensor compensation as a missing literal-parity family.
- Adopt reason: The compensation-only branch removes a meaningful portion of the literal high-frequency underfit and improves threshold readouts.
- Exclude/defer reason: Compensation alone regresses focus-preset Acutance and overall Quality Loss.
- Exclude/defer reason: The sensor-comp-only path is already superseded by the stronger literal sensor-plus-OECF-proxy branch.
- Evidence:
  `algo/deadleaf_13b10_imatest_sensor_comp_profile.json` from `artifacts/imatest_parity_sensor_compensation_benchmark.json`: `curve_mae_mean=0.05522`, `focus_acu_mae=0.06881`, `overall_ql=3.37730`, `MTF20/30/50=-/-/-`
- Fitted profiles: `algo/deadleaf_13b10_imatest_sensor_comp_profile.json`
- Release-facing configs: `release/deadleaf_13b10_release/config/imatest_parity_sensor_comp_profile.release.json`

## Storage Separation

- Golden/reference roots:
  - `20260318_deadleaf_13b10`
  - `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`
- Fitted artifact roots:
  - `algo/*.json`
  - `artifacts/*.json`
- Release-facing config roots:
  - `release/deadleaf_13b10_release/config/*.json`
- Rules:
  - Do not write fitted profiles, calibrations, or benchmark outputs under the golden/reference roots.
  - Keep new fitted profiles and calibrations in algo/ and measured benchmark outputs in artifacts/.
  - Only add release-facing configs under release/deadleaf_13b10_release/config/ after a family is chosen for release-facing validation.

## Excluded Retunes

- `generic standard inverse-OETF swaps`: The checked-in `sRGB` and `Rec.709` literal branches are source-backed controls, but both are already worse than the toe proxy and therefore should not be reopened as the next family.
- `generic direct-method retunes without new source basis`: Issue #71 explicitly forbids reopening exhausted generic direct-method retunes without a new source basis, and the issue-56 / issue-67 / issue-70 chain already closed those paths.
