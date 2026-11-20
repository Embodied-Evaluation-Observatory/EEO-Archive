# Sensitivity and per-stratum intervals, 2026-11-17

This file answers two questions the release left open. Neither changes
`public/2026-11-17/release_summary.csv`; both are computed from it and from `attempts.csv`.

Reproduce: `python3 tools/sensitivity.py --release 2026-11-17 --reps 2000`

## 1. Where the pooled rho comes from

The published estimates are reproduced exactly before any exclusion (family rho
perf 0.5025, att 0.6707, safety 0.6229; CIs unchanged), so the re-baseline is sound.
Dropping cells whose outcome is constant (0% or 100% of attempts) moves them:

| Family | Published rho | Excluding constant cells | Change |
|---|---|---|---|
| completion | 0.5025 | 0.3452 | -0.157 |
| attempt | 0.6707 | 0.2610 | -0.410 (3 of 4 strata kept) |
| safety | 0.6229 | 0.2932 | -0.330 |

Per stratum:

| Stratum | rho | Excluding constant cells | 95% CI (bootstrap over cells) |
|---|---|---|---|
| RoboDojo-RC task success | 0.501 | 0.337 | 0.320–0.636 |
| Simple-tasks task success | 0.531 | 0.516 | 0.000–0.804 |
| RoboHarm unsafe execution | 0.448 | 0.338 | 0.306–0.580 |
| RoboHarm safe refusal | 0.752 | 0.247 | 0.522–0.902 |
| RoboSpoof attempt (unaltered) | 0.484 | 0.148 | 0.250–0.671 |
| RoboSpoof attempt (blurred) | 0.654 | 0.383 | 0.046–0.860 |
| RoboSpoof attempt (doctored) | 0.727 | — (all cells constant) | 0.000–0.727 |
| RoboHarm attempt | 0.752 | 0.247 | 0.514–0.909 |

Reading: the pooled rho is carried largely by cells in which every attempt has the same
outcome. Between-cell differences in difficulty then dominate the intraclass correlation,
so the number describes how spread out the tasks are as much as how repeatable the
measurement is. Excluding those cells roughly halves it. That is not an argument to change
the published number — the published rule was fixed in advance and stays — but it is an
argument to stop reading rho as a repeatability coefficient without saying which cells
carried it.

## 2. Cells at the boundary

104 of 268 cells are at 0%, 67 at 100%, 97 in between. Nine of the 0% cells have 30 or more
attempts. These are capability boundaries, not measurement noise: no recorded attempt
succeeded. They are the natural first target for source attribution, because "always fails"
has exactly one plausible cause set — policy, harness, or task impossibility — and
distinguishing them does not require correlation analysis.

## Limit

The bootstrap resamples cells within a stratum and treats a cell as the sampling unit. It
therefore reflects between-cell sampling variation, not the within-cell attempt sampling
that `deff_cell` describes. The two intervals answer different questions and should not be
compared numerically.
