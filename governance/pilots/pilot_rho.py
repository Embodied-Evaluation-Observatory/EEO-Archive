"""Analysis for the AMR rho pilot: read the attempt log, estimate rho, report what it supports.

Usage: python3 pilot_rho.py amr_attempt_log.csv

Expects the columns of amr_attempt_log_template.csv. Cells are task_type x config_label.
Refuses to run on EXAMPLE rows and on a log whose definitions contradict the pilot.
"""
import sys
import numpy as np
import pandas as pd

REQUIRED = ["attempt_id", "date", "site_code", "task_type", "config_label", "attempt_index",
            "outcome_primary", "outcome_secondary", "takeover", "resets", "retries",
            "duration_min", "judge_role", "notes", "video"]


def icc(y, g):
    """One-way intraclass correlation, unbalanced cells, method of moments."""
    d = pd.DataFrame({"y": y, "g": np.asarray(g)})
    grp = d.groupby("g")["y"]
    n, m = grp.size(), grp.mean()
    N, k, ybar = len(d), len(n), d.y.mean()
    msb = float((n * (m - ybar) ** 2).sum() / (k - 1))
    ssw = float(((d.y - d.groupby("g")["y"].transform("mean")) ** 2).sum())
    msw = ssw / (N - k) if N > k else float("nan")
    n0 = float((N - (n ** 2).sum() / N) / (k - 1))
    den = msb + (n0 - 1) * msw
    return ((msb - msw) / den if den > 0 else float("nan")), k, N, n0, msw


def bootstrap(y, g, reps=2000, seed=11):
    """Cluster bootstrap: cells are the resampling unit, not attempts."""
    rng = np.random.default_rng(seed)
    d = pd.DataFrame({"y": y, "g": np.asarray(g)})
    cells = {c: d[d.g == c].y.values for c in d.g.unique()}
    keys, vals = list(cells), []
    for _ in range(reps):
        pick = rng.choice(len(keys), len(keys), replace=True)
        yy = np.concatenate([cells[keys[i]] for i in pick])
        gg = np.concatenate([[j] * len(cells[keys[i]]) for j, i in enumerate(pick)])
        v = icc(yy, gg)[0]
        if not np.isnan(v):
            vals.append(v)
    return np.percentile(vals, [2.5, 97.5])


def main(path):
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        sys.exit(f"missing columns: {missing}")
    if df.notes.fillna("").str.contains("EXAMPLE").any():
        sys.exit("log still contains EXAMPLE rows; delete them before analysis")

    for c in ("outcome_primary", "outcome_secondary", "takeover", "resets", "retries"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if df.outcome_primary.isna().any():
        sys.exit("outcome_primary has empty or non-numeric cells")
    if not set(df.outcome_primary.unique()) <= {0, 1}:
        sys.exit("outcome_primary must be 0 or 1")
    if len(set(df.judge_role)) > 1:
        print(f"note: {len(set(df.judge_role))} judge roles present; state this in the report")

    df["cell"] = df.task_type.astype(str) + "||" + df.config_label.astype(str)
    y, g = df.outcome_primary.values.astype(float), df.cell.values

    rho, k, N, n0, _ = icc(y, g)
    lo, hi = bootstrap(y, g)
    sizes = df.cell.value_counts()
    zero_var = df.groupby("cell").outcome_primary.agg(["size", "mean", "var"])
    zv_share = float((zero_var["var"].fillna(0) == 0).mean())
    deff = 1 + (sizes.median() - 1) * rho

    print(f"attempts {N}, cells {k}, mean outcome {y.mean():.3f}")
    print(f"attempts per cell: median {sizes.median():.0f}, min {sizes.min()}, max {sizes.max()}")
    print(f"rho {rho:.4f}  ci95 [{lo:.3f}, {hi:.3f}]  n0 {n0:.2f}")
    print(f"zero-variance cells {zv_share:.1%}")
    print(f"design effect at median J: {deff:.2f}")
    print()
    print("Reading: this design resolves rho to roughly +/-0.17. Report the interval, not the")
    print("point; use the upper bound for any sample-size plan. Cells closer than one attempt's")
    print("worth of independent information are not yet separable at this size.")
    if zv_share > 0.5:
        print("Warning: more than half the cells have no internal variance. The rho above is")
        print("then dominated by the ceiling; report the zero-failure bound instead.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
