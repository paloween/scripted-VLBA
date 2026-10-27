# Scripted VLBA Continuum Data Reduction

A CASA script skeleton for calibrating VLBA continuum data, modeled on the ALMA `scriptForCalibration.py` pattern (a numbered list of steps that can be run all together or selectively). It uses VLBI-appropriate CASA tasks (`importfitsidi`, `fringefit`, `accor`, `gencal` with `gc`/`tsys`/`eop`) in place of ALMA's WVR/ASDM-specific calls.

> **Status: skeleton, not runnable as-is.** The notebook is a design draft meant to be discussed and filled in against a specific Tier-1 dataset. Placeholders are marked `<FILL IN>` or `TODO`, and some blocks contain syntax errors and undefined variables (see [Known issues](#known-issues)).

## Contents

| File | Description |
|------|-------------|
| `VLBA_DataReduction_Script_py.ipynb` | Original design draft (notebook). Superseded by the script template. |
| `vlbapipe/templates/scriptForCalibration_VLBA.py` | The CASA script template (ALMA `scriptForCalibration.py` style). |
| `vlbapipe/scriptgen.py` | Script generator behind `vlbapipe generate`. |
| `examples/scriptForCalibration_TL016B.py` | Generated script for the TL016B test dataset. |

## Requirements

- CASA 6.6.x (the script header references 6.6.6.18). A version check is stubbed out in the script.
- Python packages available in CASA: `numpy` (used in steps 8 and 15).
- A FITS-IDI file (or several) from the correlator.
- An ANTAB file with Tsys and gain-curve information. EVN data need this appended to the FITS-IDI before import.
- Network access to download the USNO EOP file in step 3.
- Possibly `casavlbitools`, depending on how ANTAB import is handled (undecided, see the TODO in step 0).

## Usage

The script runs in monolithic CASA. Generate it from a YAML config (see `examples/TL016B.yaml`):

```bash
vlbapipe generate examples/TL016B.yaml --refant FD -o scriptForCalibration_TL016B.py
```

`--refant` is required when the config says `refant: auto`, because the standalone script has no refant heuristic. The generator fills in the parameter block of `vlbapipe/templates/scriptForCalibration_VLBA.py` and copies the rest unchanged. To change the processing itself, edit the template and regenerate.

Run all steps, or a selection (comma list and/or ranges):

```bash
casa --nologger --nogui -c scriptForCalibration_TL016B.py
casa --nologger --nogui -c scriptForCalibration_TL016B.py --steps 13-17
```

From the CASA prompt, pass `globals()` so the script can see `mysteps`:

```python
mysteps = [3, 4]
execfile('scriptForCalibration_TL016B.py', globals())
```

> **Warning:** a plain `execfile('script.py')` runs the script in CASA's own namespace. The script then never sees `mysteps` and runs **every** step, re-flagging and overwriting earlier products.

Each step finds the calibration tables it needs on disk, so a selective run applies everything derived by earlier runs.

## Processing steps

The steps map onto the planned `hiflb_*` MVP pipeline stages.

| Step | Description | Pipeline stage |
|------|-------------|----------------|
| 0 | Import FITS-IDI data (`importfitsidi`) | `hiflb_importdata` |
| 1 | `listobs` and metadata inspection; refant and timerange selection (TODO) | `hiflb_importdata` |
| 2 | A priori flagging: quack, `tfcrop`, manual flags | `hiflb_priorcals` |
| 3 | EOP correction; frequency-dependent ionosphere/opacity table | `hiflb_priorcals` |
| 4 | Autocorrelation amplitude (`accor`), Tsys and gain-curve tables | `hiflb_priorcals` |
| 5 | Antenna position table (`gencal` `antpos`, currently commented out) | `hiflb_priorcals` |
| 6 | Save flags (`BeforeFringefit`) | `hiflb_fringefit` |
| 7 | Instrumental (single-band) delay calibration | `hiflb_fringefit` |
| 8 | Global fringe fit (delay + rate) | `hiflb_fringefit` |
| 9 | Apply priorcals and fringefit to calibrators | `hiflb_bandpass` |
| 10 | Save flags (`BeforeBandpassCalibration`) | `hiflb_bandpass` |
| 11 | Bandpass calibration | `hiflb_bandpass` |
| 12 | Save flags (`BeforeApplycal`) | `hiflb_applycal` |
| 13 | Apply fringefit and bandpass tables to all fields | `hiflb_applycal` |
| 14 | Final amplitude scaling (`accor`, `smoothcal`) and `applycal` | `hiflb_applycal` |
| 15 | `split` out calibrated data | `hiflb_applycal` |
| 16 | Self-calibration of the science target or phase-reference calibrator | `hiflb_selfcal` |
| 17 | Quicklook imaging (`tclean`) | quicklook imaging |

Calibration tables are accumulated in the `gaintables` and `gc_tab_interp` lists, so later steps automatically apply everything derived earlier.

## Frequency regimes (step 3)

- **Below ~4.5 GHz:** ionosphere dominates. Intended to use `gencal(caltype='tecim')` with an IONEX file (not yet wired up).
- **Above ~15 GHz:** troposphere and opacity dominate. There is no native DELZN-equivalent term in CASA, so this is an open gap.
- **4.5 to 15 GHz:** unresolved regime. The script flags it rather than guessing.

## Known issues

The syntax errors, typos, undefined variables and step-numbering mismatches found in the first draft have been fixed, and the code cell now parses as valid Python. It has not been run in CASA. Remaining caveats:

- Placeholders (`<FILL IN>`, `refant`, `sbd_timerange`, calibrator names) must be set per dataset. Step 3's ionosphere/opacity branch is still commented out.
- The `.flagversions` check in step 0 is an ALMA leftover and may wrongly abort for FITS-IDI imports. Confirm it against a real import.
- Step 3 downloads the EOP file with `curl` from a NASA CDDIS FTP server, which may need credentials or network access. A failed download skips the EOP correction.
- Step 16 only implements the phase-reference path (`phase_ref_target: true`); direct self-cal of the target is a stub.
- Step 17 uses a fixed `image_cell`/`image_imsize` from the config rather than deriving them.
- Self-calibration S/N heuristic is not implemented.

## Open TODOs (from the script)

- Automatic reference-antenna selection (antennas present for most of the observation).
- Automatic selection of good time ranges for delay and bandpass calibration.
- Decide whether VLBA needs the ALMA-style online-flag step.
- Choose the ANTAB import tool (e.g. `casavlbitools`).
- Plotting and weblog hooks after each calibration table.
- Automated flagging of extreme Tsys solutions and bandpass edge channels.
- Per-intent `applycal` (calibrator, phase-ref, target) driven by `calibrator_assign.py`.
- Self-calibration S/N heuristic and loop.
- Derive imaging cell size from max baseline and observing frequency instead of hardcoding.
- Array generalization (e.g. ngVLA-LBA), where antenna position corrections may matter more.
