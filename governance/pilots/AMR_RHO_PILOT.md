# Measuring rho on one AMR fleet: a one-page pilot

Purpose: replace a borrowed correlation with one measured on the fleet in question, at a
size that fits inside a week and produces a number with an interval attached.

## Design

Three task types x five configurations x ten attempts = 150 attempts.

- Task types: pick three that differ in what makes them hard (a pick-and-place, a
  transport-with-obstacle, a dock or handover). Not the three easiest.
- Configurations: five that differ in a way the operator cares about — site, payload, map
  version, fleet size — recorded as a label, not merged.
- Attempts: ten per cell, run under the same conditions, in one block per cell if possible.

## Definitions, fixed before the first attempt

Each of these is written down once and does not change mid-run. A changed definition
invalidates the run, and the honest response is to start over rather than to reconcile.

- **Unit**: one task instance from start to judged end. A takeover in the middle does not
  start a new attempt.
- **Primary outcome**: run completed without remote takeover (1/0). Secondary outcome: task
  completed (1/0). They are different variables; report both, estimate rho on the primary.
- **Remote takeover**: an operator takes control and completes any part of the remaining
  motion. The attempt is scored 0 regardless of what happened afterwards.
- **On-site reset**: robot stopped, a person restores pose and the run continues. Scored 0.
- **Retry**: the instance starts again from the beginning. A new attempt, new row, counted
  in the denominator of nothing else.
- **Judge**: state who decides (operator, supervisor, automatic check) and whether that
  person also ran the robot. If the same person does both, say so; it is a known bias, not
  a disqualification.

## What to record, one row per attempt

`attempt_id, date, site_code, task_type, config_label, attempt_index (1-10), outcome_primary,
outcome_secondary, takeover (0/1), resets, retries, duration_min, judge_role, notes (free
text, no names), video (y/n)`

Free text carries no operator names. Site names become codes at intake.

## How to compute

1. rho is a one-way intraclass correlation over the fifteen cells, estimated from a
   variance-components decomposition (between-cell and within-cell mean squares), which
   handles unequal attempt counts.
2. Interval: cluster bootstrap, resampling cells with replacement and keeping their attempts
   together, 2000 draws, 2.5 and 97.5 percentiles. Cells are the resampling unit because
   they are the independent units; resampling attempts would produce an interval that is
   too narrow.
3. Report alongside rho: number of cells, attempts per cell, the share of cells with zero
   variance (all 0 or all 1), and the design effect at J = 10, which is 1 + 9 * rho.
4. Report the mean outcome as well. A rho computed where almost everything succeeds is
   dominated by the few failures and should be read that way.

## How to read the result

From simulation of this exact design (15 cells, 10 attempts, binary outcomes), the estimate
is roughly unbiased but imprecise:

| True rho | Median estimate | 90% interval of the estimate |
|---|---|---|
| 0.3 | 0.27 | 0.12 - 0.43 |
| 0.5 | 0.45 | 0.27 - 0.62 |
| 0.7 | 0.66 | 0.47 - 0.83 |

So this pilot resolves rho to about plus or minus 0.17 and cannot separate 0.5 from 0.65.
That is the intended granularity: it establishes whether correlation is negligible, moderate
or severe, and it does not pretend to pin a decimal.

Consequences to state in the report, not to leave implied:

- at rho = 0.5, ten attempts in a cell buy about two independent observations, so a "90%
  success rate on 10 runs" carries an interval close to what two trials would give;
- the upper bound of the interval is what a sample-size plan should use, never the point
  estimate, because undersizing is the failure that matters;
- if two cells differ by less than roughly one attempt's worth of independent information,
  the comparison is not yet decidable at this sample size, whatever the point estimates say.

## Cost and schedule

150 attempts, one operator, one site, two to three days including setup and the definition
workshop. Analysis is minutes once the table exists. The deliverable is a two-page note: the
table, rho with interval, the zero-variance share, and three sentences on what the number
does not cover.

## What this does not establish

Cross-site generalisation (five configurations are labels, not a sample of sites), safety,
capability ranking against another fleet, or anything about tasks not in the three chosen
types. A rho from this pilot is a property of these three task types on this fleet at this
time, and is quoted as such.

## Publication

This design is public. The result belongs to the fleet that ran it: it is published only
with the holder's consent, in the form described in `governance/DATA_TERMS.md` — derived
table and hashes, no raw logs, no operator identities.

## Status

Not run as of 2026-11-21. No fleet has supplied records yet, so the numbers above come from
simulation of the design, not from a measurement.
