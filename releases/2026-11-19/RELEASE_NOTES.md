# EEO Archive, release 2026-11-19 — comparability key, frontier, probe

This release changes the cell key and adds three tables. It re-issues the 2026-11-17
snapshot; no new measurements were collected.

## The key now includes scene

Cells were previously keyed on model + task. RoboHarm contributes records with a blank,
`wrapped` and `unwrapped` condition, so keying without scene pooled three prompt conditions
into one cell. The key is now model + task + scene (`cells.csv::key_fields` records this).

Consequence: the RoboHarm strata and therefore the safety and attempt families move.
Task-success strata are unchanged.

| Estimate | 2026-11-17 | 2026-11-19 |
|---|---|---|
| RoboHarm unsafe execution | 0.4475 | 0.4841 |
| RoboHarm safe refusal | 0.7521 | 0.8167 |
| safety family | 0.6229 | 0.6845 |
| attempt family | 0.6707 | 0.6949 |
| completion family | 0.5025 | 0.5025 |

The 2026-11-17 release stays as published and stays citable; this is a new release, not a
correction of that one.

## Comparability

`by_key.csv` adds `grading_method`, `source_tag`, `effort` and `mode` to the key: 308 keys
across 274 cells, with 32 cells (11.7%) splitting into more than one key. The headline
estimates stay pooled on purpose — most split keys hold one or two attempts, and an ICC
over them is unstable — but a reader can now restrict to a clean subset.

Composition: 8 grading regimes, 19 source tags, 8 effort levels, 7 modes.

## Zero-variance sensitivity and per-stratum intervals

`release_summary.csv::rho_excl_constant` repeats every estimate with constant-outcome cells
dropped. The drop is large and is reported, not hidden: completion 0.5025 → 0.3452,
attempt 0.6949 → 0.3337, safety 0.6845 → 0.3920. Zero-variance cells are still counted in
the headline estimate, because dropping them would describe a different benchmark.

`ci_lo`/`ci_hi` are percentile intervals from resampling cells within each stratum (500
reps, deterministic seed). The design-effect columns use the same rho; a naive interval
that ignores clustering would be narrower by sqrt(1 + 18*rho) — about 3.2× at rho 0.5.

## Capability frontier

`frontier.csv` lists cells with zero successes and at least 30 attempts: 9 cells (7
RoboDojo, 2 RoboHarm), each with a finite-J upper bound. 106 cells sit at 0% overall,
100 between, 68 at 100%.

A correction to earlier text: an earlier draft said 44 zero cells had 30+ attempts. That
was wrong — no cell in this release exceeds 40 attempts. The measured count is 9, and
`ATTRIBUTION.md` and `findings/sensitivity_2026-11-17.md` are corrected here.

## Provenance probe

`probe.json` reports five checks with explicit status:

| Check | Status | Reading |
|---|---|---|
| duplicate records | computed | 0 duplicates |
| identical outcome vectors across models | partial | 627 pairs; deterministic sandboxes produce these naturally, so it is a flag, not a verdict |
| temporal clustering | partial | 9 attempts in the busiest minute; no submission schedule to test against |
| share concentration | computed | top-model share per benchmark |
| score/outcome conflict | computed | 0 conflicts |
| reset cost | not implemented | attempts.csv has no reset timing |
| contamination probe | not implemented | the archive has no held-out probe task |

## Correction after publication

The data card in this release says "ReDA, version 1.0". That was a literal in the export
template that survived the protocol revision; the certificate binds ReDA-1.2 at sha256
844040b0. `public/2026-11-19/CORRECTION.md` records it. The card is not rewritten, because
the release is tagged and the published bytes should keep matching it; `tools/export_public.py`
now reads the version and hash from `reda-protocol.md`, so later cards cannot drift.

## Verification

```
python3 tools/verify_public.py --release 2026-11-19 --input releases/2026-11-17/robocurve_allruns.json
bash tests/run_fixture.sh
```

Both pass: the summary, the comparability columns, `by_key.csv`, `frontier.csv` and
`probe.json` all recompute from `attempts.csv`.

The snapshot is referenced, not re-copied: `manifest.json` records
`kind: reused_from_release` and `reused_from: releases/2026-11-17/robocurve_allruns.json`,
and every tool that reads the snapshot resolves that path (`freeze_release.py --reuse`,
`export_public.py`, `certify.py`, `preflight.py`). The bytes are the ones already frozen
on 2026-11-17, verified against that release's own manifest before this one was written. The fixture golden files are updated for
the new key column and still reproduce byte-for-byte.

`certificates/2026-11-19/` holds the layers record (L1, L2, L3 reached) and the C7
conformance card (`tools/conformance_card.py`), which states the three family estimates,
the level reached, 251 of 274 cells under 30 attempts, and which provenance checks are
computed, partial or not implemented. `tools/preflight.py` passes five of six gate items;
the sixth (deposit-file comparison) blocks until the Zenodo upload is downloaded back and
compared, which is the intended order.

2026-11-19 版把 scene 纳入格键、新增按可比字段拆分的表、能力前沿表与溯源探针，并给出
零方差格与分层区间的敏感性；task-success 数字不变，RoboHarm 与两个族因格键修正而变动。
