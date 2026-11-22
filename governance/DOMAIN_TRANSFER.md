# Whether a correlation estimate travels

Every design-effect statement in this archive rests on one number: rho, the intraclass
correlation of outcomes inside a cell. Columns of attempts from one model on one task are
not independent, and rho says how far from independent they are. This file states when a
measured rho may be used outside the stratum it came from, because that question has now
been asked twice by parties whose domains look nothing like the benchmarks here.

## rho is not a property of embodied AI

It is a property of a coupling: the task set, the policy, and the judging rule acting
together. Change any of the three and the number can move. The archive already shows this
across its own strata, on one snapshot:

| Stratum | rho |
|---|---|
| RoboDojo task success | 0.5013 |
| RoboHarm unsafe execution | 0.4841 |
| RoboHarm safe refusal | 0.8167 |
| RoboSpoof unaltered | 0.4838 |
| RoboSpoof blurred | 0.6538 |
| RoboSpoof doctored | 0.7273 |

Same records, same export, different strata, and the range is wider than any of the
differences one might want to attribute to "embodiment". A single number carried across
domains would hide exactly this variation.

## The rule

1. No measured rho is presented as an estimate for a domain it was not measured in.
   Borrowing it as a point value is not permitted, in a certificate or in a proposal.
2. A borrowed value may be used only as a sensitivity input, and must be labelled: "at
   rho = 0.5, as measured in desktop manipulation, the design effect would be X". The
   sentence names the source stratum and says the target value is unknown.
3. One measurement in the target domain replaces borrowing. Once rho is measured there,
   the borrowed range is no longer used except as history.
4. If a measurement cannot be made, the honest output is a range over plausible rho
   (for example 0.1 to 0.9) plus the statement that the value is unknown. A single
   fabricated point value is worse than a wide, labelled range.

## How to measure rho in a new domain

The estimate needs repeated outcomes inside cells, and cells that differ from each other:

- pick K tasks that are representative of the deployment, not the easiest ones;
- pick M configurations, models or sites that differ in a way you care about;
- run each (task, configuration) cell J times under the same conditions;
- record one binary outcome per attempt, with the judging rule fixed before the run;
- estimate rho as a one-way intraclass correlation over the cells, and report K, M, J,
  the interval, and the judging rule.

J matters more than people expect. With rho = 0.5, the design effect is 1 + (J - 1) * 0.5,
so J = 3 gives 2.0 and J = 10 gives 5.5: ten attempts in one cell buy about two
independent observations. A pilot with J = 3 and a handful of cells can show that rho is
non-zero, and cannot pin its value; saying so is part of the result.

## Industrial mobile robots

A fleet measures something the benchmarks here do not: uninterrupted operation under
recovery. Two definitional choices come before any estimate.

- The outcome variable. "Task completed" and "run completed without takeover" are different
  variables with different rho. Pick one, fix it, and report the other separately.
- The unit. A shift, a mission, or a task instance. The denominator must match the unit, and
  a takeover in the middle of an attempt does not start a new attempt.

A workable pilot: three task types, five configurations or sites, ten runs each, with the
takeover rule fixed in advance. That is 150 attempts and yields a rho with an interval wide
enough to be useful only as a bound. It is still better than an imported 0.5, because it is
about your fleet.

What must not happen: quoting the archive's 0.5 as if it applied to an AMR fleet, then
deriving a confidence interval from it. The arithmetic would be correct and the input
wrong, which is the failure mode this file exists to prevent.

## Contact-rich tasks and repeated human judgement

Contact-rich and human-judged settings add a second source of dependence that the benchmarks
do not have: the assessor. If the same operator scores the same episode twice and gives
different numbers, that variance sits inside the cell and inflates rho in a way that has
nothing to do with the policy.

So there are two quantities, and they must not be merged:

- inter-rater agreement, measured on a sample of episodes scored by two or more assessors;
- within-cell clustering of the final outcome, measured after the scoring rule is fixed.

Report both. A high rho caused by assessor disagreement is a measurement problem; a high
rho caused by episode-to-episode systematics is a design problem. The remedies differ, and
one number cannot tell them apart.

## What a reader should take from a borrowed number

If a document in this archive or from a partner quotes a design effect, the reader is
entitled to ask three things: which stratum produced rho, how many attempts per cell, and
whether the target domain was measured or assumed. A document that cannot answer all three
is not making a statistical claim; it is repeating a number.

## Status

No measurement exists for industrial mobile robots or for human-judged settings as of
2026-11-21. Both parties who asked have offered their own records, which is the right
starting point: a first estimate from their own runs, published with its interval and its
limits, is worth more than any transfer argument.
