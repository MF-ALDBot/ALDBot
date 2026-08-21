# ALDBot

Instrument-control code for the automated PE-ALD (plasma-enhanced atomic layer deposition) reactor described in:

> **An automated materials acceleration platform for active-learning-driven atomic layer deposition**
> M.B. Alghalayini\*, T. Kodalle\*, A. Gashi, A. Razumtcev, M. Surendran, S. Aloni, A.M. Schwartzberg, E.S. Barnard
> *Digital Discovery*, 2026 (DOI: TBD)

This repository is the [ScopeFoundry](https://github.com/ScopeFoundry/ScopeFoundry)-based application that runs the experimental components of ALDBot: it drives the gas/vacuum/RF hardware through a fixed ALD cycle state machine, reads growth rate in situ via spectroscopic ellipsometry, and — for active-learning campaigns — queries a Gaussian process (GP) model after every experiment to choose the next set of process parameters. Post-campaign analysis (RMSE, information gain, SHAP) is done separately in [Raw_Data_Analysis](https://github.com/MF-ALDBot/Raw_Data_Analysis), which consumes the JSON/HDF5 output produced here.

## Hardware controlled

| Component | Role | ScopeFoundry plugin (submodule) |
|---|---|---|
| Automation Direct Productivity1000 PLC | Modbus TCP control of ALD/plasma valves, MFC setpoints, substrate heater PID, high-pressure interlock | `ScopeFoundryHW/productivity_plc` |
| VAT throttle valve | Chamber pressure control (process & plasma pressure setpoints) | `ScopeFoundryHW/vat_throttle` |
| Seren RF power supply + MC2 matching network | O₂ plasma generation and impedance matching (LC/TC presets) | `ScopeFoundryHW/seren_rf` |
| Pfeiffer MaxiGauge + MPT200 | Chamber and gas-line pressure gauges | `ScopeFoundryHW/pfeiffer_vgc` |
| FilmSense FS8 ellipsometer | In situ spectroscopic ellipsometry — per-cycle film thickness → growth rate | `ScopeFoundryHW/filmsense_ellipsometer` |
| Ocean Optics spectrometer | Optical emission spectroscopy (OES) during the plasma step (optional, not used in the study cited above) | `ScopeFoundryHW/oceanoptics_spec` |
| Pico TC-08 | Precursor line/bottle thermocouple monitoring | `ScopeFoundryHW/pico_tc08` |
| InfluxDB | Time-series logging of live instrument settings | `ScopeFoundryHW/data_streamer` |
| MF crucible | Optional connection to Crucible, the Molecular Foundry's data management platform | `ScopeFoundryHW/mf_crucible` |

All hardware plugins, plus ScopeFoundry itself, are pulled in as git submodules — see [Installation](#installation).

## Repository structure

```
ALDBot/
├── aldbot_app.py                      # ScopeFoundry app entry point; registers all hardware & measurements
├── aldbot_defaults.ini                # Instrument connection defaults (COM ports, IP addresses) loaded at startup
├── ald_run_measure.py                 # Core ALD cycle experiment control (MO dose/purge, plasma dose/purge, per-cycle ellipsometry read)
├── ald_gui.py                         # Manual control panel UI (valves, MFCs, gauges, RF supply, PLC I/O)
├── ald_robot_measure.py               # Closed-loop active-learning campaign driver (GP-recommended parameters)
├── ald_robot_random_exps.py           # Random-sampling campaign driver (baseline for comparison against active learning)
├── ald_robot_fixedParams_exps.py      # Fixed-parameter repeat-experiment driver
├── ald_param_sweep_measure.py         # Single-parameter validation sweep driver (used for the Fig. 3b–d sweeps)
├── ald_data_processing.py             # Parses a run's .h5 + FilmSense .txt export into a per-run growth-rate summary
├── aldbot_logger_measure.py           # Background gauge-pressure logging/plotting
├── aldbot_gui.ui / aldrun_ui.ui        # Qt Designer layouts for the manual control panel and run panel
├── aldbot_plc_firmware.adpro,
│   aldbot_plc_firmware_Basic.csv,
│   aldbot_plc_firmware_Extended.csv   # Productivity1000 PLC ladder-logic project and Modbus tag maps
├── image_print.py                     # QR-code sample-ID label generation/printing for physical sample tracking
├── models/
│   ├── gpmodel_base.py                 # Shared GP base class (gpCAM, ARD Matérn-3/2 kernel, training, RMSE, posterior)
│   ├── gpmodel_constant_PriorMean.py   # Constant prior-mean GP
│   ├── gpmodel_ald_PriorMean.py        # Physics-informed prior mean (piecewise ellipsoidal "ALD window", not used in this study)
│   ├── get_new_points_with_gp.py       # Fits the GP, proposes the next point (variance/uncertainty acquisition), computes RMSE
│   ├── random_exploration.py           # Drop-in replacement for the GP optimizer that samples uniformly at random
│   └── old/                            # Deprecated earlier optimizer implementations, kept for reference only
├── notebooks/                          # Exploratory/development notebooks with hardcoded local paths; not needed to reproduce paper results — see Raw_Data_Analysis
├── zmq_comms/                          # Optional ZeroMQ client/server for offloading GP fitting to a remote worker
├── ScopeFoundry/                       # git submodule: ScopeFoundry instrument-control framework
├── ScopeFoundryHW/                     # git submodules: one per hardware plugin (see table above)
├── sample_id.json                      # Log of generated sample IDs
└── pyproject.toml / uv.lock            # Python dependencies (uv)
```

## The ALD cycle

Each experiment runs a fixed number of ALD cycles (`Number_of_ALD_cycles`, 25 in this study), where each cycle consists of a metal-organic (TDMAT) half-cycle followed by a plasma half-cycle. The per-cycle parameters exposed as `ald_run_measure` settings are:

| Step | Parameter | Description |
|---|---|---|
| MO prep | `ALD_prep_time` | Time to stabilize process pressure/Ar flow before precursor dose |
| MO dose | `precursor_dose_time` | TDMAT dose valve open time |
| | `ald_valves_delay` | Delay between dose and purge valve actuation |
| | `process_pressure` | Chamber pressure setpoint during the precursor half-cycle |
| | `Ar_process_flow_rate` | Ar carrier flow during the precursor half-cycle |
| MO purge | `precursor_purge_time` / `ALD_purge_time` | Post-dose purge duration |
| | `ALD_purge_flow_rate` | Ar purge line flow rate |
| Plasma prep | `plasma_prep_time` | Time to stabilize plasma pressure/gas flows before striking plasma |
| | `plasma_pressure` | Chamber pressure setpoint during the plasma half-cycle |
| Plasma dose | `plasma_duration` | RF-on exposure time |
| | `RF_power_setpoint` | Forward RF power |
| | `H2_plasma_flow_rate`, `N2_plasma_flow_rate`, `Ar_plasma_flow_rate` | Plasma gas flow rates - note that this study used O2 instead of H2, and did not use N2 |
| | `LC_preset`, `TC_preset` | Matching network capacitor presets |
| Plasma purge | `plasma_purge_time` | Post-plasma purge duration |
| | `ALD_purge_plasma_flow_rate` | Ar purge flow used during the plasma purge |

Film thickness is read from the FilmSense ellipsometer once per cycle; growth rate is derived from consecutive thickness readings in `ald_data_processing.py`.

## Campaign modes

`aldbot_app.py` registers four campaign-driver measurements, each of which repeatedly runs `ald_run_measure` with a different strategy for choosing parameters and writes a single `<campaign_uuid>_aldbot_campaign_output.json` at the end:

| Measurement | Driver script | Parameter selection |
|---|---|---|
| `ald_robot` | `ald_robot_measure.py` | Active learning: after every run, fits the configured GP model (`models/get_new_points_with_gp.py`) to all data so far and asks gpCAM for the next point via a variance (uncertainty-sampling) acquisition function |
| `ald_robot_rng` | `ald_robot_random_exps.py` | Random sampling baseline: draws all points up front, uniformly at random over the configured parameter grid |
| `ald_robot_fixed` | `ald_robot_fixedParams_exps.py` | Repeats a single fixed parameter set (`config['params']`) for `num_runs` experiments |
| `ald_robot_sweep` | `ald_param_sweep_measure.py` | Sweeps one parameter at a time over a linear grid (starting from the middle and alternating outward), all other parameters held fixed — used for the independent validation sweeps |

Each driver is configured with a JSON file (`campaign_config_file` setting) specifying, among other things, `modeled_params`, `param_limits`, `model_output_param`, `output_deviation_variable`, `num_runs`, `num_RMSE_trials`, and — for `ald_robot` — the import paths (`module:ClassName`) of the GP model (`gp_model`) and optimizer function (`optimizer`) to use, and a `prior_datasets_dir` of prior `.h5` runs to seed the model with.

## Installation

Requires Python 3.13 and [uv](https://github.com/astral-sh/uv).

```bash
# Clone with submodules (ScopeFoundry + all hardware plugins)
git clone --recurse-submodules <repo-url>
cd ALDBot

# If already cloned without submodules:
git submodule update --init --recursive

# Install dependencies
uv sync
```

Instrument addresses (serial ports, PLC IP, InfluxDB URL) are configured in `aldbot_defaults.ini`, which is loaded at startup via `settings_load_ini`.

## Usage

```bash
uv run python aldbot_app.py
```

This launches the ScopeFoundry GUI with:
- **`ald_ui`** — manual hardware control panel (valves, MFCs, RF supply, matching network, PLC readouts)
- **`ald_run`** — single-run control panel with live ellipsometry thickness plot
- **`ald_robot` / `ald_robot_rng` / `ald_robot_fixed` / `ald_robot_sweep`** — campaign drivers, each pointed at a campaign config JSON via its `campaign_config_file` setting

Live instrument state and per-run measurements are saved as timestamped HDF5 files (via `ScopeFoundry.h5_io`); campaign-level metadata and results are saved as JSON. Both feed into the `Raw_Data_Analysis` repository's processing pipeline.


## Citation

If you use this code, please cite:

```
@article{alghalayini2026aldbot,
  title   = {An automated materials acceleration platform for active-learning-driven atomic layer deposition},
  author  = {Alghalayini, Maher B. and Kodalle, Tim and Gashi, Arian and Razumtcev, Aleksandr and Surendran, Mythili and Aloni, Shaul and Schwartzberg, Adam M. and Barnard, Edward S.},
  journal = {Digital Discovery},
  year    = {2026},
  doi     = {TBD}
}
```

## License

BSD 3-Clause License. See [LICENSE](LICENSE).
