#!/usr/bin/env python3
"""Board audit: normalize public leaderboards into one cell schema and run two
defensible separability tests.

Boards covered (2026-11-17):
  - robocurve        per-run records  -> handled by tools/discriminate.py
  - robochallenge    per-task aggregate rows, no per-cell n
  - roboarena        Elo board with reported std and eval counts

Two tests are used here because these boards do not publish per-cell attempt
counts. Neither test needs n:

  sign test        model A beats B on k of m shared tasks; exact two-sided
                   binomial(m, 0.5). Task-level sign consistency, not a
                   sampling-error statement.
  rating gap       |Elo_a - Elo_b| against 1.96*sqrt(std_a^2 + std_b^2) using
                   the std the board reports. This is board-reported
                   uncertainty, not a confidence interval over attempts.

Usage:
  python3 tools/board_audit.py --raw boards/2026-11-17/raw --out boards/2026-11-17
"""
import argparse, csv, hashlib, json, math, os, statistics
from collections import defaultdict
from math import comb


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path, key):
    with open(path, encoding="utf-8") as f:
        return json.load(f)[key] if key else json.load(f)


def norm_model(row):
    return (row.get("display_name") or row.get("user_name") or "").strip()


def ingest_robochallenge(raw, out, snapshot):
    src = "https://robochallenge.ai/api/v2/leaderboard/leaderboard_task_all.json"
    rows = json.load(open(os.path.join(raw, "robochallenge_leaderboard_task_all.json"), encoding="utf-8"))
    meta = json.load(open(os.path.join(raw, "robochallenge_benchmark_list_v2.json"), encoding="utf-8"))[0]
    tmeta = json.load(open(os.path.join(raw, "robochallenge_task_meta.json"), encoding="utf-8"))
    task_name = {t["task_id"]: t["task_name"] for t in tmeta}
    task_robot = {t["task_id"]: t["robot_tag"] for t in tmeta}

    best = {}
    for r in rows:
        model = norm_model(r)
        for t in r.get("task_results", []):
            key = (t["task_id"], model)
            ts = t.get("running_end_time") or t.get("submit_time") or ""
            cand = {
                "board": "robochallenge",
                "benchmark": meta["benchmark_name"] + " (v2)",
                "model": model,
                "task": task_name.get(t["task_id"], t["task_id"]),
                "embodiment": task_robot.get(t["task_id"], ""),
                "control": "",
                "metric": "success_ratio",
                "value": float(t["success_ratio"]),
                "n": "",                       # per-cell attempts not published
                "n_scope": "unstated",
                "snapshot": snapshot,
                "source_url": src,
                "extra": json.dumps({"task_id": t["task_id"], "score": t.get("score"),
                                     "weight": t.get("weight"), "submitted": ts,
                                     "category": r.get("category")}),
            }
            if key not in best or ts > best[key]["_ts"]:
                cand["_ts"] = ts
                best[key] = cand

    cells = []
    for v in best.values():
        v.pop("_ts")
        cells.append(v)
    write_cells(os.path.join(out, "robochallenge_cells.csv"), cells)
    return {"board": "robochallenge", "benchmark": meta["benchmark_name"] + " (v2)",
            "cells": len(cells), "models": len({c["model"] for c in cells}),
            "tasks": len({c["task"] for c in cells}),
            "embodiments": sorted({c["embodiment"] for c in cells}),
            "n_reported": 0, "benchmark_episodes": int(meta["episode_number"]),
            "source_url": src}



def _p_two_sided(z):
    return math.erfc(abs(z) / math.sqrt(2))


def holm_adjust(pairs, pkey, alpha):
    """Step-down Holm across all pairs of one board; rewrites 'separated'."""
    live = [p for p in pairs if p.get(pkey) is not None]
    order = sorted(range(len(live)), key=lambda i: live[i][pkey])
    m = len(order)
    last = -1
    for rank, idx in enumerate(order):
        if live[idx][pkey] <= alpha / (m - rank):
            last = rank
        else:
            break
    for rank, idx in enumerate(order):
        live[idx]['p_adjusted'] = round(min(1.0, (m - rank) * live[idx][pkey]), 6)
        live[idx]['separated'] = rank <= last
    return len([p for p in live if p['separated']])

def sign_test(k, m):
    if m < 2:
        return 1.0
    obs = comb(m, k) / (2 ** m)
    p = sum(comb(m, i) / (2 ** m) for i in range(m + 1) if comb(m, i) / (2 ** m) <= obs * (1 + 1e-12))
    return min(1.0, p)


def run_sign(path, out, min_shared=4, alpha=0.05, adjust=True):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    by_task = defaultdict(dict)
    for r in rows:
        by_task[r["task"]][r["model"]] = float(r["value"])
    models = sorted({r["model"] for r in rows})
    pairs = []
    for i, a in enumerate(models):
        for b in models[i + 1:]:
            win = loss = tie = 0
            detail = []
            for task, mv in by_task.items():
                if a in mv and b in mv:
                    d = mv[a] - mv[b]
                    if d > 0:
                        win += 1
                    elif d < 0:
                        loss += 1
                    else:
                        tie += 1
                    detail.append(task)
            m = win + loss
            if m < min_shared:
                continue
            pairs.append({"model_a": a, "model_b": b, "shared_tasks": m, "a_wins": win,
                          "b_wins": loss, "ties": tie, "sign_p": round(sign_test(max(win, loss), m), 6),
                          "separated": sign_test(max(win, loss), m) < alpha})
    pairs.sort(key=lambda p: p["sign_p"])
    with open(os.path.join(out, "robochallenge_sign_pairs.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pairs[0].keys()) if pairs else
                           ["model_a", "model_b", "shared_tasks", "a_wins", "b_wins", "ties", "sign_p", "separated"])
        w.writeheader()
        w.writerows(pairs)
    if adjust:
        sep = holm_adjust(pairs, "sign_p", alpha)
    else:
        sep = sum(1 for p in pairs if p["separated"])
    return {"pairs": len(pairs), "separated": sep, "adjust": "holm" if adjust else "none",
            "undiscernible_share": round(100 * (1 - sep / len(pairs)), 1) if pairs else None,
            "min_shared": min_shared, "alpha": alpha}


def ingest_roboarena(raw, out, snapshot, adjust=True, alpha=0.05):
    src = "https://roboarena-api-domain-name.online/api/leaderboard"
    d = json.load(open(os.path.join(raw, "roboarena_leaderboard.json"), encoding="utf-8"))
    board = d["board"]
    rows = []
    for r in board:
        rows.append({"policy": r["policy"], "elo": float(r["score"]),
                     "elo_std": float(r.get("std") or 0.0),
                     "num_evals": int(r.get("num_evals") or 0),
                     "open_source": r.get("open_source"),
                     "uptime_fraction": (r.get("status") or {}).get("uptime_fraction")})
    rows.sort(key=lambda r: -r["elo"])
    with open(os.path.join(out, "roboarena_board.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    pairs = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            delta = a["elo"] - b["elo"]
            se = math.sqrt(a["elo_std"] ** 2 + b["elo_std"] ** 2)
            pairs.append({"policy_a": a["policy"], "policy_b": b["policy"],
                          "delta_elo": round(delta, 1), "se": round(se, 1),
                          "sep_threshold": round(1.96 * se, 1),
                          "elo_p": round(_p_two_sided(delta / se), 6),
                          "p": round(_p_two_sided(delta / se), 6),
                          "separated": abs(delta) > 1.96 * se})
    with open(os.path.join(out, "roboarena_pairs.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pairs[0].keys()))
        w.writeheader()
        w.writerows(pairs)
    if adjust:
        sep = holm_adjust(pairs, "elo_p", alpha)
    else:
        sep = sum(1 for p in pairs if p["separated"])
    thin = [r["policy"] for r in rows if r["num_evals"] < 50]
    return {"board": "roboarena", "policies": len(rows), "source_url": src,
            "pairs": len(pairs), "separated": sep,
            "adjust": "holm" if adjust else "none",
            "undiscernible_share": round(100 * (1 - sep / len(pairs)), 1),
            "thin_evidence_policies": thin,
            "median_num_evals": statistics.median([r["num_evals"] for r in rows]),
            "top_policy": rows[0]["policy"], "top_elo": rows[0]["elo"], "top_evals": rows[0]["num_evals"]}



def ingest_robotwin(raw, out, snapshot, adjust=True, alpha=0.05):
    """RoboTwin 2.0 publishes per-task success rates with 100 trials per task,
    so cells carry a real n."""
    src = "https://robotwin-platform.github.io/data/robotwin_leaderboard.json"
    d = json.load(open(os.path.join(raw, "robotwin_leaderboard.json"), encoding="utf-8"))
    tasks = d["tasks"]
    trials = 100
    cells = []
    for e in d["entries"]:
        for split, key in (("clean", "easy"), ("randomized", "hard")):
            rates = e.get(key) or []
            for task, p in zip(tasks, rates):
                if p is None:
                    continue
                cells.append({"board": "robotwin", "benchmark": "RoboTwin 2.0 (" + split + ")",
                              "model": e["name"], "task": task,
                              "embodiment": "Aloha-AgileX", "control": "",
                              "metric": "success_rate", "value": float(p) / 100.0,
                              "n": trials, "n_scope": "per_cell", "snapshot": snapshot,
                              "source_url": src,
                              "extra": json.dumps({"setting": e.get("setting"), "entry_id": e.get("id")})})
    write_cells(os.path.join(out, "robotwin_cells.csv"), cells)

    # pooled two-proportion separation over shared tasks, n = 100 per cell
    by = defaultdict(dict)
    for c in cells:
        if c["benchmark"].endswith("(clean)"):
            by[c["task"]][c["model"]] = c["value"]
    models = sorted({c["model"] for c in cells})
    pairs = []
    for i, a in enumerate(models):
        for b in models[i + 1:]:
            shared = [t for t in by if a in by[t] and b in by[t]]
            m = len(shared)
            if m < 10:
                continue
            pa = sum(by[t][a] for t in shared) / m
            pb = sum(by[t][b] for t in shared) / m
            var = sum((by[t][a] * (1 - by[t][a]) + by[t][b] * (1 - by[t][b])) / trials for t in shared) / (m * m)
            se = math.sqrt(var)
            delta = pa - pb
            pairs.append({"model_a": a, "model_b": b, "shared_tasks": m,
                          "p_a": round(pa, 4), "p_b": round(pb, 4),
                          "delta_pp": round(100 * delta, 2), "se_pp": round(100 * se, 2),
                          "elo_p": round(_p_two_sided(delta / se), 6),
                          "p": round(_p_two_sided(delta / se), 6),
                          "separated": abs(delta) > 1.96 * se})
    with open(os.path.join(out, "robotwin_pairs.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pairs[0].keys()) if pairs else
                           ["model_a", "model_b", "shared_tasks", "p_a", "p_b", "delta_pp", "se_pp", "separated"])
        w.writeheader(); w.writerows(pairs)
    if adjust:
        sep = holm_adjust(pairs, "p", alpha)
    else:
        sep = sum(1 for p in pairs if p["separated"])
    return {"board": "robotwin", "methods": len(models), "tasks": len(tasks),
            "adjust": "holm" if adjust else "none",
            "cells": len(cells), "n_per_cell": trials, "n_reported": len(cells),
            "pairs": len(pairs), "separated": sep,
            "undiscernible_share": round(100 * (1 - sep / len(pairs)), 1) if pairs else None,
            "source_url": src}


def write_cells(path, cells):
    fields = ["board", "benchmark", "model", "task", "embodiment", "control", "metric", "value", "n", "n_scope", "snapshot", "source_url", "extra"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(cells)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--snapshot", default="2026-11-17")
    ap.add_argument("--min-shared", type=int, default=4)
    ap.add_argument("--adjust", default="holm", choices=["holm", "none"],
                    help="holm: step-down correction across all pairs of a board (default); "
                         "none: per-pair 95%% intervals, as in the 2026-11-17 release")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    summary = {"snapshot": a.snapshot, "raw_hashes": {}}
    for f in sorted(os.listdir(a.raw)):
        summary["raw_hashes"][f] = sha256(os.path.join(a.raw, f))

    rc = ingest_robochallenge(a.raw, a.out, a.snapshot)
    adj = (a.adjust == "holm")
    rc.update(run_sign(os.path.join(a.out, "robochallenge_cells.csv"), a.out,
                       min_shared=a.min_shared, adjust=adj))
    ra = ingest_roboarena(a.raw, a.out, a.snapshot, adjust=adj)
    rt = ingest_robotwin(a.raw, a.out, a.snapshot, adjust=adj)
    summary["boards"] = {"robochallenge": rc, "roboarena": ra, "robotwin": rt}

    with open(os.path.join(a.out, "board_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary["boards"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
