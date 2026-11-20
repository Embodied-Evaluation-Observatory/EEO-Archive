#!/usr/bin/env python3
"""Comparability audit.

The audit so far treats a benchmark cell as one observation with one success rate.
It is not: attempts inside a cell can come from different grading methods, different
inference efforts and modes, and different source tags. Those differences are sources
of variance that ReDA pools without saying so.

This script measures how often that happens in the published release, and defines the
comparability key that a stricter table would have to keep apart.

  python3 tools/comparability.py --release 2026-11-17

Writes findings/comparability_<release>.json and .md.
"""

import argparse
import collections
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = ['grading_method', 'source_tag', 'effort', 'mode']


def load(release):
    pub = os.path.join(ROOT, 'public', release)
    att = list(csv.DictReader(open(os.path.join(pub, 'attempts.csv'), encoding='utf-8')))
    cells = list(csv.DictReader(open(os.path.join(pub, 'cells.csv'), encoding='utf-8')))
    return att, cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', default='2026-11-17')
    a = ap.parse_args()

    att, cells = load(a.release)
    key = lambda r: (r['benchmark'], r['model'], r['task'], r['scene'])

    by_cell = collections.defaultdict(list)
    for r in att:
        by_cell[key(r)].append(r)

    # Population is the published cell table; attempts define what each cell mixes.
    rows_in_table = [(c['benchmark'], c['model'], c['task'], c['scene']) for c in cells]
    pub_cells = list(dict.fromkeys(rows_in_table))   # one cell per model-task-scene

    per_field = {}
    for f in FIELDS:
        mixed = [c for c in pub_cells if len({r[f] for r in by_cell.get(c, [])}) > 1]
        per_field[f] = {
            'mixed_cells': len(mixed),
            'share_cells': round(len(mixed) / len(pub_cells), 3),
            'distinct_values': len({r[f] for r in att}),
            'dominant': collections.Counter(r[f] for r in att).most_common(3),
        }

    mixed_any = [c for c in pub_cells
                 if any(len({r[f] for r in by_cell.get(c, [])}) > 1 for f in FIELDS)]
    att_in_mixed = sum(len(by_cell.get(c, [])) for c in mixed_any)

    # Comparability key: a cell is comparable only inside the same tuple.
    cell_keys = {c: tuple(sorted({(r['grading_method'], r['mode'], r['effort'], r['source_tag'])
                                  for r in rows})) for c, rows in by_cell.items()}
    keys_per_stratum = collections.defaultdict(set)
    for c, ks in cell_keys.items():
        keys_per_stratum[(c[0],)].update(ks)
    multi_key_strata = {b[0]: len(ks) for b, ks in keys_per_stratum.items() if len(ks) > 1}

    out = {
        'release': a.release,
        'cells': len(pub_cells),
        'cell_rows_in_table': len(rows_in_table),
        'cells_with_attempts': len([c for c in pub_cells if by_cell.get(c)]),
        'attempts': len(att),
        'fields': FIELDS,
        'per_field': per_field,
        'mixed_cells_any_field': len(mixed_any),
        'share_mixed_cells': round(len(mixed_any) / len(pub_cells), 3),
        'attempts_in_mixed_cells': att_in_mixed,
        'share_attempts_in_mixed_cells': round(att_in_mixed / len(att), 3),
        'benchmarks_with_multiple_keys': multi_key_strata,
        'comparability_key': 'benchmark + grading_method + mode + effort + source_tag',
        'reading': ('A cell marked mixed pools attempts whose grading or inference conditions '
                    'differ. Its success rate is still a rate, but its variance mixes capability '
                    'with procedure. The key says what a stricter table would keep apart.'),
    }

    path = os.path.join(ROOT, 'findings', 'comparability_%s.json' % a.release)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    md = ['# Comparability audit, %s' % a.release, '',
          'Cells hold attempts that can differ in how they were graded and under what inference '
          'conditions. ReDA pools them; this records how often.', '',
          '| Field | Distinct values | Mixed cells | Share of cells |', '|---|---|---|---|']
    for f in FIELDS:
        d = per_field[f]
        md.append('| `%s` | %d | %d | %d%% |' % (f, d['distinct_values'], d['mixed_cells'],
                                                 round(100 * d['share_cells'])))
    md += ['', 'Cells mixed on at least one field: **%d of %d** (%d%%); attempts inside them: '
           '**%d of %d** (%d%%).' % (len(mixed_any), len(pub_cells),
                                     round(100 * len(mixed_any) / len(pub_cells)),
                                     att_in_mixed, len(att),
                                     round(100 * att_in_mixed / len(att))), '',
           '## Comparability key', '',
           '`%s`' % out['comparability_key'], '',
           'Benchmarks whose cells span more than one key:', '']
    for b, n in sorted(multi_key_strata.items()):
        md.append('- %s: %d distinct keys' % (b, n))
    md += ['', '## Limit', '',
           'A mixed cell is not wrong; it is unlabelled. The rate it publishes is a weighted '
           'average over procedures, and the audit cannot say which procedure produced the '
           'variance. Splitting these cells would shrink the cell count further, which is why '
           'they are flagged rather than removed.']
    with open(os.path.join(ROOT, 'findings', 'comparability_%s.md' % a.release), 'w',
              encoding='utf-8') as f:
        f.write('\n'.join(md) + '\n')

    print(json.dumps({k: out[k] for k in ('cells', 'mixed_cells_any_field', 'share_mixed_cells',
                                          'share_attempts_in_mixed_cells')}, ensure_ascii=False))
    print('written: findings/comparability_%s.{json,md}' % a.release)


if __name__ == '__main__':
    main()
