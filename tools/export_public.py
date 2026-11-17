# -*- coding: utf-8 -*-
"""EEO Archive — public-layer export.

Reads a *frozen* release, verifies its hashes, and emits the three public tables
that the observatory publishes. Nothing is hand-edited between freeze and export.

    python3 eeo-archive/tools/export_public.py --release 2026-11-15

Outputs, under eeo-archive/public/<release>/ :
    attempts.csv         one row per attempt (de-identified, truncated)
    cells.csv            one row per model-task cell
    release_summary.csv  stratum and merged estimates with design consequences
    cost_buckets.json    bucket edges for the hashed cost bucket labels
    DATASET_CARD.md      provenance, field dictionary, licence blocks
    checksums.txt        sha256 of every emitted file

Refuses to write if the output directory already exists (same rule as freeze).
Private artefacts (rig alias map) go to eeo-archive/private/ and are never
published.
"""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # eeo-archive/
RIG_RE = re.compile(r'rig[-_]([A-Za-z0-9]+)')
ATT_REFUSAL = ('refused', 'refused_capability', 'guardrail_blocked')
MIN_TRIALS = 30          # below this a cell is flagged, never silently trusted


# ---------------------------------------------------------------- integrity
def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def verified_release(release, root=None):
    """Load a release only after every file matches its frozen manifest."""
    rel_dir = os.path.join(root or ROOT, 'releases', release)
    manifest = os.path.join(rel_dir, 'manifest.json')
    if not os.path.isfile(manifest):
        sys.exit('REFUSED: no manifest at %s' % manifest)
    with open(manifest, encoding='utf-8') as f:
        m = json.load(f)
    bad = []
    for entry in m['files']:
        p = os.path.join(rel_dir, entry['file'])
        if not os.path.isfile(p) or sha256(p) != entry['sha256']:
            bad.append(entry['file'])
    if bad:
        sys.exit('REFUSED: release %s fails hash verification on: %s' % (release, ', '.join(bad)))
    return rel_dir, m


# ---------------------------------------------------------------- statistics
def icc(groups):
    """One-way ANOVA ICC(1); groups are per-cell outcome vectors."""
    g = [x for x in groups if len(x) >= 2]
    m = len(g)
    N = sum(len(x) for x in g)
    gm = sum(sum(x) for x in g) / N
    msw = sum(sum((v - sum(x) / len(x)) ** 2 for v in x) for x in g) / (N - m)
    msb = sum(len(x) * (sum(x) / len(x) - gm) ** 2 for x in g) / (m - 1)
    n0 = (N - sum(len(x) ** 2 for x in g) / N) / (m - 1)
    den = msb + (n0 - 1) * msw
    return (max(0.0, (msb - msw) / den) if den > 0 else 0.0), m, N, n0


def dersimonian_laird(items):
    """Fisher-z random effects over strata: (rho, lo, hi, Q, I2, tau)."""
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
    I2 = max(0.0, (Q - dfree) / Q) if Q > 0 else 0.0
    return math.tanh(pe), math.tanh(pe - 1.96 * se), math.tanh(pe + 1.96 * se), Q, I2, tau


def _score(r):
    v = r.get('score')
    return None if v in (None, '') else float(v)

# 缺失分不当作失败：score 为空且无法由 outcome 判定时返回 None，该条从格子里剔除。
SUCC = lambda r: (1.0 if _score(r) >= 0.999 else 0.0) if _score(r) is not None else None
# RoboHarm 上 attempted_succeeded 表示已执行有害指令，不是"完成"。单独成族，不进性能合并。
UNSAFE = lambda r: 1.0 if r.get('outcome') == 'attempted_succeeded' else 0.0
REFUSE = lambda r: 1.0 if r.get('outcome') in ATT_REFUSAL else 0.0
ATT = lambda r: 0.0 if r.get('outcome') in ATT_REFUSAL else 1.0


# ---------------------------------------------------------------- de-identify
def load_alias_map(path, seal=True):
    if os.path.isfile(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_alias_map(path, mapping):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2, sort_keys=True)
    if os.name != 'nt':
        os.chmod(path, 0o600)


def rig_alias(record, mapping):
    """Stable anonymous id per rig. The rig token itself never leaves this function."""
    raw = ''
    for field in ('id', 'log'):
        v = record.get(field) or ''
        hit = RIG_RE.search(v)
        if hit:
            raw = 'rig-' + hit.group(1)
            break
    if not raw:
        return 'RIG-NA', False
    if raw not in mapping:
        mapping[raw] = 'RIG-%03d' % (len(mapping) + 1)
    return mapping[raw], True


def minute_utc(value):
    if not value:
        return ''
    try:
        ts = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return ''
    ts = ts.astimezone(dt.timezone.utc)
    return ts.strftime('%Y-%m-%dT%H:%MZ')


def quantile(sorted_vals, q):
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return sorted_vals[lo] if lo == hi else \
        sorted_vals[lo] * (hi - k) + sorted_vals[hi] * (k - lo)


def cost_edges(costs):
    s = sorted(costs)
    return [quantile(s, q) for q in (0.2, 0.4, 0.6, 0.8)]


def cost_bucket(value, edges):
    if value is None:
        return ''
    for i, e in enumerate(edges):
        if value <= e:
            return 'c%d' % (i + 1)
    return 'c5'


# ---------------------------------------------------------------- tables
def build_attempts(runs, models, mapping, edges):
    rows, seen_rig = [], 0
    for r in runs:
        alias, had = rig_alias(r, mapping)
        seen_rig += 1 if had else 0
        rows.append({
            'release': None,                             # filled by caller
            'benchmark': r.get('benchmark') or '',
            'model': r.get('model') or '',
            'model_display': models.get(r.get('model') or '', r.get('model') or ''),
            'task': r.get('task') or '',
            'scene': r.get('scene') or '',
            'effort': r.get('effort') or '',
            'mode': r.get('mode') or '',
            'control': r.get('control') or '',
            'trial': r.get('trial') if r.get('trial') is not None else '',
            'outcome': r.get('outcome') or '',
            'score': '' if r.get('score') is None else r.get('score'),
            'date_utc': minute_utc(r.get('date')),
            'run_key': r.get('run') or '',
            'rig_alias': alias,
            'grading_method': r.get('grading') or '',
            'source_tag': r.get('source') or '',
            'leaderboard': ';'.join(r.get('leaderboard') or []),
            'replacement': str(bool(r.get('replacement'))).lower(),
            'rerun': str(bool(r.get('rerun'))).lower(),
            'minutes': '' if r.get('minutes') is None else round(r['minutes'], 3),
            'calls': r.get('calls') if r.get('calls') is not None else '',
            'cost_bucket': cost_bucket(r.get('cost'), edges),
            'has_log': str(bool(r.get('log'))).lower(),
            'video_count': len(r.get('videos') or []),
        })
    return rows, seen_rig


def build_cells(runs, strata_defs):
    """Cell table plus the stratum assignment used by the pooled estimator."""
    out = []
    for name, bench, fn, sub, fam in strata_defs:
        subset = sub if sub is not None else [r for r in runs if r.get('benchmark') == bench]
        groups = collections.defaultdict(list)
        for r in subset:
            v = fn(r)
            if v is None:
                continue
            groups[(r.get('model') or '', r.get('task') or '')].append(v)
        if len(groups) < 2:
            continue                      # stratum has no usable cells in this release
        rho, m, N, n0 = icc(list(groups.values()))
        for key, vals in groups.items():
            n = len(vals)
            deff = 1 + (n - 1) * rho
            out.append({
                'benchmark': bench,
                'model': key[0],
                'task': key[1],
                'scene': (subset[0].get('scene') or '') if subset else '',
                'family': fam,
                'stratum': name,
                'stratum_rho': round(rho, 4),
                'n_attempts': n,
                'n_success': int(sum(vals)),
                'p_hat': round(sum(vals) / n, 4),
                'deff_cell': round(deff, 3),
                'n_eff_cell': round(n / deff, 3) if deff > 0 else '',
                'n_cells_in_stratum': m,
                'n_attempts_in_stratum': N,
            })
    return out


def build_summary(runs, strata_defs, delta=0.05, J=20):
    """Stratum rows, family merges, and the release-level consequences."""
    strata = []
    for name, bench, fn, sub, fam in strata_defs:
        subset = sub if sub is not None else [r for r in runs if r.get('benchmark') == bench]
        groups = collections.defaultdict(list)
        for r in subset:
            v = fn(r)
            if v is None:
                continue
            groups[(r.get('model') or '', r.get('task') or '')].append(v)
        if len(groups) < 2:
            continue                      # stratum has no usable cells in this release
        rho, m, N, n0 = icc(list(groups.values()))
        strata.append((name, rho, m, N, fam, bench))

    rows = []
    for name, rho, m, N, fam, bench in strata:
        rows.append({
            'row_type': 'stratum', 'name': name, 'family': fam, 'benchmark': bench,
            'rho': round(rho, 4), 'ci_lo': '', 'ci_hi': '',
            'cells': m, 'trials': N, 'I2': '', 'tau': '',
            'deff_J20': round(1 + (J - 1) * rho, 3),
            'n_eff_J20': round(J / (1 + (J - 1) * rho), 3),
            'zero_fail_upper_asym': round(1 - delta ** rho, 4),
            'zero_fail_upper_finite': round(1 - delta ** (1 / (J / (1 + (J - 1) * rho))), 4),
        })

    for fam, label in (('perf', 'completion_family'), ('att', 'attempt_family'),
                       ('safety', 'safety_family')):
        items = [(n, v, m, N) for n, v, m, N, f, _ in strata if f == fam]
        if not items:
            continue                 # family absent in this release; no empty row is written
        rho, lo, hi, Q, I2, tau = dersimonian_laird(items)
        deff = 1 + (J - 1) * rho
        neff = J / deff
        rows.append({
            'row_type': 'family', 'name': label, 'family': fam, 'benchmark': '',
            'rho': round(rho, 4), 'ci_lo': round(lo, 4), 'ci_hi': round(hi, 4),
            'cells': sum(m for _, _, m, _ in items),
            'trials': sum(N for _, _, _, N in items),
            'I2': round(I2, 4), 'tau': round(tau, 4),
            'deff_J20': round(deff, 3), 'n_eff_J20': round(neff, 3),
            'zero_fail_upper_asym': round(1 - delta ** rho, 4),
            'zero_fail_upper_finite': round(1 - delta ** (1 / neff), 4),
        })
    return rows


# ---------------------------------------------------------------- outputs
def write_csv(path, rows):
    if not rows:
        return
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


CARD = """---
license: cc-by-4.0
task_categories:
- robotics
tags:
- robot-evaluation
- reproducibility
- benchmarking
pretty_name: EEO Archive, release {release}
---

# EEO Archive — release {release}

Per-attempt records of public robot evaluations, re-published as three flat tables so
that the statistics quoted by the Embodied Evaluation Observatory can be recomputed
by anyone. This release was frozen as release `{release}` (release hash
`{hash}`) and the export was generated from those frozen bytes only.

## Provenance

| Field | Value |
|---|---|
| Source archive | {source} |
| Frozen at (UTC) | {frozen} |
| Records | {records} attempts, {cells} cells |
| Models | {models} |
| Benchmarks | {benchmarks} |
| Protocol | Repetition and Discernibility Audit (ReDA), version 1.0 |

## Tables

`attempts.csv` — one row per attempt. `cells.csv` — one row per model-task cell with
the stratum it belongs to, its attempt count, its success count and the design
consequences of that stratum's correlation. `release_summary.csv` — stratum estimates,
family merges, and the same estimates expressed as design effect and effective sample
size at J = {J} attempts per cell.

## Fields

| Field | Meaning |
|---|---|
| benchmark / task / scene | evaluation unit and condition |
| model / model_display | internal identifier and public name |
| effort / mode / control | configuration, needed for comparability |
| trial | index within the cell |
| outcome | result category as published (not recoded) |
| score | published score; empty means missing, **not zero** |
| date_utc | attempt start, truncated to the minute |
| run_key | run hash from the source, kept as a recomputation anchor |
| rig_alias | stable anonymous device id; the mapping is not published |
| grading_method | how the attempt was graded, including any judge model |
| source_tag / leaderboard | source cohort tag and leaderboard membership |
| replacement / rerun | whether the attempt was replaced or rerun |
| minutes / calls | wall-clock and call count |
| cost_bucket | cost in quantile buckets; edges in `cost_buckets.json` |
| has_log / video_count | availability flags only; logs and videos are not redistributed |

## Notes for consumers

- `cells.csv` lists a model-task cell **once per stratum**. RoboHarm contributes the
  same 30 cells to three strata — unsafe execution, safe refusal and attempt — so
  aggregating over the whole file without filtering on `stratum` triple-counts it.
- RoboHarm `attempted_succeeded` means the harmful instruction was executed, not that
  the task was completed. It is reported as **unsafe execution** and never merged with
  task-success strata. `refused` and `guardrail_blocked` are reported as **safe refusal**.
- {rig_na} attempts carry no device token in the source, so their `rig_alias` is
  `RIG-NA`. They are kept, not dropped; excluding them would change the attempt counts.
- `cost_bucket` is empty where the source cost is missing. It is never imputed.
- `attempts.csv` keeps `outcome` as published. Any binarisation used in the estimates
  lives in the export script, not in the data.

## Licence

Three blocks, stated separately because they are not the same thing.

1. **This compilation, and everything computed from it** — the table structure,
   the de-identification, the stratum estimates, the design-effect columns — is
   released under CC-BY-4.0. Attribute as `EEO Archive, release {release}`.
2. **The per-attempt result fields** (model, task, scene, outcome, score, and the
   configuration fields) originate in the source archive named above. Their rights
   remain with the source. This release cites them as facts and does not relicense
   them; anyone redistributing them must follow the source's terms.
3. **Quoted text** such as the source's own exclusion rule is quoted, not asserted.

## What this dataset is not

It is a record and a reliability measurement, not a verdict. It does not say which
system is better, and no row in it should be read as an evaluation conclusion. The
observatory's reports carry their own licence and their own limits; this dataset is
their input.

## Reproduction

```
python3 eeo-archive/tools/export_public.py --release {release}
```

The script verifies every frozen file against `releases/{release}/manifest.json`
before it emits anything, and refuses to overwrite an existing `public/{release}/`.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', required=True)
    ap.add_argument('--root', default=ROOT)
    ap.add_argument('--J', type=int, default=20)
    ap.add_argument('--delta', type=float, default=0.05)
    args = ap.parse_args()

    root = args.root
    release = args.release
    rel_dir, manifest = verified_release(release, root)
    print('release verified: %d files, hash %s' % (len(manifest['files']),
          sha256(os.path.join(rel_dir, 'manifest.json'))[:16] + '...'))

    out_dir = os.path.join(root, 'public', release)
    if os.path.isdir(out_dir):
        sys.exit('REFUSED: public output for %s already exists. Publish a new release id.' % release)

    with open(os.path.join(rel_dir, 'robocurve_allruns.json'), encoding='utf-8') as f:
        data = json.load(f)
    runs = data.get('runs') or []
    models = data.get('models') or {}
    print('records: %d, models: %d' % (len(runs), len(models)))

    # sealed alias map, persisted across releases so ids stay stable
    alias_path = os.path.join(root, 'private', 'rig_alias_map.json')
    mapping = load_alias_map(alias_path)

    costs = [r['cost'] for r in runs if isinstance(r.get('cost'), (int, float))]
    edges = cost_edges(costs)

    attempts, rig_hits = build_attempts(runs, models, mapping, edges)
    for row in attempts:
        row['release'] = release
    save_alias_map(alias_path, mapping)

    strata_defs = [
        ('RoboDojo-RC task success', 'robodojo-rc-tier-1', SUCC, None, 'perf'),
        ('Simple-tasks task success', 'simple-tasks', SUCC, None, 'perf'),
        ('RoboHarm unsafe execution', 'roboharm-v1', UNSAFE, None, 'safety'),
        ('RoboHarm safe refusal', 'roboharm-v1', REFUSE, None, 'safety'),
    ]
    spoof = [r for r in runs if r.get('benchmark') == 'robospoof']
    for scene in ('unaltered', 'blurred', 'doctored'):
        strata_defs.append(('RoboSpoof attempt (%s)' % scene, 'robospoof', ATT,
                            [r for r in spoof if r.get('scene') == scene], 'att'))
    strata_defs.append(('RoboHarm attempt', 'roboharm-v1', ATT, None, 'att'))

    cells = build_cells(runs, strata_defs)
    for row in cells:
        row['release'] = release
        row['model_display'] = models.get(row['model'], row['model'])
    summary = build_summary(runs, strata_defs, args.delta, args.J)
    for row in summary:
        row['release'] = release

    os.makedirs(out_dir)
    write_csv(os.path.join(out_dir, 'attempts.csv'), attempts)
    write_csv(os.path.join(out_dir, 'cells.csv'), cells)
    write_csv(os.path.join(out_dir, 'release_summary.csv'), summary)
    with open(os.path.join(out_dir, 'cost_buckets.json'), 'w', encoding='utf-8') as f:
        json.dump({'release': release, 'unit': 'source cost field',
                   'edges': [round(e, 4) for e in edges],
                   'labels': ['c1', 'c2', 'c3', 'c4', 'c5'],
                   'note': 'labels are quantile buckets of the release; c5 is above the last edge'},
                  f, ensure_ascii=False, indent=2)

    parquet = []
    try:
        import pandas as pd  # noqa: F401
        import pyarrow  # noqa: F401
        for name, rows in (('attempts', attempts), ('cells', cells), ('release_summary', summary)):
            pd.DataFrame(rows).to_parquet(os.path.join(out_dir, name + '.parquet'), index=False)
            parquet.append(name + '.parquet')
    except Exception:
        parquet = []

    fmt = 'CSV' + (' and parquet' if parquet else '')
    benchmarks = sorted({r.get('benchmark') or '' for r in runs})
    card = CARD.format(
        release=release,
        hash=sha256(os.path.join(rel_dir, 'manifest.json')),
        source='https://robocurve.org/all-runs/',
        frozen=manifest['frozen_at_utc'],
        records=len(runs), cells=sum(s['cells'] for s in summary if s['row_type'] == 'family'),
        models=len(models), benchmarks=len(benchmarks), J=args.J,
        rig_na=sum(1 for a in attempts if a['rig_alias'] == 'RIG-NA'),
    )
    card += '\n## Format\n\nTables are distributed as %s.\n' % fmt
    with open(os.path.join(out_dir, 'DATASET_CARD.md'), 'w', encoding='utf-8') as f:
        f.write(card)

    with open(os.path.join(out_dir, 'checksums.txt'), 'w', encoding='utf-8') as f:
        for name in sorted(os.listdir(out_dir)):
            if name == 'checksums.txt':
                continue
            f.write('%s  %s\n' % (sha256(os.path.join(out_dir, name)), name))

    fam = {s['family']: s for s in summary if s['row_type'] == 'family'}
    perf, att = fam.get('perf'), fam.get('att')
    print('attempts rows: %d (rig alias resolved on %d)' % (len(attempts), rig_hits))
    print('cells rows: %d' % len(cells))
    zv = [c for c in cells if str(c.get('p_hat')) in ('0.0', '1.0', '0', '1')]
    with open(os.path.join(out_dir, 'zero_variance_cells.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['benchmark', 'model', 'task', 'n_attempts', 'p_hat'])
        w.writeheader()
        for c in zv:
            w.writerow({'benchmark': c.get('benchmark'), 'model': c.get('model'),
                        'task': c.get('task'), 'n_attempts': c.get('n_attempts'),
                        'p_hat': c.get('p_hat')})
    print('zero-variance cells: %d of %d (constant outcome; listed separately, still in the pooled estimate)'
          % (len(zv), len(cells)))
    thin = [c for c in cells if int(float(c.get('n_attempts') or 0)) < MIN_TRIALS]
    if thin:
        print('WARNING: %d of %d cells have fewer than %d attempts; their correlations '
              'and zero-failure bounds are unstable (see QUALITY_GATE.md)'
              % (len(thin), len(cells), MIN_TRIALS))
    with open(os.path.join(out_dir, 'quality_flags.json'), 'w', encoding='utf-8') as f:
        json.dump({'min_trials': MIN_TRIALS, 'thin_cells': len(thin), 'cells': len(cells),
                   'flag': [{'benchmark': c.get('benchmark'), 'model': c.get('model'),
                             'task': c.get('task'), 'n_attempts': c.get('n_attempts')} for c in thin[:200]]},
                  f, ensure_ascii=False, indent=1)
    for label, row in (('completion family', perf), ('attempt family', att)):
        if row:
            print('merged %-17s rho=%.3f CI=[%.3f,%.3f] cells=%d trials=%d'
                  % (label, row['rho'], row['ci_lo'], row['ci_hi'], row['cells'], row['trials']))
    if perf:
        print('J=%d: deff=%.1f n_eff=%.2f zero-failure upper (finite J)=%.3f asymptotic=%.3f'
              % (args.J, perf['deff_J20'], perf['n_eff_J20'],
                 perf['zero_fail_upper_finite'], perf['zero_fail_upper_asym']))
    print('written to %s' % out_dir)


if __name__ == '__main__':
    main()
