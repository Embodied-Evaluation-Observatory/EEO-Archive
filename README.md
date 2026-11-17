# EEO Archive

Embodied Evaluation Observatory — public tables for the Repetition and Discernibility
Audit (ReDA).

**We do not evaluate robots. We audit the evaluations.**

This repository publishes the derived tables for each archive release: per-attempt
records re-published in flat form, cell-level summaries, and the correlation estimates
with their design consequences. It also publishes the tooling that produces them, so a
reader can recompute every number we quote.

## What is here

| Path | Contents |
|---|---|
| `public/<release>/attempts.csv` | one row per attempt, de-identified and truncated |
| `public/<release>/cells.csv` | one row per model-task cell, with its stratum |
| `public/<release>/release_summary.csv` | stratum and merged estimates, design effects |
| `public/<release>/DATASET_CARD.md` | provenance, field dictionary, licence blocks |
| `public/<release>/checksums.txt` | sha256 of every published file |
| `releases/<release>/manifest.json` | sha256 and size of the sealed source bytes |
| `provenance/<release>.md` | where the bytes came from, when, and how many |
| `tools/export_public.py` | produces the public tables from sealed bytes |
| `tools/verify_public.py` | recomputes the summary from the public table alone |
| `tools/freeze_release.py` | creates an immutable release; refuses to overwrite one |
| `reda-protocol.md` | the ReDA protocol specification, version 1.2 |

## Check it

```
python3 tools/verify_public.py --release 2026-11-17 --input releases/2026-11-17/robocurve_allruns.json
```

This verifies every published file against `checksums.txt`, then recomputes the seven
strata and both family merges from `attempts.csv` alone, and compares them with
`release_summary.csv`. On release `2026-11-17` it prints:

```
completion_family   rho=0.5025 CI=[0.3396, 0.6362]
attempt_family      rho=0.6707 CI=[0.5433, 0.7679]
safety_family       rho=0.6229 CI=[0.2388, 0.8384]
PASS: published summary reproduces from attempts.csv
```

If the numbers we quote cannot be reproduced from what we publish, that is a defect and
should be filed as an issue.

## Source bytes

Access differs by release, and `ACCESS.md` states it per release.

- `2026-11-15`: hash only. The snapshot is not redistributed; a reader holding the same
  bytes can prove they match the manifest, but cannot rebuild the tables from source.
- `2026-11-17` onward: open. The snapshot is redistributed with the release, so
  `tools/export_public.py` can be run by anyone and the published tables compared against
  a fresh export. Redistribution of third-party records is stated as a cited copy rather
  than a relicensed work; see `LICENSE-DATA.md` block 4.

`tools/verify_public.py` works from the published tables alone; `--input` adds a check
of the redistributed bytes against the manifest hash.

## Licence

Three blocks, not one.

1. The compilation and everything computed from it — table structure, de-identification,
   stratum estimates, design-effect columns — is released under CC-BY-4.0. Attribute as
   `EEO Archive, release <id>`.
2. The per-attempt result fields originate in the source archive named in each
   `provenance` file. Their rights remain with the source; this repository cites them as
   facts and does not relicense them.
3. The code in `tools/` is MIT licensed.

## Citing

```
EEO Archive, release 2026-11-18. Embodied Evaluation Observatory.
DOI 10.5281/zenodo.24325457 (concept 10.5281/zenodo.24269291)
Snapshot sha256 5d960b810011077725dee438081e0978ee640f71494a84e915c69d87eebff850.
```

Version DOI 10.5281/zenodo.24325457 identifies the 2026-11-18 deposit, which carries the
corrected 2026-11-17 tables and the redistributed snapshot. The earlier deposit
(10.5281/zenodo.24269292) remains citable for the 2026-11-15 bytes and is not withdrawn.
When citing the archive as a continuing series rather than a single release, use the concept
DOI 10.5281/zenodo.24269291.

## Scope

This repository does not contain evaluation conclusions about any robot or model. It
contains records and their reliability measurements. Reports are separate documents with
their own limits.
