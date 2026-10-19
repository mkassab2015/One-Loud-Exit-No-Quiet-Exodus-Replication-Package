# Statistic-to-Source Manifest

Every number reported in the paper, its source field, and the notebook
that produces it. All source files are provided in `data/` of this
package; a full pipeline run regenerates them in the Drive cache
(`MyDrive/msr2027/cache/`).

| Paper location | Statistic | Source | Producing notebook |
|---|---|---|---|
| Abstract, Sec. 4.1 | DiD ATT +0.0014, p=.84 | `data/results_panel.json: att, att_p` | 03 |
| Abstract, Sec. 4.1 | MDE 8.8% of base | `data/results_panel.json: mde_rel_base` | 03 |
| Sec. 4.1 | base rate 0.212 | `data/results_panel.json: base_monthly_rate` | 03 |
| Sec. 4.1 | leads 0/11 | `data/results_panel.json: lead_sig, n_leads` | 03 |
| Sec. 4.1, Fig. 2 | treated/control monthly release rates | `data/monthly_series.csv` | 05 |
| Sec. 4.1, Fig. 3 | event-study coefficients | `data/event_study_coefs.csv` | 05 |
| Sec. 4.1 | RDD +0.015, p=.89, n_eff 685 | `data/results_rdd.json: primary_*` | 02 |
| Sec. 4.1 | RDD MDE 53% | `data/results_rdd.json: mde_80pct / control_base_rate` | 02 |
| Sec. 4.2 | log releases +0.066, p=.62 | `data/results_extended.json: alternative_outcomes` | 04 |
| Sec. 4.2 | days-to-next −10.8, p=.73 | idem | 04 |
| Sec. 4.2 | sustained −0.0014, p=.85 | idem | 04 |
| Sec. 4.1 | abandonment +0.030, p=.65 | `data/results_extended.json: alternative_outcomes` | 04 |
| Sec. 4.3 | placebo-cutoff / donut / bandwidth / cohort grids | `data/robustness_grids.csv` | 05 |
| Sec. 4.3, Fig. 4 | specification estimates with robust CIs | `data/robustness_specs_ci.csv` | 05 |
| Sec. 4.3 | placebo timing −0.0101, p=.24 | `data/results_extended.json: placebo_timing` | 04 |
| Sec. 4.4, Tab. 4 | subgroup ATTs and MDEs | `data/results_extended.json: heterogeneity` | 04 |
| Sec. 4.5 | removals 3/1,062 vs 1/1,139, p=.36 | `data/results_extended.json: removal_outcome` | 04 |
| Sec. 3.2 | rho 0.95 / 0.86; 91.5% agreement | `data/validation.json` | 05 |
| Sec. 3.5, Fig. 1 | density ratio 0.949, p=.72 | `data/validation.json` | 05 |
| Tab. 1 | sample construction counts | `data/results_rdd.json`, `data/results_panel.json` | 02, 03 |
| Tab. 2 | balance estimates | `data/analysis_frame_rdd.parquet` (recompute) | 05 |
