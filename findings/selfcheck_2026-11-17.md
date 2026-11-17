# Self-check, release 2026-11-17

Every figure below is recomputed from the files named in `inputs`; nothing is estimated.

## Repeatability

| family | rho | 95% CI | cells | trials |
|---|---|---|---|---|
| perf | 0.5025 | [0.3396, 0.6362] | 103 | 2371 |
| att | 0.6707 | [0.5433, 0.7679] | 105 | 1598 |
| safety | 0.6229 | [0.2388, 0.8384] | 60 | 1396 |

## Discernibility of published boards

| board | pairs | separated | undiscernible % | cells with n stated |
|---|---|---|---|---|
| robochallenge | 681 | 172 | 74.7 | 0 of 769 |
| roboarena | 276 | 53 | 80.8 | not stated |
| robotwin | 630 | 601 | 4.6 | 3600 of 3600 |

## Sample sufficiency

Cells: 268. Median attempts per cell: 20. Cells under 30 attempts: 245 (91.4%).

A thin cell is usable as a single-model report, not as one observation in a correlation across the board. See `QUALITY_GATE.md`.

## Certificate layers reachable for this release

| layer | reachable | meaning |
|---|---|---|
| L1 tables self-consistent | True | published summary reproduces from published tables |
| L2 source bytes match declared hash | True | the snapshot present locally hashes to the manifest |
| L3 source open to any reader | True | the snapshot itself is redistributed, so an outsider can redo the export |
