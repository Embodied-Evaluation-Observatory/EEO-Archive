# ReDA Protocol — Repetition and Discernibility Audit

**Version** ReDA-1.0 · **Institution** Embodied Evaluation Observatory · **Status** public draft

## 1. What this protocol does

The Audit takes an existing public record of robot evaluations and reports what that
record can and cannot support: how much correlation sits between attempts in the same
cell, how many attempts the counts actually buy, which model pairs are separable, and
whether the record's provenance shows signs of selective submission. It produces no
robot performance data. Every number it reports is a statement about an existing
measurement, not a new measurement.

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
the correlation-adjusted reading gives about 0.77. Both are shown, because the gap
between them is the point.

## 4. Discernibility

For a pair of models, separability is decided on the interval of the difference, not on
the gap in points. Two models are **discernible** at level α when their difference
intervals do not overlap after the design effect is applied; a group of models whose
intervals mutually overlap is reported as one **tier** with no internal ordering.
Tiers are cut by a step-down max-T procedure that controls the probability of any
false split.

Required cells: to certify a bound λ with zero failures at level δ under correlation ρ,
`n ≥ ρ ln δ / ln(1 − λ)`. For ρ = 0.491, δ = 0.05: λ = 1e-2 needs 146 cells, λ = 1e-3
needs 1,470, λ = 1e-6 needs 1,470,904. Under ρ = 0.01 the same λ = 1e-3 needs 30. The
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
