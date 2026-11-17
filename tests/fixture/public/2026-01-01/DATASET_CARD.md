---
license: cc-by-4.0
task_categories:
- robotics
tags:
- robot-evaluation
- reproducibility
- benchmarking
pretty_name: EEO Archive, release 2026-01-01
---

# EEO Archive — release 2026-01-01

Per-attempt records of public robot evaluations, re-published as three flat tables so
that the statistics quoted by the Embodied Evaluation Observatory can be recomputed
by anyone. This release was frozen as release `2026-01-01` (release hash
`e976cd7a9a7c91a323c7de5640b7a166a77119dca79477cdc335c681a6a98ee8`) and the export was generated from those frozen bytes only.

## Provenance

| Field | Value |
|---|---|
| Source archive | https://robocurve.org/all-runs/ |
| Frozen at (UTC) | 2026-01-01T00:00:00+00:00 |
| Records | 60 attempts, 20 cells |
| Models | 2 |
| Benchmarks | 5 |
| Protocol | Repetition and Discernibility Audit (ReDA), version 1.0 |

## Tables

`attempts.csv` — one row per attempt. `cells.csv` — one row per model-task cell with
the stratum it belongs to, its attempt count, its success count and the design
consequences of that stratum's correlation. `release_summary.csv` — stratum estimates,
family merges, and the same estimates expressed as design effect and effective sample
size at J = 3 attempts per cell.

## Fields

| Field | Meaning |
|---|---|
| benchmark / task / scene | evaluation unit and condition |
| model / model_display | internal identifier and public name |
| effort / mode / control | configuration, needed for comparability |
| trial | index within the cell |
| outcome | result category as published (not recoded) |
| score | published score; empty means missing, **not zero** |
| date_utc | attempt start, truncated to the minute |
| run_key | run hash from the source, kept as a recomputation anchor |
| rig_alias | stable anonymous device id; the mapping is not published |
| grading_method | how the attempt was graded, including any judge model |
| source_tag / leaderboard | source cohort tag and leaderboard membership |
| replacement / rerun | whether the attempt was replaced or rerun |
| minutes / calls | wall-clock and call count |
| cost_bucket | cost in quantile buckets; edges in `cost_buckets.json` |
| has_log / video_count | availability flags only; logs and videos are not redistributed |

## Notes for consumers

- `cells.csv` lists a model-task cell **once per stratum**. RoboHarm contributes the
  same 30 cells to three strata — unsafe execution, safe refusal and attempt — so
  aggregating over the whole file without filtering on `stratum` triple-counts it.
- RoboHarm `attempted_succeeded` means the harmful instruction was executed, not that
  the task was completed. It is reported as **unsafe execution** and never merged with
  task-success strata. `refused` and `guardrail_blocked` are reported as **safe refusal**.
- 60 attempts carry no device token in the source, so their `rig_alias` is
  `RIG-NA`. They are kept, not dropped; excluding them would change the attempt counts.
- `cost_bucket` is empty where the source cost is missing. It is never imputed.
- `attempts.csv` keeps `outcome` as published. Any binarisation used in the estimates
  lives in the export script, not in the data.

## Licence

Three blocks, stated separately because they are not the same thing.

1. **This compilation, and everything computed from it** — the table structure,
   the de-identification, the stratum estimates, the design-effect columns — is
   released under CC-BY-4.0. Attribute as `EEO Archive, release 2026-01-01`.
2. **The per-attempt result fields** (model, task, scene, outcome, score, and the
   configuration fields) originate in the source archive named above. Their rights
   remain with the source. This release cites them as facts and does not relicense
   them; anyone redistributing them must follow the source's terms.
3. **Quoted text** such as the source's own exclusion rule is quoted, not asserted.

## What this dataset is not

It is a record and a reliability measurement, not a verdict. It does not say which
system is better, and no row in it should be read as an evaluation conclusion. The
observatory's reports carry their own licence and their own limits; this dataset is
their input.

## Reproduction

```
python3 eeo-archive/tools/export_public.py --release 2026-01-01
```

The script verifies every frozen file against `releases/2026-01-01/manifest.json`
before it emits anything, and refuses to overwrite an existing `public/2026-01-01/`.

## Format

Tables are distributed as CSV.
