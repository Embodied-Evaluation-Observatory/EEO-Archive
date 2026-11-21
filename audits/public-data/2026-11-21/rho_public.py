"""One-way intraclass correlation from a per-attempt table, with a cluster bootstrap.

Input: a CSV with columns site, cell, succ (0/1). Cells are the resampling unit.
"""
import sys, numpy as np, pandas as pd


def icc(y, g):
    d = pd.DataFrame({"y": y, "g": np.asarray(g)})
    grp = d.groupby("g")["y"]
    n = grp.size(); m = grp.mean()
    N = len(d); k = len(n); ybar = d.y.mean()
    msb = float((n * (m - ybar) ** 2).sum() / (k - 1))
    ssw = float(((d.y - d.groupby("g")["y"].transform("mean")) ** 2).sum())
    msw = ssw / (N - k) if N > k else float("nan")
    n0 = float((N - (n ** 2).sum() / N) / (k - 1))
    den = msb + (n0 - 1) * msw
    return ((msb - msw) / den if den > 0 else float("nan")), k, N, n0


def bootstrap(y, g, reps=600, seed=3):
    rng = np.random.default_rng(seed)
    d = pd.DataFrame({"y": y, "g": np.asarray(g)})
    cells = {c: d[d.g == c].y.values for c in d.g.unique()}
    keys = list(cells); vals = []
    for _ in range(reps):
        pick = rng.choice(len(keys), len(keys), replace=True)
        yy = np.concatenate([cells[keys[i]] for i in pick])
        gg = np.concatenate([[j] * len(cells[keys[i]]) for j, i in enumerate(pick)])
        v = icc(yy, gg)[0]
        if not np.isnan(v):
            vals.append(v)
    return np.percentile(vals, [2.5, 97.5])


if __name__ == "__main__":
    df = pd.read_csv(sys.argv[1])
    for definition in ("site", "cell"):
        r, k, N, n0 = icc(df.succ.values.astype(float), df[definition].values)
        lo, hi = bootstrap(df.succ.values.astype(float), df[definition].values)
        print(f"{definition}: rho={r:.4f} cells={k} attempts={N} n0={n0:.2f} "
              f"ci=[{lo:.3f},{hi:.3f}]")
