# Benchmark design anti-patterns

Each entry is a check with a threshold, a command that produces the number, and
what the number usually means. Thresholds are set from what the archive has
measured, not from theory; they are starting points for a conversation, not
pass/fail rules.

## A1 — Attempts per cell are not stated

Measure: share of cells for which the number of attempts is absent.
Current evidence: RoboChallenge 0 of 769 cells state attempts; RoboArena does not
state it; RoboTwin states 100 per cell.

Why it matters: without it, a rank difference cannot be separated from sampling
noise, and no reader can tell whether a 3-point gap is a result or a coin toss.

Check: `python3 tools/board_audit.py --raw boards/<date>/raw --out boards/<date>`

## A2 — Cells below 30 attempts carry the ranking

Measure: share of cells under 30 attempts, and the median attempts per cell.
Current evidence: 2026-11-17 has 245 of 268 cells under 30, median 20.

Why it matters: a cell of 20 is a fine single-model report and a poor single
observation in a cross-model correlation. Rankings built mostly from such cells
describe the record, not the models.

Check: `python3 tools/bench_selfcheck.py --release <id>`, section "Sample sufficiency"

## A3 — Repeats and replacements are invisible

Measure: share of attempts marked as a replacement or a rerun, and whether the
policy for which attempt counts is stated.
Why it matters: choosing the better of two runs after the fact doubles the
effective success rate without any visible trace.

Check: `replacement` and `rerun` columns in `public/<date>/attempts.csv`; a release
where these are all false should say that repeats were never run, not leave it ambiguous.

## A4 — Reported gaps sit below the resolution floor

Measure: for each claimed ordering, the gap against the floor implied by the cell
count and dispersion.
Current evidence: at rho about 0.49 and n = 1,000 the floor is roughly 34
percentage points; most leaderboard gaps are single digits.

Why it matters: a "new SOTA" separated by less than the floor is indistinguishable
from the previous entry at the stated evidence level.

Check: `ReDA自查表` or `public/<date>/release_summary.csv` plus the floor formula in
`reda-protocol.md` section 5.

## A5 — Autonomy is not stated

Measure: share of attempts with `operator_mode` recorded, and whether teleoperation
appears in the protocol at all.
Why it matters: a demonstration labelled autonomous that involved a human
correction is a different claim from one that did not.

Check: `operator_mode` in EvalLog ingest (`schema/eval_log_min.schema.json`); in
existing boards, the absence of the field itself is the finding.

## A6 — Demonstrations cannot be tied to logs

Measure: share of attempts with a log reference, and whether video count and log
exist for the same attempt.
Current evidence: `has_log` and `video_count` exist as flags; no attempt-level
video verification has been performed.

Why it matters: a clipped video is not evidence of a complete run; a log without
a video cannot show what the log omits.

Check: `has_log`, `video_count` in `attempts.csv`; cross-tabulate against outcome.

## Using this list

A benchmark maintainer can run A1, A2 and A4 before publishing and fix the
statement rather than the numbers. A reviewer can cite one entry instead of
arguing about the whole framework. A course can use the entries as design rules.
