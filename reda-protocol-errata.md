# Errata to ReDA 1.2

One correction, to section 4. It is recorded here rather than edited into the protocol,
because a certificate binds the protocol by hashing the file: `preflight.py` compares the
hash in `certificates/<release>/C7.json` against the bytes of `reda-protocol.md`. Editing
that file would detach every release that bound ReDA 1.2 from the protocol it was issued
under, silently and without a new signature. The protocol text therefore stays as signed;
this note carries the correction, and ReDA 1.3 folds it in.

## Section 4, required cells: the printed counts were rounded down

The inequality `n ≥ deff · ln δ / (J · ln(1 − λ))` is unchanged and remains correct. What was
wrong is the arithmetic printed beside it: the counts were rounded to four significant digits,
and a quota of cells rounds up, never down. For ρ = 0.491, J = 20, δ = 0.05:

| Target | Requirement | Printed in 1.2 | Correct quota |
|---|---|---|---|
| λ = 1e-2 | 153.9 | 154 | **154** |
| λ = 1e-3 | 1,546.4 | 1,546 | **1,547** |
| λ = 1e-6 | 1,547,145 | 1,546,000 | **1,547,146** |

At ρ = 0.01, J = 20 the same target needs 179 cells, where 1.2 printed 178.

The shortfall is 1,146 cells at λ = 1e-6, 0.07%: small enough that no published conclusion
changes, large enough that a budget sheet built on the printed figure would be under quota.
That is the reason this is an erratum and not a footnote.

## How to get the quota

```
python3 tools/sample_budget.py --check        # reproduces the table above, exits 2 if any figure moves
python3 tools/sample_budget.py --rho <measured> --attempts <J> --bound <lambda> --delta <delta>
```

A budget sheet quotes the integer the tool returns. Prose may quote the approximation and
must say that it is one.

## What this does not touch

Sections 3 and 5, the design effect identity, the independent baseline (2,995 attempts, or
150 cells at J = 20), and every estimate in `public/` are unaffected. Only the printed cell
quotas move, and only upward.
