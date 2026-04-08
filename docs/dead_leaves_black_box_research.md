# Dead Leaves Black-Box Research

This report inventories the formulas, intermediate variables, and candidate latent parameters that are likely to exist inside the Imatest `Random / Dead Leaves` pipeline, using official Imatest documentation and primary literature as the source base.

It is meant to be read after:

- [observable_target_from_golden_samples.md](./observable_target_from_golden_samples.md)
- [gamma_0_5_hypothesis_matrix.md](./gamma_0_5_hypothesis_matrix.md)

The practical goal is to keep future fitting work aimed at a realistic parameter space instead of overfitting a reduced or incorrect abstraction.

## Source Summary

### Imatest / standards-facing sources

1. Imatest `Random / Dead Leaves` documentation:
   - <https://www.imatest.com/docs/random/>
   - Documents the PSD-based `Direct` method, the chart-MTF exponent setting, scale-invariant `1/f` MTF and `1/f^2` PSD assumptions for Spilled Coins, gray-side noise PSD subtraction, ROI handling, and the note that demosaicing is a major cause of divergence between Spilled Coins and slanted-edge MTF.
2. Imatest `Random-Cross` documentation:
   - <https://www.imatest.com/docs/random-cross/>
   - Documents the cross-correlation / intrinsic approach considered for ISO 19567-2, reference-image usage, automatic registration, and the fact that this method is full-reference rather than semi-reference.
3. Imatest acutance / SQF documentation:
   - <https://www.imatest.com/support/docs/25-1/acutance-and-sqf-subjective-quality-factor/>
   - Documents Acutance/CPIQ display conditions, CSF-based integration in cycles/degree, `Normalize MTF`, display-type MTF assumptions, preset view conditions, and JND quality-loss interpretation.
4. IS&T standards page for ISO 15739 and ISO/TS 19567-2:
   - <https://www.imaging.org/IST/IST/Standards/Digital_Camera_Noise_Tools.aspx>
   - Documents that ISO 15739 handles visual noise and that ISO/TS 19567-2 uses an intrinsic stochastic-pattern texture approach.
5. Imatest chart/sensor MTF compensation documentation:
   - <https://www.imatest.com/docs/mtf-compensation/>
   - Documents chart MTF compensation, approximate sensor MTF compensation, and the decomposition of measured system MTF into chart, lens, sensor, and image-processing terms.
6. Imatest general gamma / OECF notes:
   - <https://www.imatest.com/docs/imatest.html>
   - Documents that gamma is used to linearize input data, that OECF/contrast settings can shift effective gamma, and that measured gamma from Stepchart/Colorcheck is preferred to a nominal constant.

### Primary literature

1. Cao, Guichard, Hornung, “Dead leaves model for measuring texture quality on a digital camera” (SPIE 2010):
   - <https://corp.dxomark.com/wp-content/uploads/2017/11/Dead_Leaves_Model_EI2010.pdf>
   - Gives the classical dead-leaves texture-MTF framing: per-channel linearization by inverse OECF, FFT-domain texture MTF, and the motivation that texture sharpness differs from edge sharpness under denoising/sharpening.
2. McElvain, Campbell, Miller, Jin, “Texture-based measurement of spatial frequency response using the dead leaves target: extensions, and application to real camera systems” (SPIE/IS&T 2010):
   - <https://www.imaging.org/common/uploaded%20files/pdfs/Reporter/Articles/2010_25/Rep25_2_EI2010_MCELVAIN.pdf>
   - Shows that ideal dead-leaves PSD is not a simple global power law over the full range, scale invariance is only approximate, and explicit correction terms for captured image size and system noise may be needed.
3. Artmann, “Image quality assessment using the dead leaves target: experience with the latest approach and further investigations” (SPIE 2015):
   - <https://www.image-engineering.de/content/library/conference_papers/2015_03_13/EIC2015_9404-18.pdf>
   - Argues for the intrinsic/full-reference approach, highlights the importance of phase information, and shows that sharpening can inflate dead-leaves SFR metrics enough that a single number may mis-rank visual quality.
4. Fry et al., “Validation of Modulation Transfer Functions and Noise Power Spectra from Natural Scenes” (arXiv 2019):
   - <https://arxiv.org/abs/1907.08924>
   - Places dead-leaves texture analysis in the broader context of scene- and process-dependent MTF/NPS, which is relevant because modern ISP pipelines are nonlinear and content-aware.

## Working Model Of The Black Box

The sources collectively imply a pipeline with at least these conceptual stages:

1. Input representation and linearization
   - raw or processed image enters the measurement path
   - OECF / gamma / tonal state must be handled before texture analysis
   - channel selection matters
2. Chart localization and registration
   - crop / ROI definition
   - possibly automatic ROI detection
   - possibly full projective / subpixel registration against a reference pattern
3. Texture and noise spectrum estimation
   - signal+noise PSD from the stochastic texture region
   - noise PSD from side patches or another reference region
   - chart prior or reference texture model
4. Texture MTF / SFR estimation
   - either direct/semi-reference PSD-ratio method
   - or intrinsic/full-reference cross-correlation method
5. Readout and perceptual mapping
   - `MTFnn` or threshold readouts
   - Acutance integration under viewing conditions
   - Quality Loss / JND mapping

The project already models parts of every stage, but it does not yet cover every source-backed variable family.

## Parameter Inventory

| Variable | Role in pipeline | Source | Currently modeled in repo? | Likely observable vs latent | Notes |
| --- | --- | --- | --- | --- | --- |
| image dimensions | define the analyzed sampling grid | golden CSVs + parser | yes | observable | Already read from golden samples |
| chart family / configuration | selects chart geometry and side regions | Imatest Random docs | partial | latent | Repo assumes one dataset/chart family rather than a general chart taxonomy |
| crop / ROI bounds | chooses analysis aperture | golden CSVs + Imatest Random docs | yes | observable output + latent policy | Reported bounds are observable; search/refinement policy is latent |
| automatic ROI detection mode | determines crop acquisition path | Imatest Random docs | partial | latent | Repo has ROI detection and fixed-size override, but not full Imatest mode matrix |
| registration-mark geometry | supports robust crop / warp estimation | Imatest Random / Random-Cross docs | partial | latent | Repo uses support/ROI logic, not cross-reference registration marks |
| reference-image warp / alignment | aligns observed pattern to true pattern for intrinsic method | Imatest Random-Cross + Artmann 2015 | no | latent | Major missing method family |
| analysis gamma / OECF inversion | linearizes image prior to Fourier analysis | Imatest gamma docs + Cao 2010 | partial | latent | Repo models scalar gamma, but not LUT/inverse OECF from chart patches |
| measured gamma from chart patches | estimates tonal linearization from grayscale patches | Imatest gamma docs | no | latent/intermediate | Important missing variable family for parity work |
| color channel selection | selects luminance / R / G / B path | Imatest gamma docs + Cao 2010 | yes | partly observable | Golden CSV shows `R`, but internal channel pipeline remains latent |
| Bayer / demosaic path | affects texture-vs-noise behavior | Imatest texture examples | yes | latent | Repo explicitly models `gray`, `demosaic_red`, `raw_red_upsampled` |
| chart ideal PSD / chart-MTF prior | supplies the reference stochastic target spectrum | Imatest Random docs + Cao 2010 + McElvain 2010 | yes | latent | Repo currently uses empirical or simplified priors |
| chart MTF exponent | controls direct-method reference slope | Imatest Random docs | partial | latent | Repo approximates this through PSD models rather than exposing Imatest’s chart-exponent concept directly |
| chart scale / captured image size correction | stabilizes dead-leaves analysis across magnification | McElvain 2010 | partial | latent | Repo has `texture_support_scale`, but not the same explicit source-backed formulation |
| reference frequency bins | determines readout grid | repo-specific calibration history | yes | latent/intermediate | Useful engineering alignment, but not directly documented by sources as Imatest internals |
| signal+noise PSD | texture-region spectral measurement | Imatest Random docs | yes | observable output / latent intermediate | Present in CSV outputs and repo |
| noise PSD reference region | side-patch noise estimate | Imatest Random docs + ISO 15739 background page | yes | latent/intermediate | Repo estimates this from noise patches and subtracts it |
| noise subtraction formula | derives signal PSD or noise-corrected MTF | Imatest Random docs + McElvain 2010 | yes | latent/intermediate | Repo models this, but exact Imatest implementation details remain unknown |
| direct vs cross / intrinsic method | chooses semi-reference PSD approach vs full-reference approach | Imatest Random-Cross + Artmann 2015 | partial | latent | Repo currently implements a direct-style family, not the intrinsic full-reference method |
| phase retention | robustness to noise/artifacts in intrinsic method | Artmann 2015 | no | latent | Missing because repo does not yet implement the intrinsic method |
| demosaicing nonlinearity | distorts high-frequency texture-vs-noise relation | Imatest texture examples | partial | latent | Repo experiments with channel extraction, but not a broader demosaic model family |
| denoising strength / scene dependency | changes texture loss differently from edge response | Imatest Random docs + Fry 2019 | partial | latent | Repo fits outcomes from processed images but does not explicitly parameterize scene-dependent ISP state |
| sharpening / overshoot policy | can inflate MTF peaks and distort one-number rankings | Imatest acutance docs + Artmann 2015 | partial | latent | Repo has readout and shape-correction heuristics, but not a first-principles sharpening model |
| MTF normalization policy | low-frequency anchor / max normalization / peak normalization | Imatest Random docs + acutance docs | yes | latent/intermediate | Repo exposes normalization and separate unnormalized-vs-normalized MTF handling |
| `Normalize MTF` for Acutance | optional suppression of sharpening peaks before acutance | Imatest acutance docs | partial | latent | Repo intentionally preserves unnormalized MTF in the current path because the CSV says to use it |
| `MTFnn`, `MTFnnP` readout policy | converts curve to thresholds | Imatest Random docs | yes | observable outputs + latent interpolation policy | Repo models smoothing/interpolation heuristics |
| display / print type | determines display-medium MTF for Acutance | Imatest acutance docs | partial | latent | Repo has explicit print-display MTF approximations |
| viewing geometry | maps cycles/pixel to cycles/degree | Imatest acutance docs | yes | latent/intermediate | Repo models preset geometries |
| CSF function and acutance integral | perceptual weighting from MTF to acutance | Imatest acutance docs | yes | latent/formula | Repo already uses a CPIQ-style CSF/integral path |
| preset view conditions | standardized CPIQ display/print scenarios | Imatest acutance docs | yes | observable output + latent internal defaults | Repo models the five presets, but exact Imatest internal medium MTF may differ |
| Quality Loss / JND mapping | converts acutance to perceptual loss | Imatest acutance docs | partial | latent/formula | Repo uses an empirical quadratic mapping; exact CPIQ implementation path should be treated as not fully settled |
| chart MTF compensation | removes chart-medium blur from measured MTF | Imatest MTF compensation docs | no | latent | Important missing variable family |
| sensor MTF / OLPF compensation | separates sensor effects from lens/system MTF | Imatest MTF compensation docs | no | latent | Important missing variable family |

## Variables The Repo Already Models Well Enough To Be Useful

The current prototype already has strong engineering coverage for:

- ROI extraction and fixed crop override
- channel-path experiments (`gray`, red-channel variants)
- direct-method PSD-to-MTF estimation
- noise PSD subtraction
- empirical ideal-PSD fitting
- readout smoothing / interpolation
- Acutance presets, display MTF approximations, and quality-loss fitting

That is enough to build useful parity experiments, but not enough to claim the parameter space is complete.

## Important Missing Variable Families

These are the highest-priority gaps exposed by the source review:

1. OECF-driven linearization rather than a single scalar gamma
   - Imatest’s broader documentation repeatedly ties MTF linearization to gamma/OECF measurement from chart patches, not just a constant exponent.
2. Full-reference / intrinsic dead-leaves method
   - The cross/intrinsic approach keeps reference-image phase information and is explicitly presented by Imatest as a separate method family.
3. Chart-MTF and sensor-MTF compensation
   - Official Imatest documentation treats measured MTF as the product of chart, lens, sensor, and processing terms.
4. Registration warp accuracy for intrinsic methods
   - The cross method depends on accurate warp/registration, not just a rectangular crop.
5. Scene-/process-dependent ISP state
   - Fry 2019 and Imatest’s texture examples both reinforce that nonlinear, content-aware processing changes texture measurements in ways that do not collapse cleanly to one static MTF.

## Implications For Issue #4

The parity re-fit issue should not assume the remaining error is only a matter of retuning:

- ideal PSD coefficients
- frequency scale
- ROI size
- noise subtraction gain

Those are only a subset of the plausible parameter space.

The missing-source-backed families most likely to change the parity target are:

- OECF / measured linearization
- direct vs intrinsic method choice
- chart/sensor compensation
- registration accuracy
- nonlinear ISP behavior affecting texture differently from edges and flat noise

## Practical Guidance For Follow-up Work

For future implementation and fitting issues, use this report as the inventory boundary:

- if a variable appears in the table as `no`, the repo is currently omitting a source-backed part of the plausible black box
- if a variable is `partial`, the repo has an engineering approximation but not necessarily the full source-backed formulation
- parity-fit claims should be careful not to confuse the current engineering approximation with a validated reconstruction of Imatest internals

That means the next fitting step should either:

1. explicitly stay within the current reduced model family and say so, or
2. add one of the missing variable families before claiming a stronger parity interpretation
