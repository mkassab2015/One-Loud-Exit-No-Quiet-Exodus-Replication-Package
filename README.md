# Replication Package
## One Loud Exit, No Quiet Exodus: The Causal Effect of PyPI's Two-Factor Authentication Mandate on Maintainer Activity

*(Anonymized for double-anonymous review.)*

This repository contains the complete, executable pipeline for the study.
Everything runs end to end on **Google Colab** (free tier); no credentials
are required. All inputs are public: the ClickHouse public mirror of PyPI
download statistics, PyPI's JSON and PEP 691 APIs, `pypi/warehouse` at
commit `542f745f2`, and the `top-pypi-packages` snapshot at commit `dd326bf`.

## Pipeline

Run the notebooks in numerical order. Every cell verifies its
prerequisites; every collection step is crash-safe and resumable
(`src/msr_resume.py`, embedded as Cell 0 where used), and all intermediate
state is checkpointed to Drive under `MyDrive/msr2027/cache/`.

| Notebook | Purpose | Paper |
|---|---|---|
| `01_treatment_assignment_and_design_checks` | Re-execute the designation query; validate against an independent ranking; exclude always-takers; manipulation and balance tests | Sec. 3.2, 3.5 |
| `02_rdd_outcomes_and_robustness` | Outcome diagnosis; pre-specification; full band collection; RDD estimates, robustness grids, power | Sec. 3.3-3.5, 4 |
| `03_panel_event_study` | Monthly rankings and late-entrant exclusion; monthly panel; pooled DiD and dynamic event study | Sec. 3.6, 4.1 |
| `04_heterogeneity_and_falsification` | Subgroup estimates with per-subgroup MDEs; alternative outcomes; removal analysis; placebo timing | Sec. 4.2-4.5 |
| `05_export_results` | Rebuild all frames from cache; export every reported number, series, and coefficient | all exhibits |

All exported outputs are provided in `data/` (headline results in
`results_rdd.json`, `results_panel.json`, `results_extended.json`) and the
camera-ready figures in `figures/`. `MANIFEST.md` maps every statistic
reported in the paper to its source field and producing notebook;
`data/README.md` describes each file and distinguishes the files shipped
here from the large raw caches a full run regenerates on Drive.

`prespec/PRESPEC_20260819.json` is the timestamped pre-specification,
written before any outcome was estimated (paper Sec. 3.4) and unaltered.

## Approximate runtimes (free Colab)
Notebook 01: ~15 min · 02: ~45 min · 03: ~45 min · 04: ~10 min · 05: ~5 min.
Interrupted runs resume where they stopped.

## Licenses
Code: MIT. Data and derived datasets: CC BY 4.0.
