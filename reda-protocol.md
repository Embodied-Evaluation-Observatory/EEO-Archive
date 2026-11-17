# ReDA Protocol — Repetition and Discernibility Audit

**Version** ReDA-1.2 · **Institution** Embodied Evaluation Observatory · **Status** public draft

## 1. What this protocol does

The Audit takes an existing public record of robot evaluations and reports what that
record can and cannot support: how much correlation sits between attempts in the same
cell, how many attempts the counts actually buy, which model pairs are separable, and
whether the record's provenance shows signs of selective submission. It produces no
robot performance data. Every number it reports is a statement about an existing
measurement, not a new measurement.

The Audit is a reading aid, not an authority. It offers a second view of a record that
someone else collected, in the form of intervals, tiers and bounds, so that a reader can
judge a claim for themselves. It does not adjudicate whether a paper is correct, does not
certify a system as capable or safe, and does not rank in place of the benchmark that ran
the evaluation. A number here is usable when it changes what a reader would otherwise have
assumed; it is not usable as a verdict, and no reader is obliged to accept it.

## 2. Scope and non-goals

In scope: per-attempt records with a model identity, a task identity, and an outcome;
attempt counts per cell; submission provenance where available.

Out of scope, permanently: executing evaluations on physical robots; issuing an official
first place; re-training or redistributing third-party records; ranking cells that the
record does not cover.

## 3. Units and estimators

A **cell** is a model–task pair. Attempts within a cell are **repetitions**. A cell's
attempts are not independent, so a cell is treated as a cluster.

Correlation is estimated per cell and pooled by Fisher-z with DerSimonian–Laird weights;
I² and τ² are reported so that heterogeneity is visible rather than averaged away.
Cells with zero within-cell variance (constant outcome across all attempts) carry no
information about correlation and are reported separately, never silently included.

Consequence for counts: `deff = 1 + (J − 1) ρ` and `n_eff = J / deff`. With ρ = 0.491
and J = 20, deff = 10.3 and n_eff = 1.94 — twenty attempts buy about two.

Zero-failure reporting uses the effective count: with zero failures the upper bound at
level δ is `1 − δ^(1/n_eff)`. At J = 20, δ = 0.05 the independent reading gives 0.139;
the correlation-adjusted reading gives 0.787 at these settings (the figure 0.770 is
its J→\infty limit and differs because the two are not the same quantity). Both are shown,
because the gap
between them is the point.

Substituting `n_eff` into the Clopper–Pearson bound is a first-order move, since that
bound assumes independent draws. A simulation over 36 combinations of ρ, J and cell
count, with cluster-level rates drawn from a Beta distribution and conditioned on zero
failures, gave coverage 1.000 at every point, with bounds well above the true rate. The
reading is therefore conservative in the region where zero-failure reporting is
possible.

## 4. Discernibility

For a pair of models, separability is decided on the interval of the difference, not on
the gap in points. Two models are **discernible** at level α when their difference
intervals do not overlap after the design effect is applied; a group of models whose
intervals mutually overlap is reported as one **tier** with no internal ordering.
Tiers are cut by a step-down max-T procedure that controls the probability of any
false split: pair differences are converted to normal-approximation p-values, passed
through Holm's step-down correction across every pair in a board, and only pairs that
survive are allowed to separate a tier (`tools/discriminate.py --adjust holm`, default).
The unadjusted mode remains available (`--adjust none`) for comparison with earlier
releases, and any release computed that way says so in its output.

Required cells: to certify a bound λ with zero failures at level δ under correlation ρ,
with J attempts per cell, `n ≥ deff · ln δ / (J · ln(1 − λ))`, where
`deff = 1 + (J − 1) ρ`. For ρ = 0.491, J = 20, δ = 0.05: λ = 1e-2 needs 154 cells,
λ = 1e-3 needs 1,546, λ = 1e-6 needs 1,546,000.

The independent baseline is about 3,000 attempts for λ = 1e-3, or 150 cells at J = 20;
the correlated requirement exceeds it by the design effect, 10.3, and that factor holds
at every target. Comparisons with a much smaller figure rest on the limit J → ∞, which
no benchmark reaches: at ρ = 0.01 and J = 20 the same target needs 178 cells. The
protocol always publishes both the number and the ρ it assumed.

## 5. Provenance audit

Five checks run on every release, each reported as a number rather than a verdict:

1. **Share concentration** — what fraction of scored records comes from the top k
   submitters, against the distribution expected from the stated submission process.
2. **Temporal clustering** — batch submission within a window short enough that
   independent execution is implausible.
3. **Pairwise consistency** — whether one source's win/loss pattern is too consistent
   with its own reported results across opponents.
4. **Selective submission** — repeat submissions by one organisation where only the
   best is surfaced; detected as an unexplained gap between submitted and retained
   evaluations.
5. **Contamination probe** — a perturbed variant of the task text or scene, with a
   positive control proving the probe can detect memorisation at all.

### 5.1 What is implemented, and what is not

| Check | Status | Where |
|---|---|---|
| 1. Share concentration | partial: model-level share of cells and trials, no submitter field | `tools/provenance_check.py` |
| 2. Temporal clustering | not implemented: boards publish no submission timestamps | — |
| 3. Pairwise consistency | implemented on per-task cells: a source winning every shared task is flagged | `tools/provenance_check.py` |
| 4. Selective submission | partial: submitted episodes against retained cells, where the board states both | `tools/provenance_check.py` |
| 5. Contamination probe | not implemented: no perturbed variant has been run | — |

The archive reports the checks it can compute and names the ones it cannot. A
provenance card with three of five rows filled is more useful than a card that implies
five checks were run.

A failed check produces a flag and a number, never a deletion. Deletions, if any, are
made by the record's owner, and the Audit reports the before/after counts.

## 6. Outputs

Every release publishes: a rank-interval panel, a discernibility matrix, a
correlation-and-effective-sample panel, and a provenance card. Each output carries the
protocol version, the release id, and the hash of the frozen input.

## 7. Commitments

1. The Audit does not produce robot performance data.
2. No evaluated party may specify content, review, or timing of a release.
3. No rank position is sold, sponsored, or withheld.
4. No unfavourable result is removed; corrections are published as new releases.
5. Every number is reproducible from the frozen input by a reader with the published
   scripts.

## 8. Versioning

Protocol changes are announced before the release that adopts them, and the previous
version stays citable. ReDA-1.0 is the first public version; it is the version under
which the initial archive release was frozen.
ReDA-1.1 restates the cell requirement of §4 in its finite-J form and adds a
coverage note to §3; see §9. The release frozen under ReDA-1.0 stays citable and is
not withdrawn.

## 9. Revision notes

ReDA-1.1 (2026-11-17) fixes two errors of the public draft and adds one limitation
statement. No definition, threshold or certificate output changes.

1. §4 cell requirement. ReDA-1.0 gave `n ≥ ρ ln δ / ln(1 − λ)`, which is the J → ∞
   limit. The finite-J form differs by the factor deff/J, so the published counts were
   low: 146 becomes 154 for λ = 1e-2, 1,470 becomes 1,546 for 1e-3, and 1,470,904
   becomes 1,546,000 for 1e-6. The version also quoted 30 cells for ρ = 0.01, a figure
   that is only valid in the same limit; at J = 20 the correct count is 178.
2. §4 comparison baseline. The draft compared the correlated requirement with 30 cells
   rather than with the independent requirement at the same J, 150 cells. The honest
   statement is that correlation multiplies the requirement by the design effect,
   10.3 at the pooled estimate, not that it changes the requirement by orders of
   magnitude.
3. §3 zero-failure bound. The substitution of n_eff into the Clopper–Pearson bound is
   first-order. The version now states this and reports a simulation of coverage, which
   came out conservative at all 36 grid points.

The corrected counts are larger than the draft's, so any figure computed from §4 under
ReDA-1.0 should be recomputed; figures produced by §3 are unaffected in direction and
remain quotable as upper bounds.

ReDA-1.2 (2026-11-18) is a documentation revision. It corrects the zero-failure figure in
§3 (0.787 finite-J, against 0.770 as its limit), states that §4's max-T step is now
implemented with Holm correction, and adds §5.1 recording which provenance checks exist
and which do not. No estimator, threshold or certificate output changes; releases frozen
under 1.1 remain citable and are not recomputed.
