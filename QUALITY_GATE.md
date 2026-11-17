# Quality gate: minimum trials per cell

A cell is one model on one task in one benchmark. Every estimate in this archive
correlates cells with each other, so a cell measured 12 times carries far less
information than one measured 200 times, and a zero-failure result at low counts
cannot bound the true success rate from below in any useful way.

## The rule

`MIN_TRIALS = 30`. A cell with fewer than 30 attempts is **flagged**, not
corrected and not deleted.

- `tools/export_public.py` prints `WARNING: x of y cells have fewer than 30
  attempts` and writes `quality_flags.json` beside the published tables.
- `tools/verify_public.py` prints the strata whose per-cell counts fall below 30.
- Flags appear in the release directory; published numbers stay as computed.

## Why flag rather than drop

Dropping thin cells would silently shrink the evidence base and change the
published estimates after the fact. Flagging keeps the numbers reproducible and
puts the burden of interpretation where it belongs: on the reader, who can see
the count next to every value.

## What the flag does not mean

A flagged cell is not wrong. It is under-sampled for the inference drawn across
cells. At 20 attempts a cell is perfectly adequate for a single-model report of
"17 of 20 trials succeeded"; it is inadequate as one observation in a
correlation across an entire benchmark.

## Reading the archive with this in mind

If a stratum has almost only thin cells, its rho should be treated as a
description of the published record rather than a property of the models
themselves. This is the same distinction made in `DATASET_CARD.md`: the archive
audits disclosure, not capability.
