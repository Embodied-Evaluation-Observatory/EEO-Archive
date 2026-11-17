#!/usr/bin/env python3
"""Failure attribution from robocurve run logs.

The logs embed the agent transcript. When the agent stops short of success it
usually calls a `give_up` tool whose argument states, in its own words, why it
stopped. That text is the only failure signal in the archive; it is
self-reported and not verified against video.

Classes (first-match, deterministic keyword rules):
  grasp_empty     抓空
  collision       碰撞或撞倒
  stall           卡住或耗尽步数
  placement       放置偏差
  grip_event      滑脱或掉落
  other           其他

Usage:
  python3 tools/failure_attr.py --sample sample.json --dir logs --out findings/failure
"""
import argparse, csv, html, json, os, re, statistics
from collections import Counter

RULES = [
    ("grasp_empty", [r"did not grasp", r"didn't grasp", r"closed on (?:nothing|empty)", r"no contact",
                     r"missed the object", r"could not (?:pick|grasp|grab)", r"never (?:grasped|grabbed)",
                     r"close was empty", r"every close", r"couldn'?t (?:secure|grasp|pick)",
                     r"beyond (?:the )?reach", r"reach limit", r"could not grasp"]),
    ("collision", [r"knock(?:ed|ing)? (?:over|it|the)", r"collision", r"collided", r"bumped into",
                   r"tipped (?:over|onto)", r"toppled", r"hit the", r"pushed it", r"ejected"]),
    ("grip_event", [r"dropped", r"slipped out", r"let go", r"fell out of", r"lost (?:the )?grip"]),
    ("placement", [r"did not go on", r"not (?:on|inside|in) the", r"misalign", r"slipped off",
                   r"off the (?:table|plate|surface)", r"gap between"]),
    ("stall", [r"no progress", r"stuck", r"ran out of (?:steps|time|calls)", r"time(?:d)? out",
               r"step limit", r"call limit"]),
]

FIELDS = ["run_id", "benchmark", "model", "task", "outcome", "calls", "minutes",
          "max_steps", "total_steps", "duration_s", "max_llm_calls", "give_up",
          "reason_class", "reason_text", "log_bytes", "parsed_from"]


def text_of(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def header(text):
    d = {}
    for k, v in re.findall(r"<dt>(.*?)</dt><dd>(.*?)</dd>", text, re.S):
        k = html.unescape(k).strip()
        if k not in d:
            d[k] = html.unescape(re.sub("<[^>]+>", "", v)).strip()
    return d


def give_up_text(text):
    m = re.findall(r"give_up\s*[:：]\s*(.+)", text)
    if not m:
        return ""
    raw = m[-1]
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(re.sub(r"\s+", " ", raw)).strip()
    return raw[:600]


def classify(txt):
    if not txt:
        return "no_reason"
    low = txt.lower()
    hits = [cls for cls, pats in RULES if any(re.search(p, low) for p in pats)]
    return ",".join(hits) if hits else "other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    sample = json.load(open(a.sample, encoding="utf-8"))
    rows = []
    for i, s in enumerate(sample):
        path = os.path.join(a.dir, f"{i}.html")
        if not os.path.exists(path):
            rows.append({**{k: s.get(k, "") for k in ("id", "benchmark", "model", "task", "outcome")},
                         "run_id": s.get("id"), "reason_class": "missing_log", "log_bytes": 0, "parsed_from": path})
            continue
        body = text_of(path)
        h = header(body)
        g = give_up_text(body)
        cls = classify(g)
        if cls == "no_reason" and str(s.get("calls") or "") in ("40", "40.0"):
            cls = "stall"          # call budget exhausted, no stated reason
        rows.append({"run_id": s.get("id"), "benchmark": s.get("benchmark"), "model": s.get("model"),
                     "calls": s.get("calls"), "minutes": round(float(s["minutes"]), 2) if s.get("minutes") else "",
                     "task": s.get("task"), "outcome": s.get("outcome"),
                     "max_steps": h.get("max steps", ""), "total_steps": h.get("total steps", ""),
                     "duration_s": (h.get("duration") or "").replace(" s", ""),
                     "max_llm_calls": h.get("max_llm_calls", ""),
                     "give_up": "yes" if g else "no", "reason_class": cls,
                     "reason_text": g, "log_bytes": len(body), "parsed_from": os.path.relpath(path)})

    os.makedirs(a.out, exist_ok=True)
    out = os.path.join(a.out, "failure_pilot.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})

    dist = Counter()
    for r in rows:
        for cls in str(r["reason_class"]).split(","):
            dist[cls] += 1
    cover = sum(1 for r in rows if r["reason_class"] not in ("no_reason", "missing_log"))
    steps = [int(r["total_steps"]) for r in rows if str(r.get("total_steps", "")).isdigit()]
    summary = {"runs": len(rows), "with_log": sum(1 for r in rows if r["reason_class"] != "missing_log"),
               "reason_found": cover, "reason_share": round(100 * cover / len(rows), 1),
               "distribution_year": None, "distribution": dict(dist),
               "median_total_steps": statistics.median(steps) if steps else None,
               "median_log_bytes": statistics.median([r["log_bytes"] for r in rows if r["log_bytes"]])}
    with open(os.path.join(a.out, "failure_pilot_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for r in rows:
        if r.get("give_up") == "yes":
            print("\n-", r["benchmark"], r["outcome"], r["reason_class"], "|", r["reason_text"][:220])


if __name__ == "__main__":
    main()
