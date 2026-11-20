#!/usr/bin/env python3
"""Comparability-keyed cells, the zero-capability frontier, and a contamination probe.

Three things the canonical tables do not carry:

  by_key.csv     one row per cell keyed on benchmark+model+task+scene+grading_method+
                 mode+effort+source_tag, so a cell that mixes grading regimes is split
                 rather than averaged
  frontier.csv   cells with zero successes and at least 30 attempts: a capability
                 boundary, not evidence about correlation
  probe.json     five provenance checks on the published attempts, each labelled
                 computed / partial / not implemented

  python3 tools/layers.py --release 2026-11-19
  python3 tools/layers.py --release 2026-11-19 --root /tmp/candidate
"""

import argparse
import collections
import csv
import importlib.util
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

spec = importlib.util.spec_from_file_location('export_public',
                                              os.path.join(ROOT, 'tools', 'export_public.py'))
ep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ep)

KEY_FIELDS = ('benchmark', 'model', 'task', 'scene', 'grading_method', 'mode',
              'effort', 'source_tag')
FRONTIER_MIN = 30


def strata_defs():
    d = [('RoboDojo-RC task success', 'robodojo-rc-tier-1', ep.SUCC, None, 'perf'),
         ('Simple-tasks task success', 'simple-tasks', ep.SUCC, None, 'perf'),
         ('RoboHarm unsafe execution', 'roboharm-v1', ep.UNSAFE, None, 'safety'),
         ('RoboHarm safe refusal', 'roboharm-v1', ep.REFUSE, None, 'safety')]
    for s in ('unaltered', 'blurred', 'doctored'):
        d.append(('RoboSpoof attempt (%s)' % s, 'robospoof', ep.ATT, s, 'att'))
    d.append(('RoboHarm attempt', 'roboharm-v1', ep.ATT, None, 'att'))
    return d


def key_of(row):
    return tuple((row.get(f) or '') for f in KEY_FIELDS)


def stratum_rows(attempts, name, bench, rule, scene):
    out = []
    for r in attempts:
        if r['benchmark'] != bench:
            continue
        if scene is not None and r['scene'] != scene:
            continue
        v = rule(r)
        if v is None:
            continue
        out.append((r, v))
    return out


def build_by_key(attempts):
    rows = []
    for name, bench, rule, scene, fam in strata_defs():
        sub = stratum_rows(attempts, name, bench, rule, scene)
        if len(sub) < 2:
            continue
        groups = collections.defaultdict(list)
        run_rows = collections.defaultdict(list)
        for r, v in sub:
            groups[key_of(r)].append(v)
            run_rows[key_of(r)].append(r)
        if len(groups) < 2:
            continue
        rho = round(ep.icc(list(groups.values()))[0], 4)
        for k, vals in sorted(groups.items()):
            r0 = run_rows[k][0]
            rows.append({
                'stratum': name, 'family': fam, 'benchmark': k[0], 'model': k[1],
                'model_display': r0.get('model_display', k[1]), 'task': k[2], 'scene': k[3],
                'grading_method': k[4], 'mode': k[5], 'effort': k[6], 'source_tag': k[7],
                'n_attempts': len(vals), 'n_success': int(sum(vals)),
                'p_hat': round(sum(vals) / len(vals), 4),
                'n_keys_in_stratum': len(groups), 'stratum_rho_by_key': rho,
            })
    return rows


def build_frontier(attempts):
    rows = []
    for name, bench, rule, scene, fam in strata_defs():
        sub = stratum_rows(attempts, name, bench, rule, scene)
        groups = collections.defaultdict(list)
        run_rows = collections.defaultdict(list)
        for r, v in sub:
            k = (r['model'], r['task'], r['scene'])
            groups[k].append(v)
            run_rows[k].append(r)
        for k, vals in sorted(groups.items()):
            if len(vals) < FRONTIER_MIN or sum(vals) != 0:
                continue
            rows.append({
                'stratum': name, 'family': fam, 'benchmark': bench, 'model': k[0],
                'model_display': run_rows[k][0].get('model_display', k[0]),
                'task': k[1], 'scene': k[2] or '', 'n_attempts': len(vals),
                'upper_95_finite': round(1 - 0.05 ** (1 / len(vals)), 4),
            })
    return rows


def probe(attempts):
    n = len(attempts)
    # 1. exact duplicate records (trial id excluded)
    sig = collections.Counter(tuple(sorted((k, v) for k, v in r.items() if k != 'trial'))
                              for r in attempts)
    dup = sum(c - 1 for c in sig.values() if c > 1)
    # 2. identical outcome vectors across different models in one task
    vecs = collections.defaultdict(list)
    for r in attempts:
        v = ep.ATT(r)
        if v is not None:
            vecs[(r['benchmark'], r['task'], r['scene'], r['model'])].append((r['trial'], v))
    by_task = collections.defaultdict(dict)
    for (b, t, s, m), items in vecs.items():
        if len(items) >= 5:
            by_task[(b, t, s)][m] = tuple(v for _, v in sorted(items, key=lambda x: str(x[0])))
    identical_pairs = 0
    for cell, models in by_task.items():
        seqs = collections.defaultdict(list)
        for m, seq in models.items():
            seqs[seq].append(m)
        for seq, ms in seqs.items():
            if len(ms) > 1:
                identical_pairs += len(ms) * (len(ms) - 1) // 2
    # 3. temporal clustering
    minute = collections.Counter((r['benchmark'], r['date_utc'][:16]) for r in attempts)
    top_per_bench = {}
    for (b, _), c in minute.items():
        top_per_bench[b] = max(top_per_bench.get(b, 0), c)
    top_single = max(minute.values()) if minute else 0
    # 4. share concentration
    share = {}
    for b in {r['benchmark'] for r in attempts}:
        tot = sum(1 for r in attempts if r['benchmark'] == b)
        top = collections.Counter(r['model'] for r in attempts if r['benchmark'] == b).most_common(1)
        share[b] = {'trials': tot, 'top_model_share': round(top[0][1] / tot, 4) if tot else None}
    # 5. score/outcome conflict
    conflict = 0
    for r in attempts:
        try:
            s = float(r['score'])
        except (TypeError, ValueError):
            continue
        if r['outcome'] == 'success' and s < 0.5:
            conflict += 1
        elif r['outcome'] in ('fail', 'failure') and s >= 0.5:
            conflict += 1
    return {
        'attempts': n,
        'checks': {
            'duplicate_records': {'status': 'computed', 'duplicates': dup,
                                  'rate': round(dup / n, 4) if n else None},
            'identical_outcome_vectors': {'status': 'partial', 'pairs': identical_pairs,
                                          'note': ('identical sequences across models in one '
                                                   'task suggest shared records; they also '
                                                   'occur naturally in deterministic '
                                                   'sandboxes, so this is a flag, not a verdict')},
            'temporal_clustering': {'status': 'partial', 'max_per_minute': top_single,
                                    'max_per_benchmark': top_per_bench,
                                    'note': 'no test against a submission schedule is available'},
            'share_concentration': {'status': 'computed', 'by_benchmark': share},
            'score_outcome_conflict': {'status': 'computed', 'conflicts': conflict},
            'reset_cost': {'status': 'not_implemented',
                           'note': 'attempts.csv carries no reset timing or reset count'},
            'contamination_probe': {'status': 'not_implemented',
                                    'note': ('no held-out probe task exists in this archive, '
                                             'so contamination cannot be measured here')},
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', required=True)
    ap.add_argument('--root', default=ROOT)
    args = ap.parse_args()

    pub = os.path.join(args.root, 'public', args.release)
    attempts = list(csv.DictReader(open(os.path.join(pub, 'attempts.csv'), encoding='utf-8')))
    by_key = build_by_key(attempts)
    frontier = build_frontier(attempts)
    p = probe(attempts)

    with open(os.path.join(pub, 'by_key.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(by_key[0].keys()) if by_key else list(KEY_FIELDS))
        w.writeheader()
        w.writerows(by_key)
    with open(os.path.join(pub, 'frontier.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(frontier[0].keys()) if frontier else
                           ['stratum', 'benchmark', 'model', 'task'])
        w.writeheader()
        w.writerows(frontier)
    with open(os.path.join(pub, 'probe.json'), 'w', encoding='utf-8') as f:
        json.dump({'release': args.release, **p}, f, ensure_ascii=False, indent=1)

    print('by_key: %d rows, %d strata' % (len(by_key), len({r['stratum'] for r in by_key})))
    print('frontier: %d cells at 0%% with >=%d attempts' % (len(frontier), FRONTIER_MIN))
    print('probe: duplicates=%d identical_pairs=%d conflicts=%d max_per_minute=%d'
          % (p['checks']['duplicate_records']['duplicates'],
             p['checks']['identical_outcome_vectors']['pairs'],
             p['checks']['score_outcome_conflict']['conflicts'],
             p['checks']['temporal_clustering']['max_per_minute']))


if __name__ == '__main__':
    main()
