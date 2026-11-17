# Discernibility under Holm correction

This directory re-runs the archive's own pair tests on the 2026-11-17 snapshot with
multiplicity control, which the protocol section 4 has always specified and the
published 2026-11-17 tables did not apply.

- `--adjust none` reproduces the 2026-11-17 figures (143 pairs, 57 separated, 60.1% undiscernible).
- `--adjust holm` (new default) controls the family-wise error rate across all pairs in a board.

The difference is large and is the point: without a multiplicity correction, dozens of
pairs clear a 95% interval by chance alone. The published 2026-11-17 release is not
rewritten; it stays citable with its own method stated, and this directory records what
the corrected method yields on the same bytes.
