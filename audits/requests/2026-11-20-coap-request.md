# Request to the authors — arXiv:2610.12369

To: the authors of *Embodied Turing Machines: Stateful Code for Robot Recursive
Self-Improvement* (arXiv:2610.12369v1)
From: Embodied Evaluation Observatory
Date: 2026-11-20

## What we did

We read Table 2 and recomputed the Overall column of all 24 methods from the five domain
success rates. Every row reproduces to within 0.03 pp, so the table is arithmetically
consistent. Two observations came out of the recomputation, and one request follows from them.

## Two observations

1. The Overall column is the unweighted mean of the five domains. The domains hold unequal
   task counts (6, 8, 8, 12, 8), so a task-weighted mean differs: COAP 68.87 against 70.24,
   PhysicalRSI 29.15 against 31.38, DM0.5 17.20 against 19.34. Whether the macro or the
   weighted mean is the intended headline is a choice, but the choice changes the reported
   number by one to two points and is not stated in the text.
2. From the five aggregates alone, the interval around 70.24 is about ±11 pp at 95%; applying
   the archive's RoboDojo intra-cluster correlation (0.5013) to the stated design of 42 tasks,
   3 seeds and 50 layouts gives about ±10 pp. The two routes agree, which suggests the
   aggregate route is not overstating precision.

Neither observation is a criticism of the result. Both are limited by the same missing
material, which is the reason for this request.

## Request

Please release, with the paper or in a repository:

1. **Per-task success rates**: 42 rows, task name, domain, attempts, successes, and the success
   rule applied. This alone would let any reader reproduce the five domain values and the
   Overall column, and would settle observation 1.
2. **Run manifest**: one row per evaluated run — task id, seed, layout id, library or code
   version used, date, and outcome (success, failure stage or reason, or abstention). The
   manifest does not need the video or the trajectories; identifiers and outcomes are enough
   to check aggregation and to measure between-task variance.
3. **The success rule**: how a partially completed task is scored (all-or-nothing, or the
   benchmark's progress score), and how the reattempt policy in Table 3 interacts with it.
4. **Which library version produced Table 2**, so the reported numbers can be attached to a
   commit rather than to a development process.

## How we would use it

We would recompute the headline from your record, report whether it matches, and cite the
paper and the release. We would not redistribute your logs; the archive publishes derived
tables and hashes, not source records, and the same policy would apply here. If a discrepancy
appeared, we would send it to you before publishing anything.

If releasing logs is not possible, per-task success rates alone would still raise this paper
from L1 to L2, and we would record that level with the constraint stated.
