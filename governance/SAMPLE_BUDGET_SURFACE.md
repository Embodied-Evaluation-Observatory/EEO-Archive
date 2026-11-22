# Sample-budget surface: what to plan on before a fleet's own rho exists

A cell count is a function of correlation, and correlation is a property of the thing being
measured. Nobody knows a fleet's rho before measuring it. The question this page answers is
what a budget may say in that gap, without importing a number from somewhere else.

Short answer: a surface over a fixed ladder, with a decision rule attached. Not an interval,
and not a recommended value.

## Why not an interval

The archive's own strata span 0.4838 to 0.8167. That is a measurement of the desktop
manipulation layer in one release, not a prior for robotics in general. Reporting a budget
for a fleet as "0.48 to 0.82" contradicts `governance/DOMAIN_TRANSFER.md` in the same
repository: rho is not borrowed across strata. The measured public-data site-level value
(0.0827, interval 0.056 to 0.112) sits roughly sixfold below that span, and moving from one
desktop stratum to another within a single snapshot moves rho from 0.4841 to 0.8167. The
instability that forbids borrowing is within a layer, not between layers.

So 0.48 to 0.82 may appear in this repository as a counterexample — measured on the
2026-11-19 release, model–task cells, 274 cells across 8 strata, not applicable to another
unit — and must never appear as a budget range.

## The ladder

The ladder is a fixed ruler: seven rungs, chosen because the numbers are round, not because
any of them was measured anywhere. A rung carries no provenance, so nothing can be lifted
from it without saying so.

Fixed parameters for the table below: zero-failure bound lambda = 1e-3 at delta = 0.05,
J = 20 attempts per cell. `cells = ceil(deff * ln(delta) / (J * ln(1 - lambda))`,
`deff = 1 + (J - 1) * rho`.

| rho | deff | cells | attempts (cells * J) | ceiling 1/rho |
|---|---|---|---|---|
| 0 | 1.00 | 150 | 3,000 | — |
| 0.1 | 2.90 | 435 | 8,700 | 10.0 |
| 0.2 | 4.80 | 719 | 14,380 | 5.0 |
| 0.3 | 6.70 | 1,004 | 20,080 | 3.3 |
| 0.5 | 10.50 | 1,572 | 31,440 | 2.0 |
| 0.7 | 14.30 | 2,141 | 42,820 | 1.4 |
| 0.9 | 18.10 | 2,710 | 54,200 | 1.1 |

The last column is the part readers skip. `1/rho` is the most independent observations a
single cell can ever supply. At rho = 0.82, twenty attempts in a cell buy 1.2 of them: past
that point attempts are not information, and the correct response is fewer attempts per cell
and more cells, not a longer run per cell. The table below shows the same bound at J = 10:

| rho | cells at J = 20 | cells at J = 10 | attempts at J = 20 | attempts at J = 10 |
|---|---|---|---|---|
| 0.3 | 1,004 | 1,108 | 20,080 | 11,080 |
| 0.5 | 1,572 | 1,647 | 31,440 | 16,470 |
| 0.82 | 2,483 | 2,510 | 49,660 | 25,100 |

Where rho is large, halving J nearly halves the total work for about the same cell count.

## Annotations, not rungs

Two measured values are printed beside the ladder, because a reader will want to place
themselves somewhere. Neither is a candidate for the operating point.

| Measurement | Value | What it would imply at J = 20 | Status for another unit |
|---|---|---|---|
| Public company data, site level | 0.0827 [0.056, 0.112] | 385 cells | measured on 74 sites, desktop manipulation; a scenario, not a prior |
| Archive desktop strata, 2026-11-19 | 0.4838 – 0.8167 | 1,572 – 2,473 cells | measured on 274 model–task cells, 8 strata; not applicable outside that layer |

The first row reads "if this fleet behaved like those sites, 385 cells". It does not read
"385 cells is enough". The second row exists to show what a large rho costs, not to set the
price.

## Decision rule

The surface is inert without a rule for choosing a rung, and the cheap rungs are the
attractive ones. Both of the following are permitted; nothing else is.

1. **Conservative end.** With no local measurement and no appetite for a staged plan, plan
   at the top rung of the relevant range and state the assumption in the plan itself. Cost
   is paid once; undersizing is paid twice, because a run that cannot carry the claim has
   produced no evidence.
2. **Measure, then return.** Start at the independent baseline — 150 cells at J = 20, 2,995
   attempts at lambda = 1e-3, delta = 0.05 — record rho from those cells, then read this
   table again and decide whether to extend. This is the path `governance/pilots/AMR_RHO_PILOT.md`
   takes. The baseline is a floor and a measuring instrument. It is not a stopping point: naming
   150 as the budget would be the same borrowing error in a cheaper disguise, because 150
   assumes rho = 0 and no fleet has been shown to have rho = 0.

Choosing an interior rung because it is affordable is not on the list.

## One number in the protocol is an illustration

`reda-protocol.md` section 4 shows 1,547 cells for lambda = 1e-3. That figure is computed at
rho = 0.491 — the archive's own desktop-layer measurement. It is an example of the formula
with real inputs, not a recommended budget for anything. Readers who take it as a budget
would be borrowing the layer this page forbids, through the protocol rather than through a
plan. `reda-protocol-errata.md` carries the corrected counts.

## What this page does not say

- Nothing about task mix. A rho measured on three task types is a property of those three.
- Nothing about a fleet whose correlation changes over time, for example after a controller
  release. Re-measure, do not re-read.
- Nothing about ranking. A cell count buys a decision about one quantity; it does not
  compare two fleets.
- Nothing about which rung a reader should pick. That is a decision to be written down
  and defended in the plan.

## Reproduce

```
python3 tools/sample_budget.py --rho 0.5 --attempts 20 --bound 1e-3 --delta 0.05
python3 tools/sample_budget.py --rho 0.82 --attempts 10 --bound 1e-3 --delta 0.05
python3 tools/sample_budget.py --check
```

Every cell count on this page comes from that command; none was computed by hand.
