# External paper audits

Notes on third-party papers whose numbers touch a board the archive also covers. These are
audit notes, not certificates: a certificate applies to the archive's own tables, signed and
frozen. A note records what could be checked on a paper's published material, and stops where
the material stops.

## Levels used for third-party papers

| Level | What it means | What it needs |
|---|---|---|
| L1 | published aggregates are internally consistent with what they summarise | the paper's own tables |
| L2 | published aggregates recompute from released per-task or per-run records | a data release with task-level rows |
| L3 | headline recomputes from per-episode logs | attempt-level records, code version, grading rule |

Only L1 can be reached without a data release. A note states the level it reached and does not
imply the others.

## Index

| # | Paper | Board | Level | Date | Note |
|---|---|---|---|---|---|
| 1 | Hu, Hu, Hong, Chen, Liu, *Embodied Turing Machines: Stateful Code for Robot Recursive Self-Improvement*, arXiv:2610.12369v1 | RoboDojo | L1 | 2026-11-20 | `2026-11-20-coap-2610.12369.md` |

Entry 1 reached L1: 24 of 24 rows reproduce, the headline is a macro mean over five domains
(70.24 against 68.87 task-weighted), and the aggregates imply roughly ±11 pp. No per-task or
per-episode records were released, so L2 and L3 are out of reach for this paper.

## Rules

- A note names the board, the level reached and the reason the next level was not reached.
- Numbers in a note are recomputed here, never copied from the paper's prose.
- A note is dated and never edited after issue; a later check is a new note with a later date.
- Requesting missing material is recorded in `audits/requests/`, so a reader can see what was
  asked for and when.
