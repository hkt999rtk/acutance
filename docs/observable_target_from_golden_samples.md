# Observable Target From Golden Imatest Samples

This document is the canonical source of truth for what the project can directly observe from the golden Imatest `Random / Dead Leaves` CSV samples.

It exists to keep three categories separate:

- observable sample conditions and outputs
- latent black-box variables that still need to be inferred
- current engineering assumptions used by the Python prototype

If a field is not directly present in the golden CSVs, it must not be described elsewhere in the repo as if Imatest has already revealed it.

## Golden Sample Set

Current canonical golden samples come from:

- `20260318_deadleaf_13b10/OV13B10_AI_NR_OV13B10_ori/Results/OV13b10_AG15.5_ET2800_deadleaf_12M_60_R_Random.csv`
- `20260318_deadleaf_13b10/OV13B10_AI_NR_OV13B10_ori/Results/OV13b10_AG1_ET40000_deadleaf_12M_1_R_Random.csv`
- `20260318_deadleaf_13b10/OV13B10_AI_NR_OV13B10_ori/Results/OV13b10_AG4_ET11000_deadleaf_12M_20_R_Random.csv`
- `20260318_deadleaf_13b10/OV13B10_AI_NR_OV13B10_ori/Results/OV13b10_AG8_ET5500_deadleaf_12M_40_R_Random.csv`

The parser entry point for these files is `algo.dead_leaves.parse_imatest_random_csv`.

Related follow-up note:

- [gamma_0_5_hypothesis_matrix.md](./gamma_0_5_hypothesis_matrix.md)
- [dead_leaves_black_box_research.md](./dead_leaves_black_box_research.md)

## Directly Observed Conditions

These values are read directly from the golden CSV rows and are therefore part of the observable fitting target.

| Field | Observed value(s) in golden set | Notes |
| --- | --- | --- |
| `Image pixels (WxH)` | `4032 x 3024` in all four CSVs | Observable image-domain input condition |
| `Crop` | `1673 x 1656` in three CSVs; `1669 x 1653` in one CSV | Observable reported crop size, not proof of Imatest's internal crop-search policy |
| `L R T B` | `1194, 2866, 646, 2301` in three CSVs; `1194, 2862, 647, 2299` in one CSV | Observable crop bounds |
| `Gamma` | `0.5` in all four CSVs | Observable report field only; internal meaning remains unresolved |
| `Color channel` | `R` in all four CSVs | Observable report field only |
| `Use unnormalized MTF for Acutance calculation` | present in all four CSVs | Observable Acutance-path condition |
| `Max detected f (c/p)` | `0.498` in all four CSVs | Observable report output |
| `Table of MTF` | 64 reported frequency bins per CSV | Includes `MTF`, `MTF w/noise`, `Noise PSD`, `S+N PSD`, `Signal PSD` |
| `MTFnn` threshold rows | present in every CSV | Observable threshold outputs such as `MTF70/50/30/20/10` |
| `Acutance (CPIQ)` curve | 100 distances for `Print height = 40 cm` in every CSV | Observable full Acutance curve target |
| preset Acutance rows | present in every CSV | `Computer Monitor`, `5.5\" Phone`, `UHDTV`, `Small Print`, `Large Print` |
| preset Quality Loss rows | present in every CSV | Same five presets as above |

## What Is Not Directly Observed

The golden CSVs do not directly reveal these internal variables. They remain latent black-box state and should be treated as fitting hypotheses, not observed facts.

| Variable / concept | Why it is latent |
| --- | --- |
| analysis gamma exponent | The CSV shows `Gamma = 0.5`, but it does not say this is the exact exponent applied before Fourier analysis |
| internal color-channel pipeline | `Color channel = R` does not prove whether Imatest uses `demosaic_red`, raw-red upsampling, or another internal path |
| Bayer pattern handling details | Not encoded in the golden CSV rows |
| OECF / linearization implementation | Not encoded in the golden CSV rows |
| ideal dead-leaves PSD formula | Not encoded in the golden CSV rows |
| ROI search / refinement policy | Reported crop bounds are observable, but the search algorithm that produced them is not |
| frequency-axis mapping internals | Reported bins are observable; the hidden mapping logic is not |
| noise PSD model and subtraction policy | Output columns are observable; the internal estimator is not |
| display / print MTF model used inside preset Acutance | Final preset numbers are observable; the internal display model is not |

## Current Inferred Assumptions In This Repo

These are current engineering choices used by the Python prototype. They may be useful, but they are not part of the observable source-of-truth target.

| Current assumption / choice | Status |
| --- | --- |
| `analysis_gamma = 1.0` in the recommended profile | inferred workaround based on current benchmark evidence, not directly observed |
| `bayer_mode = demosaic_red` | inferred current best-fit channel path, not directly observed |
| `ideal_psd_mode = calibrated_log` | inferred modeling choice |
| `reference_bins = true` with the current 64-bin centers | inferred modeling choice chosen to align sampling with the golden CSVs |
| fixed ROI sizes such as `1655 x 1673` in current profiles | inferred engineering approximation, not the same thing as observed golden `Crop` rows |
| `texture_support_scale` | inferred correction term |
| current Acutance noise compensation and print-display MTF models | inferred correction terms |

## Working Rule For Follow-up Issues

Future fitting and research issues should use this document as the boundary:

- observable fields define the target to match
- latent variables define the search space
- inferred assumptions are allowed as temporary engineering choices, but they must be labeled as assumptions

This is especially important for `Gamma = 0.5`: it is currently an observed report field, not a settled statement about the internal analysis exponent.
