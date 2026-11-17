#!/usr/bin/env python3
"""Build a tiny synthetic release so the export->verify pipeline can be run
end to end by anyone, with no third-party data.

12 cells: 3 models x 4 tasks, 6 trials each = 72 runs. Outcomes are generated
from a fixed formula (no randomness, no seed), so the fixture is byte-stable.
"""
import hashlib, json, os

HERE = os.path.dirname(os.path.abspath(__file__))


def build():
    models = [("m_alpha", 0.83), ("m_beta", 0.67)]
    benches = ["robodojo-rc-tier-1", "simple-tasks", "roboharm-v1",
               "robospoof", "datacenterbench"]
    tasks = ["pick", "place"]
    runs = []
    for mi, (model, p) in enumerate(models):
        for bi, bench in enumerate(benches):
          for ti, task in enumerate(tasks):
            for trial in range(3):
                ok = ((mi * 7 + bi * 5 + ti * 3 + trial) % 10) < int(p * 10)
                if bench == "roboharm-v1":
                    outcome = "attempted_succeeded" if ok else "refused"
                elif bench == "robospoof":
                    outcome = "claimed_done" if ok else "attempted_failed"
                else:
                    outcome = "complete" if ok else "partial"
                runs.append({
                    "id": "fx-%s-%s-%s-%d" % (model, bench, task, trial),
                    "run": "fx_%s_%s_%s_%d" % (model, bench, task, trial),
                    "benchmark": bench,
                    "model": model,
                    "task": task + "-" + bench.split("-")[0],
                    "scene": "",
                    "effort": "medium",
                    "mode": "solo",
                    "trial": trial,
                    "control": "end-effector",
                    "outcome": "complete" if ok else "partial",
                    "score": 1.0 if ok else 0.0,
                    "date": "2026-01-01T0%d:%02d:00Z" % (trial, bi * 5 + ti * 3),
                    "grading": "Autograded",
                    "source": "fixture",
                    "replacement": False,
                    "rerun": False,
                    "log": "fixture://log/%s/%s/%s/%d" % (model, bench, task, trial),
                    "videos": ["Left", "Top"],
                    "leaderboard": ["demo"],
                    "minutes": 3.0 + (mi + ti) * 0.5,
                    "calls": 12 + ti,
                    "cost": 0.02,
                    "tokens": 4000,
                })
    snap = {"cohort_date": "2026-01-01", "models": {m: m.upper() for m, _ in models},
            "runs": runs, "safety": {}, "doll_study": {}}
    rel = os.path.join(HERE, "releases", "2026-01-01")
    os.makedirs(rel, exist_ok=True)
    path = os.path.join(rel, "robocurve_allruns.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=1, sort_keys=True)
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    manifest = {"archive": "EEO Archive", "release": "2026-01-01",
                "frozen_at_utc": "2026-01-01T00:00:00+00:00", "source_note": "synthetic",
                "note": "synthetic fixture, no third-party data",
                "files": [{"file": "robocurve_allruns.json", "bytes": os.path.getsize(path),
                           "sha256": h, "record_count": len(runs), "count_key": "runs"}]}
    with open(os.path.join(rel, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("fixture written:", path)


if __name__ == "__main__":
    build()
