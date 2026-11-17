#!/usr/bin/env python3
"""Ingest EvalLog records into a frozen release snapshot.

Reads JSONL where each line follows schema/eval_log_min.schema.json, checks the
required fields, and writes a release directory (snapshot + manifest) that
export_public.py accepts unchanged. This is the entry point for benchmarks that
want their next release to be auditable from birth.

    python3 tools/ingest_evallog.py --log run.jsonl --release 2026-02-01 --root tests/fixture
"""
import argparse, hashlib, json, os, sys
from datetime import datetime, timezone

REQUIRED = ['attempt_id', 'benchmark', 'model', 'task', 'trial', 'outcome',
            'seed', 'init_state_digest', 'termination_cause', 'operator_mode']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', required=True)
    ap.add_argument('--release', required=True)
    ap.add_argument('--root', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument('--archive', default='EEO Archive')
    a = ap.parse_args()

    rows, bad = [], []
    with open(a.log, encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception as e:
                bad.append((i, 'not json: %s' % e))
                continue
            missing = [k for k in REQUIRED if r.get(k) in (None, '')]
            if missing:
                bad.append((i, 'missing %s' % ','.join(missing)))
                continue
            rows.append(r)
    if bad:
        for i, why in bad[:20]:
            print('line %d: %s' % (i, why), file=sys.stderr)
        sys.exit('REFUSED: %d malformed records; nothing written' % len(bad))
    if not rows:
        sys.exit('REFUSED: no records')

    models = sorted({r['model'] for r in rows})
    snap = {
        'cohort_date': a.release,
        'models': {m: m for m in models},
        'runs': [{
            'id': r['attempt_id'],
            'run': r['attempt_id'],
            'benchmark': r['benchmark'],
            'model': r['model'],
            'task': r['task'],
            'trial': r['trial'],
            'seed': r.get('seed'),
            'init_state_digest': r.get('init_state_digest'),
            'termination_cause': r.get('termination_cause'),
            'outcome': r['outcome'],
            'score': r.get('score'),
            'mode': r.get('operator_mode'),
            'control': r.get('operator_mode'),
            'rig_id': r.get('rig_id'),
            'embodiment': r.get('embodiment'),
            'date': r.get('started_at'),
            'log': r.get('log_uri'),
            'videos': ['x'] * int(r.get('video_count') or 0),
            'steps': r.get('steps'),
            'calls': r.get('llm_calls'),
            'cost': r.get('cost_usd'),
            'source': 'evallog',
            'grading': 'declared',
            'replacement': False,
            'rerun': False
        } for r in rows]
    }
    rel_dir = os.path.join(a.root, 'releases', a.release)
    os.makedirs(rel_dir, exist_ok=True)
    path = os.path.join(rel_dir, 'robocurve_allruns.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(snap, f, ensure_ascii=False, indent=1, sort_keys=True)
    raw = open(path, 'rb').read()
    manifest = {
        'archive': a.archive, 'release': a.release,
        'frozen_at_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'),
        'source_note': 'eval log ingest: %s' % os.path.basename(a.log),
        'files': [{'file': 'robocurve_allruns.json', 'bytes': len(raw),
                   'sha256': hashlib.sha256(raw).hexdigest(),
                   'record_count': len(rows), 'count_key': 'runs',
                   'shape': 'dict:cohort_date,models,runs'}],
        'note': 'Records carry seed, initial-state digest and termination cause; '
                'these are the fields a replay needs.'
    }
    json.dump(manifest, open(os.path.join(rel_dir, 'manifest.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print('ingested %d records -> releases/%s/ (sha256 %s)'
          % (len(rows), a.release, manifest['files'][0]['sha256'][:16]))


if __name__ == '__main__':
    main()
