#!/usr/bin/env python3
"""Sensitivity of the pooled estimates.

Two questions the release does not answer:

  - what happens to rho if the constant-outcome cells are dropped rather than pooled?
  - what is each stratum's own uncertainty, not only the family's?

Stratum definitions mirror tools/export_public.py, so the re-baselined numbers reproduce
the published ones before any exclusion. The family estimate is the DerSimonian-Laird
merge over strata, as in the export; it is not a pooled ICC.

  python3 tools/sensitivity.py --release 2026-11-17 --reps 1000
"""

import argparse
import collections
import csv
import importlib.util
import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

spec = importlib.util.spec_from_file_location('export_public',
                                              os.path.join(ROOT, 'tools', 'export_public.py'))
ep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ep)

SCENES = ('unaltered', 'blurred', 'doctored')


def strata_defs():
    d = [('RoboDojo-RC task success', 'robodojo-rc-tier-1', ep.SUCC, None, 'perf'),
         ('Simple-tasks task success', 'simple-tasks', ep.SUCC, None, 'perf'),
         ('RoboHarm unsafe execution', 'roboharm-v1', ep.UNSAFE, None, 'safety'),
         ('RoboHarm safe refusal', 'roboharm-v1', ep.REFUSE, None, 'safety')]
    for s in SCENES:
        d.append(('RoboSpoof attempt (%s)' % s, 'robospoof', ep.ATT, s, 'att'))
    d.append(('RoboHarm attempt', 'roboharm-v1', ep.ATT, None, 'att'))
    return d


def groups(rows, bench, fn, sub):
    g = collections.defaultdict(list)
    for r in rows:
        if r['benchmark'] != bench:
            continue
        if sub is not None and r['scene'] != sub:
            continue
        v = fn(r)
        if v is not None:
            g[(r['model'], r['task'], r['scene'])].append(v)
    return dict(g)


def boot(g, reps, seed):
    if len(g) < 2:
        return None
    keys = list(g.keys())
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        pick = [keys[rng.randrange(len(keys))] for _ in keys]
        vals.append(ep.icc([g[k] for k in pick])[0])
    vals.sort()
    return [round(vals[int(0.025 * reps)], 4), round(vals[int(0.975 * reps) - 1], 4)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', default='2026-11-17')
    ap.add_argument('--reps', type=int, default=1000)
    ap.add_argument('--root', default=ROOT)
    a = ap.parse_args()

    pub = os.path.join(a.root, 'public', a.release)
    att = list(csv.DictReader(open(os.path.join(pub, 'attempts.csv'), encoding='utf-8')))
    cells = list(csv.DictReader(open(os.path.join(pub, 'cells.csv'), encoding='utf-8')))

    strata, families = {}, collections.defaultdict(list)
    for name, bench, fn, sub, fam in strata_defs():
        g = groups(att, bench, fn, sub)
        if len(g) < 2:
            continue
        rho, m, N, _ = ep.icc(list(g.values()))
        zv = {k for k, v in g.items() if sum(v) in (0, len(v))}
        keep = {k: v for k, v in g.items() if k not in zv}
        d = {'family': fam, 'rho': round(rho, 4), 'cells': m, 'attempts': N,
             'ci': boot(g, a.reps, abs(hash(name)) % 9999),
             'zero_variance_cells': len(zv),
             'rho_excluding_zero_variance': round(ep.icc(list(keep.values()))[0], 4)
                                          if len(keep) >= 2 else None,
             'ci_excluding_zero_variance': boot(keep, a.reps, abs(hash(name)) % 9999 + 1)
                                          if len(keep) >= 2 else None,
             'deff_cluster_J20': round(1 + (19 - 1) * rho, 3),
             'deff_naive': 1.0,
             'ci_width_ratio_cluster_vs_naive': round((1 + 18 * rho) ** 0.5, 3),
             'note': ('rho is the one-way ANOVA ICC(1); "naive" ignores clustering entirely, '
                      '"cluster" uses 1+(J-1)*rho at J=20')}
        strata[name] = d
        families[fam].append((name, d['rho'], m, N))

    fam_rows = {}
    for fam, items in families.items():
        rho_with, lo, hi, Q, I2, tau = ep.dersimonian_laird(items)
        kept = [(n, strata[n]['rho_excluding_zero_variance'], m, N) for n, _, m, N in items
                if strata[n]['rho_excluding_zero_variance'] is not None]
        rho_ex = ep.dersimonian_laird(kept)[0] if len(kept) >= 2 else (kept[0][1] if kept else None)
        fam_rows[fam] = {'family_rho': round(rho_with, 4), 'ci': [round(lo, 4), round(hi, 4)],
                         'I2': round(I2, 4), 'tau': round(tau, 4), 'strata': len(items),
                         'family_rho_excluding_zero_variance': round(rho_ex, 4)
                         if rho_ex is not None else None,
                         'strata_kept_after_exclusion': len(kept)}

    n_all = [c for c in cells if float(c['p_hat']) == 0.0]
    n_one = [c for c in cells if float(c['p_hat']) == 1.0]
    frontier = {
        'cells_at_zero_percent': len(n_all),
        'cells_between': len(cells) - len(n_all) - len(n_one),
        'cells_at_hundred_percent': len(n_one),
        'zero_by_benchmark': dict(collections.Counter(c['benchmark'] for c in n_all)),
        'zero_with_30_plus_attempts': len([c for c in n_all if int(c['n_attempts']) >= 30]),
        'reading': ('A 0% cell is a capability boundary, not noise: every recorded attempt '
                    'failed. Such a cell says nothing about correlation, so it is dropped in '
                    'the sensitivity column and kept in the published one. Whether that boundary '
                    'is the policy or the harness is a question this release cannot answer.'),
    }

    out = {'release': a.release,
           'bootstrap': {'unit': 'cell within stratum', 'reps': a.reps,
                         'interval': 'percentile 2.5-97.5'},
           'strata': strata, 'families': fam_rows, 'frontier': frontier,
           'note': ('Sensitivity only. release_summary.csv is unchanged. These numbers say what '
                    'the estimates would be under a different inclusion rule, not what they are.')}

    with open(os.path.join(a.root, 'findings', 'sensitivity_%s.json' % a.release), 'w',
              encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print('%-28s %6s %6s %18s %5s' % ('stratum', 'rho', 'excl', 'CI', 'cells'))
    for n, d in strata.items():
        excl = '%.3f' % d['rho_excluding_zero_variance'] \
            if d['rho_excluding_zero_variance'] is not None else '—'
        print('%-28s %6.3f %6s %18s %5d' % (n, d['rho'], excl, d['ci'], d['cells']))
    print('families:', json.dumps(fam_rows, ensure_ascii=False))
    print('frontier:', frontier['cells_at_zero_percent'], 'zero /',
          frontier['cells_between'], 'between /', frontier['cells_at_hundred_percent'], 'one')
    print('written: findings/sensitivity_%s.json' % a.release)


if __name__ == '__main__':
    main()
