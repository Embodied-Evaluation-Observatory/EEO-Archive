# -*- coding: utf-8 -*-
"""Reader-side verification of a ReDA claim certificate.

    python3 tools/verify_certificate.py --cert certificates/2026-11-15/C2.json

Checks, in order:
  1. the certificate hash matches its own canonical content (nothing edited after signing);
  2. every input file still matches the sha256 recorded at signing time;
  3. every asserted quantity is recomputed from those bytes and compared within tolerance;
  4. the resolution is recomputed from the design recorded in the certificate.
Exit 0 = the certificate is valid for these bytes. Exit 1 = it is not.
"""
import argparse, collections, csv, hashlib, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ATT_REFUSAL = ('refused', 'refused_capability', 'guardrail_blocked')


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
    m = len(g); N = sum(len(x) for x in g)
    gm = sum(sum(x) for x in g) / N
    msw = sum(sum((v - sum(x) / len(x)) ** 2 for v in x) for x in g) / (N - m)
    msb = sum(len(x) * (sum(x) / len(x) - gm) ** 2 for x in g) / (m - 1)
    n0 = (N - sum(len(x) ** 2 for x in g) / N) / (m - 1)
    den = msb + (n0 - 1) * msw
    return (max(0.0, (msb - msw) / den) if den > 0 else 0.0), m, N


def dersimonian_laird(items):
    ys = [(math.atanh(min(max(v, 0.001), 0.999)), 1 / max(m - 3, 1)) for _, v, m, _ in items]
    y = [a for a, _ in ys]; v = [b for _, b in ys]; w = [1 / x for x in v]
    fe = sum(a * b for a, b in zip(y, w)) / sum(w)
    Q = sum(wi * (yi - fe) ** 2 for wi, yi in zip(w, y))
    dfree = len(y) - 1
    C = sum(w) - sum(wi ** 2 for wi in w) / sum(w)
    tau = max(0.0, (Q - dfree) / C) if C > 0 else 0.0
    wr = [1 / (x + tau) for x in v]
    pe = sum(a * b for a, b in zip(y, wr)) / sum(wr)
    se = math.sqrt(1 / sum(wr))
    return math.tanh(pe)


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
    ap.add_argument('--cert', required=True)
    ap.add_argument('--root', default=ROOT)
    args = ap.parse_args()

    cert = json.load(open(args.cert, encoding='utf-8'))
    fails = []

    # 1 -- self hash
    claimed = cert.pop('certificate_hash', None)
    got_hash = hashlib.sha256(canon(cert)).hexdigest()
    if got_hash != claimed:
        fails.append(f'certificate hash mismatch: signed {claimed}, content {got_hash}')
    else:
        print(f'hash: OK ({got_hash[:16]}...)')
    cert['certificate_hash'] = claimed

    rel = cert['input']['release']
    pub = os.path.join(args.root, 'public', rel)
    if not os.path.isdir(pub):
        sys.exit(f'FAIL: release not found at {pub}')

    # 2 -- input bytes
    for name, want in cert['input']['file_sha256'].items():
        p = os.path.join(pub, name)
        if not os.path.isfile(p):
            fails.append(f'input missing: {name}')
            continue
        got = sha256(p)
        if got != want:
            fails.append(f'input changed: {name} (signed {want[:16]}..., now {got[:16]}...)')
    if not fails:
        print(f'inputs: {len(cert["input"]["file_sha256"])} files match signed hashes')

    # 3 -- recompute
    rows = list(csv.DictReader(open(os.path.join(pub, 'attempts.csv'), encoding='utf-8')))
    got_strata = {}
    for name, bench, rule, scene, fam in STRATA:
        sub = [r for r in rows if r['benchmark'] == bench and (scene is None or r['scene'] == scene)]
        groups = collections.defaultdict(list)
        for r in sub:
            groups[(r['model'], r['task'])].append(outcome_value(r, rule))
        rho, m, N = icc(list(groups.values()))
        got_strata[name] = (rho, m, N, fam)
    merged = {}
    for fam in ('perf', 'att'):
        items = [(n, v[0], v[1], v[2]) for n, v in got_strata.items() if v[3] == fam]
        merged[fam] = dersimonian_laird(items)

    tol = cert['verification']['tolerance']
    A = {a['id']: a for a in cert['assertions']}
    checks = [
        ('C1.1', merged['perf']),
        ('C1.2', merged['att']),
    ]
    for aid, val in checks:
        if abs(A[aid]['value'] - val) > tol:
            fails.append(f'{aid} {A[aid]["quantity"]}: cert {A[aid]["value"]} vs recomputed {val:.4f}')
        else:
            print(f'  {aid} {A[aid]["quantity"]}: {val:.4f} OK')

    fam = 'perf' if cert['claim']['scope'].find('完成族') >= 0 else 'att'
    got_cells = sum(v[1] for v in got_strata.values() if v[3] == fam)
    got_trials = sum(v[2] for v in got_strata.values() if v[3] == fam)
    pair = 'C1.3' if fam == 'perf' else 'C1.4'
    if A[pair]['value']['cells'] != got_cells or A[pair]['value']['attempts'] != got_trials:
        fails.append(f'{pair} counts: cert {A[pair]["value"]} vs recomputed {got_cells}/{got_trials}')
    else:
        print(f'  {pair} cells/trials: {got_cells}/{got_trials} OK')

    # 4 -- resolution
    des = cert['resolution']['design']
    deff = 1 + (des['attempts_per_cell'] - 1) * des['rho']
    n_eff_cell = des['attempts_per_cell'] / deff
    n_eff_model = des['cells_per_model'] * n_eff_cell
    z = 1.959963985 if abs(cert['resolution']['alpha'] - 0.05) < 1e-9 else None
    if z is None:
        fails.append('unsupported alpha in certificate; verifier implements 0.05 only')
    else:
        delta = z * math.sqrt(2 * 0.5 * 0.5 / n_eff_model)
        if abs(delta - cert['resolution']['delta_star']) > 0.001:
            fails.append(f'delta*: cert {cert["resolution"]["delta_star"]} vs recomputed {delta:.4f}')
        else:
            print(f'  delta*: {delta:.4f} ({delta*100:.1f} pp) OK   deff {deff:.3f}  n_eff/cell {n_eff_cell:.3f}')

    if fails:
        print('\nFAIL')
        for f in fails:
            print('  - ' + f)
        sys.exit(1)
    print('\nPASS: the certificate is valid for these bytes.')


if __name__ == '__main__':
    main()
