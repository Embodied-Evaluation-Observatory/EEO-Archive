#!/usr/bin/env python3
"""Write findings/stratification_<release>.md from the published tables.

  python3 tools/layers_report.py --release 2026-11-19 --root .
"""
import argparse
import collections
import csv
import json
import os

FIELDS = ('grading_method', 'source_tag', 'effort', 'mode')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', required=True)
    ap.add_argument('--root', default='.')
    a = ap.parse_args()
    pub = os.path.join(a.root, 'public', a.release)
    cells = list(csv.DictReader(open(os.path.join(pub, 'cells.csv'), encoding='utf-8')))
    bykey = list(csv.DictReader(open(os.path.join(pub, 'by_key.csv'), encoding='utf-8')))
    frontier = list(csv.DictReader(open(os.path.join(pub, 'frontier.csv'), encoding='utf-8')))
    probe = json.load(open(os.path.join(pub, 'probe.json'), encoding='utf-8'))
    att = list(csv.DictReader(open(os.path.join(pub, 'attempts.csv'), encoding='utf-8')))

    split = collections.defaultdict(set)
    for r in bykey:
        split[(r['stratum'], r['model'], r['task'], r['scene'])].add(
            tuple(r[f] for f in FIELDS))
    per = collections.defaultdict(list)
    for (s, _m, _t, _sc), keys in split.items():
        per[s].append(len(keys))
    canon = {r['stratum']: float(r['stratum_rho']) for r in cells}
    key_rho = {r['stratum']: float(r['stratum_rho_by_key']) for r in bykey}

    md = ['# Comparability key and stratification, release %s' % a.release, '',
          'The cell key is `model + task + scene`. Where a cell also varies on '
          '`grading_method`, `source_tag`, `effort` or `mode`, the split is published in '
          '`by_key.csv` but the headline estimate stays pooled: most split keys hold one or '
          'two attempts and an ICC over them is unstable.', '',
          '| Stratum | cells | full keys | cells split by the four fields | rho (cell key) | rho (full key) |',
          '|---|---|---|---|---|---|']
    for s in sorted(per, key=lambda x: (-len(per[x]), x)):
        k = per[s]
        n = len(k) if not isinstance(k, int) else k
        md.append('| %s | %d | %d | %d (%.0f%%) | %.4f | %.4f |'
                  % (s, n, sum(k), sum(1 for x in k if x > 1),
                     100 * sum(1 for x in k if x > 1) / n, canon.get(s, 0), key_rho.get(s, 0)))

    md += ['', 'Field composition of attempts (top levels):', '',
           '| Field | levels | most frequent |', '|---|---|---|']
    for f in FIELDS:
        comp = collections.Counter((x[f] or 'blank') for x in att).most_common(6)
        md.append('| %s | %d | %s |' % (f, len({(x[f] or 'blank') for x in att}),
                                        ', '.join('%s (%d)' % (k, v) for k, v in comp)))

    zero = [c for c in cells if float(c['p_hat']) == 0.0]
    one = [c for c in cells if float(c['p_hat']) == 1.0]
    mid = len(cells) - len(zero) - len(one)
    md += ['', '## Zero-capability frontier', '',
           '%d cells sit at 0%% with at least 30 attempts (%d at 0%% overall, %d in between, '
           '%d at 100%%). Every recorded attempt failed, so they are boundaries rather than '
           'noise, and they carry no information about correlation. `frontier.csv` lists them.'
           % (len(frontier), len(zero), mid, len(one)), '',
           'Zero by benchmark: %s.'
           % json.dumps(dict(collections.Counter(c['benchmark'] for c in frontier)), ensure_ascii=False),
           '', '## Provenance probe', '']
    for k, v in probe['checks'].items():
        extra = {x: y for x, y in v.items() if x not in ('status', 'note')}
        md.append('- `%s` — %s%s' % (k, v['status'],
                                     ('; ' + json.dumps(extra, ensure_ascii=False)) if extra else ''))

    md += ['', 'Not implemented: reset-cost accounting and a held-out contamination probe. '
               '`attempts.csv` carries no reset timing, and the archive has no probe task of '
               'its own.', '']
    out = os.path.join(a.root, 'findings', 'stratification_%s.md' % a.release)
    open(out, 'w', encoding='utf-8').write('\n'.join(md))
    print('written: %s' % out)


if __name__ == '__main__':
    main()
