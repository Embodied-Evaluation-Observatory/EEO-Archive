# Accumulation before publication

Four things are deliberately off the public surface for now: source attribution, cross-board
mapping, scenario thresholds, cross-layer comparability tags. They are recorded here so that
data collection can start before any claim is made.

## What to keep per attempt, from the next release on

| Field | Why it is needed |
|---|---|
| engine / simulator version, if published | attribution cannot separate engine artifacts from policy without it |
| log path or checksum, not just `has_log` | a boolean cannot be re-inspected |
| video path or checksum, not just `video_count` | same |
| reset protocol: fixed pose, randomized, human | reset cost is a first-order noise source on real hardware |
| operator intervention count | separates autonomy from teleoperation |
| episode termination reason | distinguishes failure from timeout from safety stop |
| attempt ordinal within the cell | needed to see learning or drift inside a cell |

All of these are optional and empty is allowed. An empty field is a recorded absence, not a
zero. The archive does not gate a release on them; it records whether a source supplied them.

## Cross-board mapping

One row per board: attempt definition, reset protocol, success criterion, aggregation,
whether per-attempt records exist. No numbers are to be published from this table until at
least three boards are mapped, because a two-board table invites exactly the comparison
the mapping is meant to prevent.

## Thresholds

The formula exists; the calibration does not. Publishing a threshold table before the
resolution arithmetic is consistent across documents would repeat a known defect. No such
table is published until the formula in the protocol and the one in the self-check tool
agree to the digit.

## Cross-layer tags

An industrial force-control spec and an embodied success rate sit on different causal
layers. The tag exists in prose (`ATTRIBUTION.md`); it is not applied to any published
number, because no record in the archive carries both layers.

## Where this goes

Nothing here is public. When a release carries the fields above for enough records, the
first public step is a coverage table — how many attempts have a log, a video, a reset
protocol — and not an attribution claim.
