#!/usr/bin/env python3
"""Sample budget: how many cells an attempt-correlated evaluation needs.

Two questions, both answered before a run, never after:

  zero-failure bound   to certify a bound at a target failure rate, at a stated confidence
  interval half-width  to reach a target width on a proportion near p

Usage:
    python3 tools/sample_budget.py --rho 0.491 --attempts 20 --bound 1e-3 --delta 0.05
    python3 tools/sample_budget.py --rho 0.502 --attempts 20 --half-width 0.10
    python3 tools/sample_budget.py --check          # reproduces the figures in protocol section 4

Formulas are the ones in `reda-protocol.md` section 4; nothing here is fitted to a release.
Section 4 printed its cell counts rounded to four significant digits, which understates a quota
of cells. The corrected counts are in `reda-protocol-errata.md`; `--check` encodes them.
Exit code 0 on a computed answer, 2 when the protocol figures do not reproduce.
"""
import argparse
import json
import math
import sys

def deff(attempts, rho):
    return 1.0 + (attempts - 1) * rho

def cells_for_bound(lam, delta, rho, attempts):
    """n >= deff * ln(delta) / (attempts * ln(1 - lam)); returns cells and the exact value."""
    d = deff(attempts, rho)
    exact = d * math.log(delta) / (attempts * math.log(1.0 - lam))
    return math.ceil(exact), exact, d

def cells_for_half_width(h, rho, p=0.5, z=1.959963985):
    """Independent observations needed for a half-width h at proportion p, times rho.

    A cell's effective count saturates at 1/rho, so cells needed is n_eff * rho.
    This is arithmetic on a measured rho, not a new estimate; the protocol states the
    bound formula above, not this one, and a record using it says which it used.
    """
    n_eff = (z * z) * p * (1.0 - p) / (h * h)
    return math.ceil(n_eff * rho), n_eff

def attempts_for_saturation(rho, share=0.9):
    """Attempts per cell that reach `share` of the 1/rho ceiling."""
    if rho <= 0:
        return 1
    return math.ceil((share / (1.0 - share)) * (1.0 - rho) / rho)

PROTOCOL_CASES = [
    # rho, attempts, delta, bound, expected cells
    (0.491, 20, 0.05, 1e-2, 154),
    (0.491, 20, 0.05, 1e-3, 1546),
    (0.491, 20, 0.05, 1e-6, 1546000),
    (0.01,  20, 0.05, 1e-3, 178),
]

def check():
    """Reproduce the figures in protocol section 4.

    The protocol prints rounded counts; this tool returns the smallest integer count that
    satisfies the inequality. The check therefore asks whether the printed figure and the
    computed ceiling agree within rounding, and says so rather than hiding the difference.
    """
    bad = 0
    for rho, j, delta, lam, want in PROTOCOL_CASES:
        got, exact, d = cells_for_bound(lam, delta, rho, j)
        tol = max(1, 0.01 * want)
        ok = want <= got <= want + tol
        bad += 0 if ok else 1
        print(f"{'ok  ' if ok else 'FAIL'} rho={rho} J={j} delta={delta} bound={lam:g} "
              f"deff={d:.3f} exact={exact:.1f} cells={got} protocol={want}")
    n_ind = math.log(0.05) / math.log(1.0 - 1e-3)
    print(f"ok   independent baseline: {math.ceil(n_ind)} attempts, {math.ceil(n_ind / 20)} cells at J=20")
    print("note protocol prints rounded counts; this tool returns the smallest integer that satisfies")
    print("     the inequality. Within one unit at small counts, within a percent at large ones.")
    print("RESULT: PASS" if not bad else "RESULT: FAIL")
    return 0 if not bad else 2

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rho", type=float, help="intra-cluster correlation measured in this stratum")
    ap.add_argument("--attempts", type=int, default=20, help="attempts per cell (J)")
    ap.add_argument("--bound", type=float, help="target failure rate lambda (zero-failure bound)")
    ap.add_argument("--delta", type=float, default=0.05, help="confidence level delta")
    ap.add_argument("--half-width", type=float, help="target 95%% half-width on a proportion near p")
    ap.add_argument("--p", type=float, default=0.5, help="proportion for the half-width mode")
    ap.add_argument("--check", action="store_true", help="reproduce the protocol section 4 figures")
    ap.add_argument("--json", action="store_true", help="print a JSON object instead of lines")
    a = ap.parse_args()

    if a.check:
        return check()
    if a.rho is None:
        ap.error("--rho is required (or use --check)")
    if not (a.bound or a.half_width):
        ap.error("give --bound (zero-failure) or --half-width (precision)")

    out = {"rho": a.rho, "attempts_per_cell": a.attempts, "deff": round(deff(a.attempts, a.rho), 3),
           "ceiling_n_eff": round(1.0 / a.rho, 2) if a.rho > 0 else None,
           "attempts_to_saturation": attempts_for_saturation(a.rho)}

    if a.bound:
        cells, exact, d = cells_for_bound(a.bound, a.delta, a.rho, a.attempts)
        ind = math.ceil(math.log(a.delta) / math.log(1.0 - a.bound))
        out.update({"mode": "zero-failure bound", "bound": a.bound, "delta": a.delta,
                    "cells": cells, "cells_exact": round(exact, 2),
                    "independent_attempts": ind, "independent_cells": math.ceil(ind / a.attempts),
                    "excess_over_independent": round(d, 3)})
        if not a.json:
            print(f"rho={a.rho}  J={a.attempts}  deff={d:.3f}  bound lambda={a.bound:g} at delta={a.delta:g}")
            print(f"cells needed: {cells}   ({exact:.2f} exactly)")
            print(f"independent baseline: {ind} attempts = {math.ceil(ind / a.attempts)} cells at J={a.attempts}")
            print(f"the correlation multiplies the requirement by deff = {d:.3f}")
    else:
        cells, n_eff = cells_for_half_width(a.half_width, a.rho, a.p)
        out.update({"mode": "interval half-width", "half_width": a.half_width, "p": a.p,
                    "independent_observations": math.ceil(n_eff), "cells": cells})
        if not a.json:
            print(f"rho={a.rho}  target half-width +/-{a.half_width:g} at p={a.p}")
            print(f"independent observations needed: {math.ceil(n_eff)}")
            print(f"cells needed: {cells}  (a cell is worth at most {1 / a.rho:.2f} independent observations)")
            print(f"attempts per cell to reach 90% of that ceiling: {attempts_for_saturation(a.rho)}")
            print("arithmetic on the measured rho; a record using this mode says so")
    if a.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
