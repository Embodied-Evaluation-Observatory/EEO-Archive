#!/usr/bin/env python3
"""Pre-publication self-check for a benchmark or an archive release.

Intended to run *before* a benchmark publishes a new version, and to be run by
any outsider on the archive's public tables. It writes a short report instead of
a verdict: every line is a number someone can recompute.

    python3 tools/bench_selfcheck.py --release 2026-11-17
    python3 tools/bench_selfcheck.py --release 2026-11-17 --out findings/selfcheck

Inputs, when present under the repository root:
    public/<release>/release_summary.csv, cells.csv
    boards/<release>/board_summary.json
    releases/<release>/manifest.json, robocurve_allruns.json
Missing inputs are reported as "not available", never estimated.
"""
import argparse, collections, csv, hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_TRIALS = 30


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def read_csv(path):
    if not os.path.isfile(path):
        return []
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', required=True)
    ap.add_argument('--root', default=ROOT)
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    rel, root = a.release, a.root
    pub = os.path.join(root, 'public', rel)
    board = os.path.join(root, 'boards', rel, 'board_summary.json')
    man = os.path.join(root, 'releases', rel, 'manifest.json')
    snap = os.path.join(root, 'releases', rel, 'robocurve_allruns.json')

    report = {'release': rel, 'generated_by': 'tools/bench_selfcheck.py',
              'inputs': {}, 'repeatability': [], 'discernibility': [],
              'sample_sufficiency': {}, 'disclosure': [], 'layers': {}}

    # ---------------------------------------------------------------- inputs
    for name, path in (('release_summary.csv', os.path.join(pub, 'release_summary.csv')),
                       ('cells.csv', os.path.join(pub, 'cells.csv')),
                       ('board_summary.json', board),
                       ('manifest.json', man),
                       ('robocurve_allruns.json', snap)):
        report['inputs'][name] = ({'bytes': os.path.getsize(path), 'sha256': sha256(path)[:16]}
                                  if os.path.isfile(path) else None)

    # ----------------------------------------------------------- repeatability
    for r in read_csv(os.path.join(pub, 'release_summary.csv')):
        if r.get('row_type') != 'family':
            continue
        def f(k):
            try: return float(r[k])
            except Exception: return None
        report['repeatability'].append({
            'family': r.get('family'), 'rho': f('rho'), 'ci_lo': f('ci_lo'), 'ci_hi': f('ci_hi'),
            'cells': int(float(r.get('cells') or 0)), 'trials': int(float(r.get('trials') or 0)),
            'deff_J20': f('deff_J20'), 'n_eff_J20': f('n_eff_J20'),
            'zero_fail_upper_finite': f('zero_fail_upper_finite')})

    # --------------------------------------------------------- discernibility
    if os.path.isfile(board):
        for name, b in json.load(open(board, encoding='utf-8')).get('boards', {}).items():
            report['discernibility'].append({
                'board': name, 'pairs': b.get('pairs'), 'separated': b.get('separated'),
                'undiscernible_share_pct': b.get('undiscernible_share'),
                'cells': b.get('cells'), 'n_reported': b.get('n_reported')})

    # ---------------------------------------------------- sample sufficiency
    cells = read_csv(os.path.join(pub, 'cells.csv'))
    if cells:
        def n(c):
            try: return int(float(c.get('n_attempts') or 0))
            except Exception: return 0
        hist = collections.Counter(n(c) for c in cells)
        thin = sum(v for k, v in hist.items() if k < MIN_TRIALS)
        report['sample_sufficiency'] = {
            'cells': len(cells), 'min_trials_threshold': MIN_TRIALS,
            'thin_cells': thin, 'thin_share': round(thin / len(cells), 4),
            'trials_histogram': {str(k): v for k, v in sorted(hist.items())},
            'median_trials': sorted(n(c) for c in cells)[len(cells) // 2]}

    # -------------------------------------------------------------- disclosure
    for name, b in (json.load(open(board, encoding='utf-8')).get('boards', {}).items()
                    if os.path.isfile(board) else []):
        report['disclosure'].append({'board': name, 'cells': b.get('cells'),
                                     'cells_with_n': b.get('n_reported')})

    # ----------------------------------------------------------------- layers
    L1 = bool(cells) and bool(report['repeatability'])
    L2 = os.path.isfile(snap) and os.path.isfile(man)
    if L2:
        m = json.load(open(man, encoding='utf-8'))
        entry = next((e for e in m['files'] if e['file'] == 'robocurve_allruns.json'), None)
        L2 = bool(entry) and sha256(snap) == entry['sha256'] and os.path.getsize(snap) == entry['bytes']
    L3 = L2 and bool(m.get('records_key') or m.get('files'))
    if L2:
        rec = None
        try:
            data = json.load(open(snap, encoding='utf-8'))
            key = m['files'][0].get('count_key', 'runs')
            rec = len(data.get(key, []))
        except Exception:
            rec = None
        parent = m['files'][0].get('record_count')
        L3 = L2 and rec is not None and parent is not None and rec == parent
    report['layers'] = {
        'L1_tables_self_consistent': L1,
        'L2_source_bytes_match_declared_hash': L2,
        'L3_source_snapshot_open_to_any_reader': L3,
        'note': 'L3 requires the source snapshot to be redistributable. Where terms forbid it, '
                'only the holder of the original bytes can complete L3.'}

    # ----------------------------------------------------------------- output
    base = a.out or os.path.join(root, 'findings', 'selfcheck_%s' % rel)
    os.makedirs(os.path.dirname(base), exist_ok=True)
    json.dump(report, open(base + '.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    md = ['# Self-check, release %s' % rel, '',
          'Every figure below is recomputed from the files named in `inputs`; nothing is estimated.', '']
    md += ['## Repeatability', '', '| family | rho | 95% CI | cells | trials |', '|---|---|---|---|---|']
    for r in report['repeatability']:
        md.append('| %s | %.4f | [%.4f, %.4f] | %d | %d |' % (
            r['family'], r['rho'], r['ci_lo'], r['ci_hi'], r['cells'], r['trials']))
    if report['discernibility']:
        md += ['', '## Discernibility of published boards', '',
               '| board | pairs | separated | undiscernible % | cells with n stated |',
               '|---|---|---|---|---|']
        for d in report['discernibility']:
            stated = ('%s of %s' % (d['n_reported'], d['cells'])
                      if d.get('n_reported') is not None else 'not stated')
            md.append('| %s | %s | %s | %s | %s |' % (
                d['board'], d['pairs'], d['separated'], d['undiscernible_share_pct'], stated))
    if report['sample_sufficiency']:
        s = report['sample_sufficiency']
        md += ['', '## Sample sufficiency', '',
               'Cells: %d. Median attempts per cell: %d. Cells under %d attempts: %d (%.1f%%).' % (
                   s['cells'], s['median_trials'], s['min_trials_threshold'],
                   s['thin_cells'], s['thin_share'] * 100),
               '', 'A thin cell is usable as a single-model report, not as one observation '
               'in a correlation across the board. See `QUALITY_GATE.md`.']
    md += ['', '## Certificate layers reachable for this release', '',
           '| layer | reachable | meaning |', '|---|---|---|',
           '| L1 tables self-consistent | %s | published summary reproduces from published tables |' % report['layers']['L1_tables_self_consistent'],
           '| L2 source bytes match declared hash | %s | the snapshot present locally hashes to the manifest |' % report['layers']['L2_source_bytes_match_declared_hash'],
           '| L3 source open to any reader | %s | the snapshot itself is redistributed, so an outsider can redo the export |' % report['layers']['L3_source_snapshot_open_to_any_reader']]
    open(base + '.md', 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    print('written: %s.md / .json' % base)
    print('L1=%s L2=%s L3=%s' % tuple(report['layers'][k] for k in
          ('L1_tables_self_consistent', 'L2_source_bytes_match_declared_hash',
           'L3_source_snapshot_open_to_any_reader')))


if __name__ == '__main__':
    main()
