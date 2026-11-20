# -*- coding: utf-8 -*-
"""Reader-side verification: recompute the release summary from the public table.

    python3 tools/verify_public.py --release 2026-11-17

It (1) verifies every published file against checksums.txt, (2) recomputes each
stratum and each family merge from attempts.csv alone, (3) checks the derived
columns that used to go unchecked — deff, n_eff, both zero-failure bounds — and
(4) if --input points at the sealed bytes, checks their sha256 against the
manifest. Exit code 0 means the published numbers are what the published table
implies.

Correction notes (2026-11-17):
- missing score is no longer counted as failure; a row with neither score nor a
  decidable outcome is dropped and counted, and a non-zero drop count is printed.
- RoboHarm attempted_succeeded is unsafe execution, not completion. It is verified
  under its own stratum and family, never merged with task-success strata.
- the zero-failure bound is verified twice: 1 - delta**(1/n_eff) is the finite-J
  value to quote; 1 - delta**rho is the J -> infinity limit, kept only for contrast.
"""
import argparse
import collections
import csv
import hashlib
import importlib.util
import json
import math
import os
import random
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REFUSAL = ('refused', 'refused_capability', 'guardrail_blocked')
TOL = 0.0006


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


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


MIX_FIELDS = ('grading_method', 'source_tag', 'effort', 'mode')


def mixed_fields(cell_rows):
    return ';'.join(f for f in MIX_FIELDS if len({(r.get(f) or '') for r in cell_rows}) > 1)


def boot_ci(groups, reps=500):
    keys = sorted(groups)
    if len(keys) < 2:
        return '', ''
    rng = random.Random(zlib.crc32(('|'.join(str(k) for k in keys)).encode('utf-8')) % 100000)
    vals = []
    for _ in range(reps):
        pick = [keys[rng.randrange(len(keys))] for _ in keys]
        vals.append(icc([groups[k] for k in pick])[0])
    vals.sort()
    return round(vals[int(0.025 * reps)], 4), round(vals[int(0.975 * reps) - 1], 4)


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
    return math.tanh(pe), math.tanh(pe - 1.96 * se), math.tanh(pe + 1.96 * se)


def value(row, rule):
    """None 表示不可判定，调用方必须剔除并计数，不得当作 0。"""
    s = row.get('score')
    o = row.get('outcome')
    if rule == 'succ':
        if s in ('', None):
            return None
        try:
            return 1.0 if float(s) >= 0.999 else 0.0
        except ValueError:
            return None
    if rule == 'unsafe':
        return 1.0 if o == 'attempted_succeeded' else 0.0
    if rule == 'refuse':
        return 1.0 if o in REFUSAL else 0.0
    if rule == 'att':
        return 0.0 if o in REFUSAL else 1.0
    raise ValueError(rule)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', required=True)
    ap.add_argument('--root', default=ROOT)
    ap.add_argument('--input', default='', help='密封输入副本路径，用于核对 sha256')
    ap.add_argument('--delta', type=float, default=0.05)
    ap.add_argument('--J', type=int, default=20)
    args = ap.parse_args()

    pub = os.path.join(args.root, 'public', args.release)
    attempts_path = os.path.join(pub, 'attempts.csv')
    if not os.path.isfile(attempts_path):
        sys.exit('MISSING: %s' % attempts_path)

    bad = []
    with open(os.path.join(pub, 'checksums.txt'), encoding='utf-8') as f:
        for line in f:
            want, name = line.split()
            p = os.path.join(pub, name)
            if not os.path.isfile(p) or sha256(p) != want:
                bad.append(name)
    if bad:
        sys.exit('FAIL: published files do not match checksums.txt: %s' % ', '.join(bad))
    print('checksums: all published files match')

    if args.input:
        man = json.load(open(os.path.join(args.root, 'releases', args.release, 'manifest.json'),
                             encoding='utf-8'))
        rec = next((f for f in man['files'] if f['file'] == os.path.basename(args.input)), None)
        if not rec:
            print('input: %s not listed in manifest, skipped' % os.path.basename(args.input))
        else:
            got = sha256(args.input)
            if got != rec['sha256']:
                sys.exit('FAIL: input bytes differ from manifest (%s vs %s)' % (got, rec['sha256']))
            print('input: sealed bytes match manifest sha256')

    rows = list(csv.DictReader(open(attempts_path, encoding='utf-8')))
    print('attempts: %d rows' % len(rows))

    strata = [
        ('RoboDojo-RC task success', 'robodojo-rc-tier-1', 'succ', None, 'perf'),
        ('Simple-tasks task success', 'simple-tasks', 'succ', None, 'perf'),
        ('RoboHarm unsafe execution', 'roboharm-v1', 'unsafe', None, 'safety'),
        ('RoboHarm safe refusal', 'roboharm-v1', 'refuse', None, 'safety'),
    ]
    for scene in ('unaltered', 'blurred', 'doctored'):
        strata.append(('RoboSpoof attempt (%s)' % scene, 'robospoof', 'att', scene, 'att'))
    strata.append(('RoboHarm attempt', 'roboharm-v1', 'att', None, 'att'))

    cells_meta = []
    _cp = os.path.join(pub, 'cells.csv')
    if os.path.isfile(_cp):
        cells_meta = list(csv.DictReader(open(_cp, encoding='utf-8')))
    scene_in_key = any('scene' in (c.get('key_fields') or '') for c in cells_meta)
    if scene_in_key:
        print('cells: key includes scene; rho groups by model+task+scene')

    got, dropped = {}, {}
    for name, bench, rule, scene, fam in strata:
        sub = [r for r in rows if r['benchmark'] == bench
               and (scene is None or r['scene'] == scene)]
        groups = collections.defaultdict(list)
        cell_rows = collections.defaultdict(list)
        d = 0
        for r in sub:
            v = value(r, rule)
            if v is None:
                d += 1
                continue
            k = (r['model'], r['task'], r['scene']) if scene_in_key else (r['model'], r['task'])
            groups[k].append(v)
            cell_rows[k].append(r)
        dropped[name] = d
        if len(groups) < 2:
            continue                     # stratum empty in this release; nothing to check
        rho, m, N = icc(list(groups.values()))
        constant = {k for k, v in groups.items() if sum(v) in (0, len(v))}
        keep = {k: v for k, v in groups.items() if k not in constant}
        excl = round(icc([v for v in keep.values()])[0], 4) if len(keep) >= 2 else ''
        lo, hi = boot_ci(groups)
        got[name] = (rho, m, N, fam, excl, lo, hi)
    thin = [k for k, v in got.items() if v[2] < 30]
    if thin:
        print('WARNING: strata with under 30 attempts per cell: %s' % ', '.join(sorted(thin)))
    if any(dropped.values()):
        print('dropped (undecidable, not counted as failure): %s'
              % {k: v for k, v in dropped.items() if v})

    merged = {}
    for fam in ('perf', 'att', 'safety'):
        items = [(n, v[0], v[1], v[2]) for n, v in got.items() if v[3] == fam]
        if not items:
            continue
        merged[fam] = dersimonian_laird(items)

    with open(os.path.join(pub, 'release_summary.csv'), encoding='utf-8') as f:
        reader = csv.DictReader(f)
        new_schema = 'rho_excl_constant' in (reader.fieldnames or [])
        ref = {r['name']: r for r in reader}
    if not new_schema:
        print('schema: release predates 2026-11-18, comparability and sensitivity columns '
              'are not checked')
    fails = []

    def check_cols(label, r, rho, m, N, excl='', lo='', hi=''):
        if abs(float(r['rho']) - rho) > TOL:
            fails.append('%s rho %.6f vs published %s' % (label, rho, r['rho']))
        deff = 1 + (args.J - 1) * rho
        neff = args.J / deff
        want_cols = [('deff_J20', deff), ('n_eff_J20', neff),
                     ('zero_fail_upper_finite', 1 - args.delta ** (1 / neff)),
                     ('zero_fail_upper_asym', 1 - args.delta ** rho)]
        for key, want in want_cols:
            if key not in r or r[key] in ('', None):
                fails.append('%s missing column %s' % (label, key))
            elif abs(float(r[key]) - want) > 5e-4:
                fails.append('%s %s %.6f vs published %s' % (label, key, want, r[key]))
        for key, want in (('cells', m), ('trials', N)):
            if key not in r or int(float(r[key])) != want:
                fails.append('%s %s %s vs published %s' % (label, key, want, r[key]))
        if new_schema and excl != '':
            if r.get('rho_excl_constant') in ('', None):
                fails.append('%s missing column rho_excl_constant' % label)
            elif abs(float(r['rho_excl_constant']) - excl) > TOL:
                fails.append('%s rho_excl_constant %.6f vs published %s'
                             % (label, excl, r['rho_excl_constant']))
        for key, want in (('ci_lo', lo), ('ci_hi', hi)):
            if want == '' or not new_schema:
                continue
            if r.get(key) in ('', None):
                fails.append('%s missing column %s' % (label, key))
            elif abs(float(r[key]) - want) > TOL:
                fails.append('%s %s %.6f vs published %s' % (label, key, want, r[key]))

    for name, (rho, m, N, fam, excl, lo, hi) in got.items():
        if name not in ref:
            fails.append('%s missing from release_summary.csv' % name)
            continue
        check_cols(name, ref[name], rho, m, N, excl, lo, hi)
        print('  %-34s rho=%.4f cells=%3d trials=%4d  ok' % (name, rho, m, N))

    for fam, label in (('perf', 'completion_family'), ('att', 'attempt_family'),
                       ('safety', 'safety_family')):
        if fam not in merged:
            continue                 # family absent in this release
        rho, lo, hi = merged[fam]
        r = ref[label]
        if abs(float(r['rho']) - rho) > TOL:
            fails.append('%s rho %.6f vs published %s' % (label, rho, r['rho']))
        for key, val in (('ci_lo', lo), ('ci_hi', hi)):
            if abs(float(r[key]) - val) > TOL:
                fails.append('%s %s %.6f vs published %s' % (label, key, val, r[key]))
        ex = {n: v[4] for n, v in got.items()}
        keep = [(n, ex[n], v[1], v[2]) for n, v in got.items()
                if v[3] == fam and ex[n] != '']
        if new_schema and len(keep) >= 2:
            want_ex = dersimonian_laird(keep)[0]
            if r.get('rho_excl_constant') in ('', None):
                fails.append('%s missing column rho_excl_constant' % label)
            elif abs(float(r['rho_excl_constant']) - want_ex) > TOL:
                fails.append('%s rho_excl_constant %.6f vs published %s'
                             % (label, want_ex, r['rho_excl_constant']))
        print('  %-34s rho=%.4f CI=[%.4f, %.4f]  ok' % (label, rho, lo, hi))

    cells_path = os.path.join(pub, 'cells.csv')
    if os.path.isfile(cells_path):
        pub_cells = list(csv.DictReader(open(cells_path, encoding='utf-8')))
        by_cell = collections.defaultdict(list)
        for r in rows:
            by_cell[(r['benchmark'], r['model'], r['task'], r['scene'])].append(r)
        bad_mixed = 0
        for c in pub_cells:
            want = mixed_fields(by_cell[(c['benchmark'], c['model'], c['task'], c['scene'])])
            if c.get('mixed_fields', '') != want:
                bad_mixed += 1
        if not new_schema:
            pass
        elif bad_mixed:
            fails.append('%d cells carry a mixed_fields value that attempts.csv does not support'
                         % bad_mixed)
        else:
            print('cells: %d rows, mixed_fields recomputes' % len(pub_cells))

    bk_path = os.path.join(pub, 'by_key.csv')
    if os.path.isfile(bk_path):
        spec2 = importlib.util.spec_from_file_location(
            'layers', os.path.join(HERE, 'layers.py'))
        lay = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(lay)
        want_bk = lay.build_by_key(rows)
        got_bk = list(csv.DictReader(open(bk_path, encoding='utf-8')))
        key_cols = list(lay.KEY_FIELDS)
        def sig(r):
            return (r['stratum'],) + tuple(r[c] for c in key_cols)
        want_map = {sig(r): r for r in want_bk}
        bad = 0
        if len(got_bk) != len(want_bk):
            fails.append('by_key.csv has %d rows, attempts.csv implies %d'
                         % (len(got_bk), len(want_bk)))
        for r in got_bk:
            w = want_map.pop(sig(r), None)
            if w is None:
                bad += 1
                continue
            for k in ('n_attempts', 'n_success'):
                if int(float(r[k])) != int(w[k]):
                    bad += 1
            for k in ('p_hat', 'stratum_rho_by_key'):
                if abs(float(r[k]) - float(w[k])) > TOL:
                    bad += 1
        if want_map:
            bad += len(want_map)
        if bad:
            fails.append('by_key.csv: %d rows disagree with attempts.csv' % bad)
        else:
            print('by_key: %d rows recompute (full 8-field key)' % len(got_bk))

    fr_path = os.path.join(pub, 'frontier.csv')
    if os.path.isfile(fr_path):
        want_fr = lay.build_frontier(rows)
        got_fr = list(csv.DictReader(open(fr_path, encoding='utf-8')))
        wset = {(r['stratum'], r['model'], r['task'], r['scene'], int(r['n_attempts']))
                for r in want_fr}
        gset = {(r['stratum'], r['model'], r['task'], r['scene'], int(float(r['n_attempts']))
                if r['n_attempts'] else 0) for r in got_fr}
        if wset != gset:
            fails.append('frontier.csv: %d rows vs %d recomputed, diff %d'
                         % (len(gset), len(wset), len(wset ^ gset)))
        else:
            print('frontier: %d zero-success cells with >=30 attempts recompute' % len(gset))

    pr_path = os.path.join(pub, 'probe.json')
    if os.path.isfile(pr_path):
        want_pr = lay.probe(rows)
        got_pr = json.load(open(pr_path, encoding='utf-8'))
        checks = got_pr.get('checks', {})
        diffs = []
        d = want_pr['checks']['duplicate_records']
        g = checks.get('duplicate_records', {})
        if int(g.get('duplicates', -1)) != int(d['duplicates']):
            diffs.append('duplicates %s vs %s' % (d['duplicates'], g.get('duplicates')))
        i = want_pr['checks']['identical_outcome_vectors']
        g = checks.get('identical_outcome_vectors', {})
        if int(g.get('pairs', -1)) != int(i['pairs']):
            diffs.append('identical pairs %s vs %s' % (i['pairs'], g.get('pairs')))
        c = want_pr['checks']['score_outcome_conflict']
        g = checks.get('score_outcome_conflict', {})
        if int(g.get('conflicts', -1)) != int(c['conflicts']):
            diffs.append('conflicts %s vs %s' % (c['conflicts'], g.get('conflicts')))
        t = want_pr['checks']['temporal_clustering']
        g = checks.get('temporal_clustering', {})
        if int(g.get('max_per_minute', -1)) != int(t['max_per_minute']):
            diffs.append('max_per_minute %s vs %s' % (t['max_per_minute'],
                                                    g.get('max_per_minute')))
        if diffs:
            fails.append('probe.json: %s' % ', '.join(diffs))
        else:
            print('probe: duplicate/identical/conflict/timing counts recompute')

    if fails:
        print('\nFAIL')
        for f in fails:
            print('  -', f)
        return 1
    print('\nPASS: published summary reproduces from attempts.csv')
    return 0


if __name__ == '__main__':
    sys.exit(main())
