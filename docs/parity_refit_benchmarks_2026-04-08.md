# Parity Refit Benchmarks 2026-04-08

This note records the benchmark state reached for issue `#4` on `2026-04-08`.

Scope:

- target observable conditions from the golden CSVs
- `Gamma = 0.5`
- `Color channel = R`
- unnormalized MTF for Acutance
- full `Random / Dead Leaves` CSV outputs as the comparison target

The goal of this pass was to re-fit under the parity target rather than keep relying on the older non-parity baseline.

## Current parity baseline

Tested analysis path:

- `gamma = 0.5`
- `bayer_mode = demosaic_red`
- `ideal_psd_mode = calibrated_log`
- fixed centered ROI: `1655 x 1673`
- empirical noise PSD
- high-frequency-share quadratic Acutance noise scaling

Measured on the full `20260318_deadleaf_13b10` set:

- `curve_mae_mean = 0.13126369948174793`
- preset Acutance MAE:
  - `5.5" Phone = 0.027812329173867657`
  - `Computer Monitor = 0.17852791708556975`
  - `Large Print = 0.12280686519956494`
  - `Small Print = 0.10181796066338866`
  - `UHDTV = 0.13940892890235201`
- Quality Loss preset MAE:
  - `5.5" Phone = 0.5677944324669054`
  - `Computer Monitor = 14.821386669329353`
  - `Large Print = 8.526793150080538`
  - `Small Print = 6.256429142103515`
  - `UHDTV = 8.698401026035851`
- `overall_quality_loss_mae_mean = 7.774160884003233`

Baseline MTF residual summary:

- `low signed_rel_mean = -0.1019628113485191`
- `mid signed_rel_mean = -0.38469925271336475`
- `high signed_rel_mean = -0.7133118945815905`
- `top signed_rel_mean = -0.7599363328352176`

Interpretation:

- the parity path still suppresses mid/high/top-frequency MTF far too strongly
- the remaining error is not behaving like a small readout or ROI mismatch

## Tested follow-up variants

### Variant A: reuse the existing HF-noise-share gated shape correction

Change:

- enable `mtf_shape_correction_mode = hf_noise_share_gated_bump`
- reuse the current tuned gain/gates from the non-parity experiments

Result:

- `curve_mae_mean = 0.13120729088665492`

Interpretation:

- the change is real but negligible
- this is not a material parity improvement

### Variant B: use the observed reference ROI from each golden CSV

Change:

- benchmark scripts use `--roi-source reference`
- ROI comes directly from each CSV `L R T B` row instead of the fixed centered crop

Result:

- `curve_mae_mean = 0.13430841096729565`
- preset Acutance MAE:
  - `5.5" Phone = 0.033290996850892075`
  - `Computer Monitor = 0.18193174848982335`
  - `Large Print = 0.12794164833223248`
  - `Small Print = 0.10741718813251477`
  - `UHDTV = 0.144680004527268`

Interpretation:

- observable ROI alone does not fix the parity gap
- this variant is slightly worse than the fixed-ROI parity baseline

## What changed in code during this pass

- parity benchmark scripts now support `--roi-source {fixed,reference}`:
  - `algo/calibrate_acutance.py`
  - `algo/calibrate_quality_loss.py`
  - `algo/analyze_mtf_residuals.py`
- compatibility fixes were applied so the benchmark tools run in the current environment:
  - replace `zip(..., strict=False)` with plain `zip(...)`
  - replace `np.trapezoid(...)` with `np.trapz(...)`

These changes make the parity benchmark path reproducible in the current repo, but they do not solve the parity fit.

## Current conclusion

Issue `#4` is blocked at the model-family level, not at the parameter-tuning level.

Within the currently implemented reduced model family, the tested changes do not materially improve:

- MTF residual bands
- Acutance curve MAE
- preset MAEs
- Quality Loss MAE

The most likely next steps are to add one missing source-backed variable family before claiming a parity re-fit, especially one of:

1. OECF-driven linearization rather than a single scalar gamma
2. chart/sensor MTF compensation
3. intrinsic / full-reference dead-leaves method
4. more faithful registration/warp handling for that method

Until one of those families is added, `imatest_parity_profile.release.json` should be treated as a reference hypothesis profile, not a validated release candidate.
