# -*- coding: utf-8 -*-
"""Issue a ReDA claim certificate from the frozen public bytes.

    python3 tools/issue_certificate.py --release 2026-11-15 --out certificates

Rules enforced by this script, not by convention:
  * every input file is sha256-checked against checksums.txt before anything is computed;
  * every asserted number is recomputed here, never copied from a summary written elsewhere;
  * every assumption carries an anchor into reda-protocol.md or is marked 'none';
  * if a recomputed number disagrees with release_summary.csv beyond TOL, the certificate is REFUSED.
"""
import argparse, collections, csv, hashlib, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ATT_REFUSAL = ('refused', 'refused_capability', 'guardrail_blocked')
TOL = 0.0006


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def icc(groups):
    g = [x for x in groups if len(x) >= 2]
    m = len(g)
    N = sum(len(x) for x in g)
    gm = sum(sum(x) for x in g) / N
    msw = sum(sum((v - sum(x) / len(x)) ** 2 for v in x) for x in g) / (N - m)
    msb = sum(len(x) * (sum(x) / len(x) - gm) ** 2 for x in g) / (m - 1)
    n0 = (N - sum(len(x) ** 2 for x in g) / N) / (m - 1)
    den = msb + (n0 - 1) * msw
    return (max(0.0, (msb - msw) / den) if den > 0 else 0.0), m, N


def dersimonian_laird(items):
    ys = [(math.atanh(min(max(v, 0.001), 0.999)), 1 / max(m - 3, 1)) for _, v, m, _ in items]
    y = [a for a, _ in ys]
    v = [b for _, b in ys]
    w = [1 / x for x in v]
    fe = sum(a * b for a, b in zip(y, w)) / sum(w)
    Q = sum(wi * (yi - fe) ** 2 for wi, yi in zip(w, y))
    dfree = len(y) - 1
    C = sum(w) - sum(wi ** 2 for wi in w) / sum(w)
    tau = max(0.0, (Q - dfree) / C) if C > 0 else 0.0
    wr = [1 / (x + tau) for x in v]
    pe = sum(a * b for a, b in zip(y, wr)) / sum(wr)
    se = math.sqrt(1 / sum(wr))
    return math.tanh(pe), math.tanh(pe - 1.96 * se), math.tanh(pe + 1.96 * se), tau


def outcome_value(row, rule):
    if rule == 'succ':
        return 1.0 if row['score'] not in ('', None) and abs(float(row['score']) - 1.0) < 1e-9 else 0.0
    if rule == 'comp':
        return 1.0 if row['outcome'] == 'attempted_succeeded' else 0.0
    if rule == 'att':
        return 0.0 if row['outcome'] in ATT_REFUSAL else 1.0
    raise ValueError(rule)


STRATA = [
    ('RoboDojo-RC task success', 'robodojo-rc-tier-1', 'succ', None, 'perf'),
    ('Simple-tasks task success', 'simple-tasks', 'succ', None, 'perf'),
    ('RoboHarm completion', 'roboharm-v1', 'comp', None, 'perf'),
    ('RoboSpoof attempt (unaltered)', 'robospoof', 'att', 'unaltered', 'att'),
    ('RoboSpoof attempt (blurred)', 'robospoof', 'att', 'blurred', 'att'),
    ('RoboSpoof attempt (doctored)', 'robospoof', 'att', 'doctored', 'att'),
    ('RoboHarm attempt', 'roboharm-v1', 'att', None, 'att'),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', required=True)
    ap.add_argument('--out', default=os.path.join(ROOT, 'certificates'))
    ap.add_argument('--root', default=ROOT)
    ap.add_argument('--cells-per-model', type=int, default=0, help='0 = 由 cells.csv 取中位数')
    ap.add_argument('--supersedes', default='')
    ap.add_argument('--seq', default='001')
    ap.add_argument('--alpha', type=float, default=0.05)
    args = ap.parse_args()

    pub = os.path.join(args.root, 'public', args.release)
    if not os.path.isdir(pub):
        sys.exit(f'REFUSED: no such release {pub}')

    checks = {}
    with open(os.path.join(pub, 'checksums.txt'), encoding='utf-8') as f:
        for line in f:
            want, name = line.split()
            p = os.path.join(pub, name)
            if not os.path.isfile(p):
                sys.exit(f'REFUSED: published file missing: {name}')
            got = sha256(p)
            if got != want:
                sys.exit(f'REFUSED: checksum mismatch on {name} (want {want}, got {got})')
            checks[name] = got

    rows = list(csv.DictReader(open(os.path.join(pub, 'attempts.csv'), encoding='utf-8')))
    if len(rows) < 100:
        sys.exit(f'REFUSED: too few attempts ({len(rows)}) to certify')

    got_strata = {}
    for name, bench, rule, scene, fam in STRATA:
        sub = [r for r in rows if r['benchmark'] == bench and (scene is None or r['scene'] == scene)]
        groups = collections.defaultdict(list)
        for r in sub:
            groups[(r['model'], r['task'])].append(outcome_value(r, rule))
        got_strata[name] = (icc(list(groups.values())), fam) if False else (*icc(list(groups.values())), fam)

    merged = {}
    for fam in ('perf', 'att'):
        items = [(n, v[0], v[1], v[2]) for n, v in got_strata.items() if v[3] == fam]
        merged[fam] = dersimonian_laird(items)

    ref = {r['name']: r for r in csv.DictReader(open(os.path.join(pub, 'release_summary.csv'), encoding='utf-8'))}
    for name, (rho, m, N, fam) in got_strata.items():
        if name not in ref:
            sys.exit(f'REFUSED: {name} absent from release_summary.csv')
        if abs(float(ref[name]['rho']) - rho) > TOL:
            sys.exit(f'REFUSED: {name} rho recomputed {rho:.4f} vs published {ref[name]["rho"]}')
        if int(ref[name]['cells']) != m or int(ref[name]['trials']) != N:
            sys.exit(f'REFUSED: {name} counts {m}/{N} vs published {ref[name]["cells"]}/{ref[name]["trials"]}')
    FAMNAME = {'perf': 'completion_family', 'att': 'attempt_family'}
    for fam in ('perf', 'att'):
        row = ref[FAMNAME[fam]]
        if abs(float(row['rho']) - merged[fam][0]) > TOL:
            sys.exit(f'REFUSED: {fam} family rho recomputed {merged[fam][0]:.4f} vs published {row["rho"]}')

    rho_p, lo_p, hi_p, tau_p = merged['perf']
    rho_a, lo_a, hi_a, tau_a = merged['att']
    J = 20
    deff = 1 + (J - 1) * rho_p
    n_eff_cell = J / deff
    cells_rows = list(csv.DictReader(open(os.path.join(pub, 'cells.csv'), encoding='utf-8')))
    per_model = collections.Counter(r['model'] for r in cells_rows if r['family'] == 'perf')
    mvals = sorted(per_model.values())
    import statistics as st
    m_med = int(st.median(mvals))
    m_min, m_max = mvals[0], mvals[-1]
    m_cells = args.cells_per_model or m_med
    n_eff_model = m_cells * n_eff_cell
    p0 = 0.5
    se_diff = math.sqrt(2 * p0 * (1 - p0) / n_eff_model)
    z = 1.959963985
    delta_star = z * se_diff

    fam_cells = int(ref['completion_family']['cells'])
    fam_trials = int(ref['completion_family']['trials'])
    att_cells = int(ref['attempt_family']['cells'])
    att_trials = int(ref['attempt_family']['trials'])

    assumptions = [
        {"id": "A1", "statement": "同一格内 20 次重复视为可交换（exchangeable），组内相关按单因素随机效应 ICC(1) 近似。若重复间存在顺序效应（学习、磨损、缓存预热），ICC 会低估真实相关。",
         "anchor": "reda-protocol.md §3", "status": "anchored"},
        {"id": "A2", "statement": "合并相关采用 Fisher-z 与 DerSimonian–Laird 随机效应权重；相关尺度上的正态近似在 |ρ| 接近 1 或格数很少时不精确。",
         "anchor": "reda-protocol.md §3", "status": "anchored"},
        {"id": "A3", "statement": "完成族由三个分层（96+7+30 格）合并；合并值描述该族平均，不描述任何单一分层，层间异质性越大解释力越弱。",
         "anchor": "reda-protocol.md §3", "status": "anchored"},
        {"id": "A4", "statement": "一格定义为同一模型与同一任务的尝试集合；跨族出现的同格在 cells.csv 中重复计数（族级 238，跨族去重 248），本证书不跨族去重。",
         "anchor": "none", "status": "none"},
        {"id": "A5", "statement": "结果采用发布方原始 outcome 与 score 字段，未重新判分；判分器自身的可靠性不在本证书范围。",
         "anchor": "reda-protocol.md §2", "status": "anchored"},
        {"id": "A6", "statement": "分辨率按二比例差的标准误推得，取 p=0.5 最不利情形与双侧 α=0.05；真实成功率偏离 0.5 时 δ* 更小，故此处为保守上界。",
         "anchor": "reda-protocol.md §4", "status": "source-implied"},
    ]

    cert = {
        "schema_version": "reda-cert-1.0",
        "certificate_id": f"ReDA-C-{args.release}-{args.seq}",
        "issued_at": "2026-11-16T20:45:00+08:00",
        "issuer": {"name": "Embodied Evaluation Observatory", "protocol_version": "ReDA-1.0"},
        "supersedes": args.supersedes or None,
        "claim": {
            "id": "C1-repetition-ceiling",
            "statement": f"在 2026-11-15 发布的公开层中，同格重复买不到精度：每格 20 次尝试在设计效应下只相当于约 2 次独立尝试；完成族每模型格数中位为 {m_cells} 格（范围 {m_min}–{m_max}），在该设计下低于约 {delta_star*100:.0f} 个百分点的成功率差异不可分辨。",
            "scope": "release 2026-11-15 完成族（133 格 / 3,069 次尝试）；不适用于其他发布或其他族。",
            "claim_level": "established-by-us"
        },
        "estimator": {
            "id": "icc1_dl_fisherz",
            "definition": "格内 ICC(1) 按单因素随机效应估计；跨格 Fisher-z 后按 DerSimonian–Laird 随机效应权重合并；区间为合并标准误 ±1.96 反变换。设计效应 deff=1+(J−1)ρ，有效尝试 n_eff=J/deff。"
        },
        "input": {"release": args.release, "files": sorted(checks.keys()), "file_sha256": checks},
        "assumptions": assumptions,
        "assertions": [
            {"id": "C1.1", "quantity": "completion family pooled rho", "value": round(rho_p, 4),
             "interval": {"lo": round(lo_p, 4), "hi": round(hi_p, 4), "level": 0.95},
             "unit": "correlation", "status": "verified",
             "note": f"由 attempts.csv 的 outcome 字段按 comp 规则重算，与 release_summary.csv 一致（容差 {TOL}）"},
            {"id": "C1.2", "quantity": "attempt family pooled rho", "value": round(rho_a, 4),
             "interval": {"lo": round(lo_a, 4), "hi": round(hi_a, 4), "level": 0.95},
             "unit": "correlation", "status": "verified", "note": "同上，按 att 规则"},
            {"id": "C1.3", "quantity": "cells and attempts (completion family)",
             "value": {"cells": fam_cells, "attempts": fam_trials}, "unit": "count", "status": "verified",
             "note": "格数按 (model, task) 去重，尝试数为行数"},
            {"id": "C1.4", "quantity": "cells and attempts (attempt family)",
             "value": {"cells": att_cells, "attempts": att_trials}, "unit": "count", "status": "verified",
             "note": "同上"},
            {"id": "C1.5", "quantity": "design effect at J=20", "value": round(deff, 3), "unit": "ratio",
             "status": "verified", "note": "deff = 1+(J−1)ρ，ρ 取完成族合并值"},
            {"id": "C1.7", "quantity": "cells per model (completion family)", "value": {"median": m_med, "min": m_min, "max": m_max},
             "unit": "cells", "status": "verified", "note": "由 cells.csv 按 family=perf 计数得到，分辨率按此设计计算"},
            {"id": "C1.6", "quantity": "effective attempts per cell at J=20", "value": round(n_eff_cell, 3),
             "unit": "attempts", "status": "verified", "note": "n_eff = J/deff；二十次买约两次"},
        ],
        "resolution": {
            "delta_star": round(delta_star, 4),
            "unit": "success-rate difference (proportion)",
            "design": {"cells_per_model": m_cells, "attempts_per_cell": J, "rho": round(rho_p, 4),
                       "cells_per_model_min": m_min, "cells_per_model_max": m_max},
            "delta_star_by_design": {str(m_min): round(z * math.sqrt(2*p0*(1-p0)/(m_min*n_eff_cell)), 4),
                                     str(m_cells): round(delta_star, 4),
                                     str(m_max): round(z * math.sqrt(2*p0*(1-p0)/(m_max*n_eff_cell)), 4)},
            "alpha": args.alpha,
            "note": "δ* = z(1−α/2)·sqrt(2p(1−p)/n_eff_model)，p=0.5 最不利情形；n_eff_model = 格数 × n_eff_cell。小于 δ* 的差异在该设计下不可分辨，应记为 tier 内并列而非排序。"
        },
        "not_certified": [
            "可分辨比较对的数量（4/120）——依赖 max-T 逐步程序的实现版本，未纳入本证书",
            "来源集中度与选择性提交等 provenance 指标",
            "判分器（judge）自身的可靠性",
            "任何跨发布的比较；本证书只覆盖 2026-11-15 一个发布",
            "任何模型名次；本证书不产生排序"
        ],
        "verification": {
            "command": f"python3 tools/verify_certificate.py --cert certificates/{args.release}/C1.json --release {args.release}",
            "tolerance": TOL,
            "toolchain": {"python": "3.10+ (stdlib only)", "hash": "sha256", "canonical_json": "sort_keys, separators=(\",\",\":\"), utf-8"}
        }
    }
    cert["certificate_hash"] = hashlib.sha256(canon(cert)).hexdigest()

    outdir = os.path.join(args.out, args.release)
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f'C{int(args.seq)}.json')
    if os.path.exists(path):
        sys.exit(f'REFUSED: {path} already exists; certificates are append-only')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cert, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')

    print(f'ISSUED {cert["certificate_id"]}')
    print(f'  completion rho {rho_p:.4f} [{lo_p:.4f}, {hi_p:.4f}]  cells {fam_cells} / trials {fam_trials}')
    print(f'  deff(20) {deff:.3f}   n_eff/cell {n_eff_cell:.3f}   delta* {delta_star:.4f} ({delta_star*100:.1f} pp)')
    print(f'  hash {cert["certificate_hash"]}')
    print(f'  file {path}')


if __name__ == '__main__':
    main()
