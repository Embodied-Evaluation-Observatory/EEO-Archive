# Comparability key and stratification, release 2026-11-19

The cell key is `model + task + scene`. Where a cell also varies on `grading_method`, `source_tag`, `effort` or `mode`, the split is published in `by_key.csv` but the headline estimate stays pooled: most split keys hold one or two attempts and an ICC over them is unstable.

| Stratum | cells | full keys | cells split by the four fields | rho (cell key) | rho (full key) |
|---|---|---|---|---|---|
| RoboDojo-RC task success | 96 | 113 | 17 (18%) | 0.5013 | 0.5380 |
| RoboHarm attempt | 32 | 36 | 4 (12%) | 0.8167 | 0.8150 |
| RoboHarm safe refusal | 32 | 36 | 4 (12%) | 0.8167 | 0.8150 |
| RoboHarm unsafe execution | 32 | 36 | 4 (12%) | 0.4841 | 0.4918 |
| RoboSpoof attempt (blurred) | 25 | 25 | 0 (0%) | 0.6538 | 0.6538 |
| RoboSpoof attempt (doctored) | 25 | 25 | 0 (0%) | 0.7273 | 0.7273 |
| RoboSpoof attempt (unaltered) | 25 | 26 | 1 (4%) | 0.4838 | 0.4842 |
| Simple-tasks task success | 7 | 11 | 2 (29%) | 0.5308 | 0.5392 |

Field composition of attempts (top levels):

| Field | levels | most frequent |
|---|---|---|
| grading_method | 8 | Autograded (2108), Claude Fable 5.1 refusal judge (899), Astra autograde (695), Report score (471), Autograded (re-graded, old rubric) (25), Human label (20) |
| source_tag | 19 | robospoof-2026-10-27 (900), roboharm-latest-2026-10-01 (600), leaderboard-2026-09-29 (480), gpt-6-sol-report (331), datacenterbench-2026-10-22 (270), vla-baselines-2026-10-16 (240) |
| effort | 8 | high (2330), medium (1069), vla (360), max (330), budget-8k (40), none (40) |
| mode | 7 | standard (1451), fast (1190), not-recorded (698), ultrafast (420), self-hosted (240), priority (120) |

## Zero-capability frontier

9 cells sit at 0% with at least 30 attempts (106 at 0% overall, 100 in between, 68 at 100%). Every recorded attempt failed, so they are boundaries rather than noise, and they carry no information about correlation. `frontier.csv` lists them.

Zero by benchmark: {"robodojo-rc-tier-1": 7, "roboharm-v1": 2}.

## Provenance probe

- `duplicate_records` — computed; {"duplicates": 0, "rate": 0.0}
- `identical_outcome_vectors` — partial; {"pairs": 627}
- `temporal_clustering` — partial; {"max_per_minute": 9, "max_per_benchmark": {"robodojo-rc-tier-1": 6, "roboharm-v1": 5, "simple-tasks": 3, "datacenterbench": 5, "robospoof": 9}}
- `share_concentration` — computed; {"by_benchmark": {"robodojo-rc-tier-1": {"trials": 2151, "top_model_share": 0.1116}, "datacenterbench": {"trials": 270, "top_model_share": 0.1111}, "roboharm-v1": {"trials": 698, "top_model_share": 0.2006}, "robospoof": {"trials": 900, "top_model_share": 0.2}, "simple-tasks": {"trials": 220, "top_model_share": 0.4545}}}
- `score_outcome_conflict` — computed; {"conflicts": 0}
- `reset_cost` — not_implemented
- `contamination_probe` — not_implemented

Not implemented: reset-cost accounting and a held-out contamination probe. `attempts.csv` carries no reset timing, and the archive has no probe task of its own.
