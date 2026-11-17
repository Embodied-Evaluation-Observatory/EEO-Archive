#!/usr/bin/env python3
"""Provenance card: run the submission checks that the published data allows.

Protocol section 5 lists five checks. Three can be computed from what boards
publish; two cannot, and say so. Output is a card with a number per row, never a
deletion.

    python3 tools/provenance_check.py --snapshot 2026-11-17
"""
import argparse, collections, csv, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_cells(path):
    return list(csv.DictReader(open(path, encoding='utf-8'))) if os.path.isfile(path) else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--snapshot', required=True)
    ap.add_argument('--root', default=ROOT)
    a = ap.parse_args()
    base = os.path.join(a.root, 'boards', a.snapshot)
    card = {'snapshot': a.snapshot, 'checks': [], 'note': 'flags only; nothing is deleted'}

    # ---- 1. share concentration (top models' share of trials / cells)
    tw = load_cells(os.path.join(base, 'robotwin_cells.csv'))
    if tw:
        trials = collections.Counter()
        for r in tw:
            try: trials[r['model']] += int(float(r['n'] or 0))
            except Exception: pass
        total = sum(trials.values()) or 1
        top3 = sum(v for _, v in trials.most_common(3))
        card['checks'].append({'check': 'share concentration', 'status': 'computed',
                               'board': 'robotwin', 'models': len(trials),
                               'top3_share_of_trials': round(top3 / total, 3),
                               'reading': 'high share means the board is dominated by few sources; '
                                          'it does not by itself indicate gaming'})
    # ---- 2. temporal clustering (RoboChallenge publishes submission timestamps)
    rc = load_cells(os.path.join(base, 'robochallenge_cells.csv'))
    stamps = []
    for r in rc:
        try:
            extra = json.loads(r.get('extra') or '{}')
            if extra.get('submitted'):
                stamps.append(((r['model'], r['task']), extra['submitted'][:16]))
        except Exception:
            pass
    if stamps:
        per_model = {}
        for (model, task), ts in stamps:
            per_model.setdefault(model, set()).add(ts)
        hours = collections.Counter(ts[:13] for _, ts in stamps)
        busiest_hour, busiest_n = (hours.most_common(1)[0] if hours else ('', 0))
        same_instant = sum(v - 1 for v in collections.Counter(ts for _, ts in stamps).values() if v > 1)
        card['checks'].append({'check': 'temporal clustering', 'status': 'computed',
                               'board': 'robochallenge', 'cells_with_timestamp': len(stamps),
                               'busiest_hour_utc': busiest_hour, 'cells_in_busiest_hour': busiest_n,
                               'cells_sharing_minute_with_another': same_instant,
                               'reading': 'batch submission in a short window is a flag, not a verdict; '
                                          'a single sweep of a benchmark produces the same pattern'})
    else:
        card['checks'].append({'check': 'temporal clustering', 'status': 'not computable',
                               'reason': 'no submission timestamps in the ingested data'})

    # ---- 3. pairwise consistency (a source beating everyone on every task)
    if tw:
        cells = collections.defaultdict(dict)
        for r in tw:
            try: cells[(r['task'], r['embodiment'])][r['model']] = float(r['value'])
            except Exception: pass
        models = sorted({r['model'] for r in tw})
        flags = []
        for i, x in enumerate(models):
            for y in models[i + 1:]:
                shared = [k for k in cells if x in cells[k] and y in cells[k]]
                if len(shared) < 20:
                    continue
                wins = sum(1 for k in shared if cells[k][x] > cells[k][y])
                if wins in (0, len(shared)):
                    flags.append({'model_a': x, 'model_b': y, 'shared_tasks': len(shared),
                                  'wins_a': wins})
        card['checks'].append({'check': 'pairwise consistency', 'status': 'computed',
                               'board': 'robotwin', 'pairs_with_shared_tasks': '>=20 tasks',
                               'fully_consistent_pairs': len(flags), 'examples': flags[:10],
                               'reading': 'perfect consistency across many tasks is suspicious only '
                                          'when the tasks are heterogeneous; check task families before reading it'})
    # ---- 4 / 5. cannot be computed
    card['checks'].append({'check': 'selective submission', 'status': 'partial',
                           'reason': 'submitted-vs-retained counts are published for RoboChallenge '
                                     '(32,980 benchmark episodes against 769 leaderboard cells) but '
                                     'attempt counts per cell are unstated, so the retention ratio '
                                     'cannot be normalised',
                           'robochallenge_episodes_per_cell': round(32980 / 769, 1)})
    card['checks'].append({'check': 'contamination probe', 'status': 'not implemented',
                           'reason': 'no perturbed task variant has been run; a probe without a '
                                     'positive control would produce an uninterpretable number'})

    out = os.path.join(a.root, 'findings', 'provenance_%s' % a.snapshot)
    json.dump(card, open(out + '.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    md = ['# Provenance card, %s' % a.snapshot, '',
          'Three of the five checks in protocol section 5 can be computed from published data; '
          'two cannot, and are marked as such.', '']
    for c in card['checks']:
        md.append('## %s — %s' % (c['check'], c['status']))
        md.append('')
        for k, v in c.items():
            if k in ('check', 'status'):
                continue
            md.append('- %s: %s' % (k, v))
        md.append('')
    open(out + '.md', 'w', encoding='utf-8').write('\n'.join(md))
    print('written: findings/provenance_%s.md / .json' % a.snapshot)
    for c in card['checks']:
        print('  %-24s %s' % (c['check'], c['status']))


if __name__ == '__main__':
    main()
