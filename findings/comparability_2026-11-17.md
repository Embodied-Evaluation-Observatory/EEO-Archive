# Comparability audit, 2026-11-17

Cells hold attempts that can differ in how they were graded and under what inference conditions. ReDA pools them; this records how often.

| Field | Distinct values | Mixed cells | Share of cells |
|---|---|---|---|
| `grading_method` | 8 | 18 | 9% |
| `source_tag` | 19 | 15 | 7% |
| `effort` | 8 | 14 | 7% |
| `mode` | 7 | 12 | 6% |

Cells mixed on at least one field: **23 of 208** (11%); attempts inside them: **830 of 4239** (20%).

## Comparability key

`benchmark + grading_method + mode + effort + source_tag`

Benchmarks whose cells span more than one key:

- datacenterbench: 8 distinct keys
- robodojo-rc-tier-1: 17 distinct keys
- roboharm-v1: 3 distinct keys
- robospoof: 4 distinct keys
- simple-tasks: 6 distinct keys

## Limit

A mixed cell is not wrong; it is unlabelled. The rate it publishes is a weighted average over procedures, and the audit cannot say which procedure produced the variance. Splitting these cells would shrink the cell count further, which is why they are flagged rather than removed.
