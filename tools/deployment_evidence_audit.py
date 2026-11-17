#!/usr/bin/env python3
"""Audit deployment-evidence rows: assign evidence grade by form, check
denominator consistency, and report a Wilson interval next to the quoted
success rate.

Usage:
  python3 tools/deployment_evidence_audit.py --in templates/deployment-evidence/deployment_evidence_template.csv
"""
import argparse, csv, json, math
from collections import Counter

FIELDS = ["product", "scenario", "task_set", "continuous_hours", "attempts", "successes",
          "significant_failures", "human_interventions", "denominator_defined",
          "intervention_counted_as_failure", "log_available", "continuous_video",
          "third_party_present", "claim_text", "claim_source", "evidence_grade", "notes"]


def yn(v):
    return str(v).strip().lower() in ("是", "y", "yes", "true", "1")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - m) / d, (c + m) / d)


def grade(row):
    has_log = bool(str(row["log_available"]).strip()) and not yn(row["log_available"]) is False
    has_log = str(row["log_available"]).strip() not in ("", "无", "none", "否", "no")
    has_video = str(row["continuous_video"]).strip() not in ("", "无", "none", "否", "no")
    has_third = str(row["third_party_present"]).strip() not in ("", "无", "none", "否", "no")
    denom = yn(row["denominator_defined"])
    inter = yn(row["intervention_counted_as_failure"])
    if has_log and denom and inter and has_video and has_third:
        return "A"
    if has_log and denom and (has_video or has_third):
        return "B"
    if str(row["attempts"]).strip() and str(row["successes"]).strip():
        return "C"
    return "D"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    rows = []
    with open(a.inp, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if not any((v or "").strip() for v in r.values()):
                continue
            for k in FIELDS:
                r.setdefault(k, "")
            flags = []
            n = s = iv = 0
            try:
                n = int(float(r["attempts"])) if str(r["attempts"]).strip() else 0
                s = int(float(r["successes"])) if str(r["successes"]).strip() else 0
                iv = int(float(r["human_interventions"])) if str(r["human_interventions"]).strip() else 0
            except ValueError:
                flags.append("非数值")
            if n and s > n:
                flags.append("成功数大于尝试数")
            if not yn(r["denominator_defined"]):
                flags.append("分母未写明")
            if not yn(r["intervention_counted_as_failure"]):
                flags.append("介入未计入失败")
            lo, hi = wilson(s, n) if n else (0, 0)
            rows.append({"product": r["product"], "scenario": r["scenario"],
                         "attempts": n, "successes": s,
                         "success_rate": round(100 * s / n, 1) if n else "",
                         "wilson_lo": round(100 * lo, 1) if n else "",
                         "wilson_hi": round(100 * hi, 1) if n else "",
                         "intervention_rate": round(100 * iv / n, 1) if n else "",
                         "grade": grade(r), "flags": ";".join(flags)})
    summary = {"rows": len(rows), "grade_counts": Counter(r["grade"] for r in rows),
               "flagged": sum(1 for r in rows if r["flags"])}
    print(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2))
    if a.out:
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["product"])
            w.writeheader()
            w.writerows(rows)


if __name__ == "__main__":
    main()
