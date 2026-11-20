# Comparability, release 2026-11-17

The audit reports one rho per family and one per stratum. That number assumes each cell
measures one thing. This document records what the cells actually mix, and defines the key
under which they would be comparable.

Computed by `tools/comparability.py`; output `findings/comparability_2026-11-17.json`.

## What a cell contains

`attempts.csv` carries four fields that vary inside a cell:

| Field | Distinct values | Cells mixed | Share |
|---|---|---|---|
| `grading_method` | 8 | 18 | 9% |
| `source_tag` | 19 | 15 | 7% |
| `effort` | 8 | 14 | 7% |
| `mode` | 7 | 12 | 6% |

23 of 208 distinct cells (11%) mix on at least one field, and those cells hold 830 of
4,239 attempts (20%). The published table has 268 rows for those 208 cells because
RoboHarm appearances are counted three times (unsafe, refusal, attempt); row-level,
32 rows carry a mixed label. The values are not cosmetic: `grading_method` runs from `Autograded` to
`Claude Fable 5.1 refusal judge` to `Report score`; `mode` runs from `standard` to
`not-recorded`; `effort` from `high` to `budget-8k`.

Every benchmark spans more than one key: robodojo-rc-tier-1 17 keys, datacenterbench 8,
simple-tasks 6, robospoof 4, roboharm-v1 3.

## The key

```
benchmark + grading_method + mode + effort + source_tag
```

A rate is comparable across cells only within one tuple. Cells outside it are flagged,
not deleted — deleting them would leave too few cells to estimate anything, and the rate
itself is not wrong, only unlabelled.

## Why this is the sharpest gap

The audit's core claim is that a reported difference may not be distinguishable from
repeat noise. If part of the repeat noise is procedural — a re-graded rubric, a fast
inference mode, a different source batch — then the audit currently attributes to
capability what belongs to procedure. Nothing in the published tables separates the two.

Two honest consequences, neither of which is a fix:

- the tables as published cannot be re-cut by key without shrinking the cell count
  below what the estimator needs (248 scored cells already; splitting by key leaves
  single-digit cells in several strata);
- the missing fact is not statistical but documentary. A benchmark that recorded which
  rubric graded an attempt, and published it, could be audited per key tomorrow.

## What a next release would carry

A `key` column on `cells.csv`, empty where the cell is mixed, plus a `mixed_fields` column
listing which of the four varied. That is a schema change and a new release, not a patch
to this one. Until then this file is the record.

## Cross-board comparability

Four boards are ingested under `boards/`. Their records are not yet mapped onto one
framework: attempt definition, reset protocol and success criterion differ, and the
published separability shares differ accordingly (91.6% / 97.8% / 90.9% / 7.3% at
2026-11-18). Those percentages are not interchangeable, and the board notes already say
so. A mapping table — one row per board, one column per definition — is the next step,
and it is documentary work: it requires reading each board's protocol, not recomputing.
