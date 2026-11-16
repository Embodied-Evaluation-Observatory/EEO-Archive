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
| `reda-protocol.md` | the ReDA protocol specification, version 1.0 |

## Check it

```
python3 tools/verify_public.py --release 2026-11-15
```

This verifies every published file against `checksums.txt`, then recomputes the seven
strata and both family merges from `attempts.csv` alone, and compares them with
`release_summary.csv`. On release `2026-11-15` it prints:

```
completion_family   rho=0.4909 CI=[0.3463, 0.6127]
attempt_family      rho=0.6707 CI=[0.5433, 0.7679]
PASS: published summary reproduces from attempts.csv
```

If the numbers we quote cannot be reproduced from what we publish, that is a defect and
should be filed as an issue.

## Sealed bytes

The source bytes are held sealed rather than redistributed here. Publishing hashes and
sizes lets anyone holding the same copy prove it matches this release; redistributing
third-party records is a different act, and one this project does not do. See
`releases/2026-11-15/manifest.json` for the hashes.

`tools/export_public.py` therefore needs the sealed bytes to run. `tools/verify_public.py`
does not: it works from the published tables.

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
EEO Archive, release 2026-11-15. Embodied Evaluation Observatory.
DOI 10.5281/zenodo.24269292
Release hash c0bd689f26900f488802ed21159c55c5a40ca5cde6064cb91fbe9795ce93b7db.
```

This release is archived on Zenodo under DOI 10.5281/zenodo.24269292. When citing the archive as a
continuing series rather than this single release, use the concept DOI printed on the
Zenodo record page; the version DOI above identifies exactly these bytes.

## Scope

This repository does not contain evaluation conclusions about any robot or model. It
contains records and their reliability measurements. Reports are separate documents with
their own limits.
