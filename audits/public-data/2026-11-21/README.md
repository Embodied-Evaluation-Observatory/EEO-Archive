# Public company data, checked for what it can actually support

Date 2026-11-21. Question: which robot-company public releases carry a per-attempt outcome
label, and what can be estimated from them without borrowing anything.

## What was collected

Twelve candidate sources, listed in `sources.csv` with declared licence, access route, label
field and size. Two findings from the inventory alone:

- Only one source exposes a per-episode binary outcome through a small, label-only read:
  DROID 1.0.1, co-produced by Physical Intelligence and thirteen institutions. Everything
  else either puts labels inside 30 GB-to-terabyte archives (AgiBot World 2026), withholds
  terms until an access request is granted (AgiBot World Beta, RoboMIND original, one humanoid vendor's sample
  repository), or is simulation rather than deployment (RoboCasa, GenieSim).
- Two classes of party have nothing public at all: the large humanoid vendors and the
  industrial AMR vendors, including the fleet that asked for a correlation estimate. For
  them no amount of collection produces a number; only their own records do.

## The test that was run

DROID 1.0.1, all 95,658 episodes, label `is_episode_successful`, read from the frame tables
with column projection so no video or image data was transferred. Table deduplicated on
`episode_index`.

Mean success over the whole set: 0.8244. Sites: 74.

Two cell definitions were estimated, because they answer different questions:

| Cell | Cells | rho (one-way ICC) | 95% interval (cluster bootstrap) |
|---|---|---|---|
| site (74 operators' locations) | 74 | 0.0827 | 0.056 - 0.112 |
| site x task instruction | 54,453 | 0.6356 | 0.466 - 0.777 |
| site x task instruction, attempts >= 5 | 1,336 | 0.7446 | not reported (subset of the row above) |

## How to read the second and third rows

They should not be read as correlation. Among the 6,815 cells with at least two attempts,
**98.6% are zero-variance** — every attempt succeeded, or every attempt failed. A cell with
no internal variance contributes nothing to a within-cell estimate except an infinite
contrast against other cells, so the 0.64 and 0.74 figures are artefacts of the ceiling, not
measurements of clustering.

That is the finding, and it is the one worth publishing: public robot-company data is
overwhelmingly success-only demonstration. On such data a correlation cannot be estimated,
and the right instrument is the zero-failure bound this archive already uses, not rho.

## What the site-level number does say

0.0827 is a real estimate, on 95,658 attempts across 74 sites, with an interval narrow
enough to be useful. It says: on this dataset, being at the same site explains about eight
percent of the variance in outcome. Attempts from one site are close to independent, in
sharp contrast with the desktop-manipulation strata in this archive, which sit between 0.48
and 0.82.

Two consequences, both already written into `governance/DOMAIN_TRANSFER.md` and now
supported by a measurement rather than an argument:

- the ~0.5 prior is not a general property of embodied evaluation; a published company
  dataset yields a number six times smaller;
- a design effect computed from a borrowed 0.5 would have inflated the required sample size
  by roughly 5.5x for ten attempts per cell, when the measured value here implies about
  1.7x.

Caveat, stated because it matters: the low value is partly an artefact of heterogeneity
inside sites. Each site runs many different tasks, so "same site" is a weak cell. A
task-level cell would be stronger, and it is exactly the one that the label distribution
makes unusable. The two limitations trade against each other, and neither number should be
quoted without the other.

## What is published here, and what is not

Published: `sources.csv`, `cells_derived.csv` (6,815 cell aggregates: site, instruction,
attempts, successes, zero-variance flag), `summary.json`, this note.

Not published: any frame data, video, image, or per-episode row from DROID. The derived
aggregate is published under the source's Apache-2.0 terms with attribution; raw bytes were
read remotely and never stored in this repository.

## Reproducing

The label column and the site column are sufficient. Read the 156 data shards of
`lerobot/droid_1.0.1` with column projection (`episode_index`, `is_last`,
`is_episode_successful`, `building`, `language_instruction`), keep rows where `is_last` is
true, deduplicate on `episode_index`, then estimate a one-way intraclass correlation from
between-cell and within-cell mean squares and bootstrap over cells. Reading all shards takes
about thirteen minutes; no image or video byte is transferred.

## Limits

The label is an operator annotation with no per-episode judging rule recorded, so part of
what looks like clustering may be annotator behaviour. That cannot be separated from the
public release, and it is the reason the estimate is reported as a site-level quantity with
a stated caveat rather than as a claim about the dataset's difficulty structure.
