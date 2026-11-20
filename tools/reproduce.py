#!/usr/bin/env python3
"""Produce a reproduction receipt for one release.

Runs the reader-side verification, hashes the tables it used, and writes a JSON receipt
that a third party can attach to an issue or cite in a paper. The receipt is evidence of
an arithmetic check, not of measurement validity.

  python3 tools/reproduce.py --release 2026-11-17
  python3 tools/reproduce.py --release 2026-11-17 --input releases/2026-11-17/robocurve_allruns.json
  python3 tools/reproduce.py --release 2026-11-17 --name "A. Reviewer" --org "Uni X" --scope arithmetic

Exit code mirrors the verification: 0 pass, 1 fail, 2 cannot run.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL_VERSION = '2026-11-18'
PARTNER_HEADER = ('organisation', 'role', 'release_scope', 'access_route',
                  'scope_of_check', 'agreed_on', 'public_note', 'evidence_link')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def git_head():
    try:
        return subprocess.run(['git', '-C', ROOT, 'rev-parse', 'HEAD'], capture_output=True,
                              text=True, timeout=10).stdout.strip()
    except Exception:
        return ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', required=True)
    ap.add_argument('--input', default='', help='copy of the sealed snapshot, if held')
    ap.add_argument('--out', default='')
    ap.add_argument('--name', default='')
    ap.add_argument('--org', default='')
    ap.add_argument('--scope', default='arithmetic',
                    choices=['arithmetic', 'export', 'deposit'])
    ap.add_argument('--no-consent', action='store_true')
    a = ap.parse_args()

    pub = os.path.join(ROOT, 'public', a.release)
    if not os.path.isdir(pub):
        sys.exit('MISSING: public/%s' % a.release)

    cmd = [sys.executable, os.path.join(ROOT, 'tools', 'verify_public.py'), '--release', a.release]
    if a.input:
        cmd += ['--input', a.input]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    verdict = 'pass' if proc.returncode == 0 else 'fail'

    receipt = {
        'tool': 'tools/reproduce.py',
        'tool_version': TOOL_VERSION,
        'release': a.release,
        'scope': a.scope,
        'checked_at_utc': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),
        'repository_commit': git_head(),
        'environment': {'python': platform.python_version(), 'platform': platform.platform()},
        'inputs': {},
        'result': verdict,
        'output_tail': proc.stdout.strip().splitlines()[-6:],
        'not_checked': ['source record completeness', 'measurement validity of the benchmark',
                        'whether attempts.csv reflects every original evaluation'],
    }
    for name in ('attempts.csv', 'cells.csv', 'release_summary.csv'):
        p = os.path.join(pub, name)
        if os.path.isfile(p):
            receipt['inputs'][name] = sha256(p)
    if a.input and os.path.isfile(a.input):
        receipt['inputs']['snapshot'] = {'file': os.path.basename(a.input),
                                         'sha256': sha256(a.input)}

    if a.name:
        receipt['reproducer'] = {'name': a.name, 'organisation': a.org,
                                 'consent_to_be_named': not a.no_consent}

    out = a.out or os.path.join(ROOT, 'receipts', '%s-%s.json'
                                % (a.release, receipt['checked_at_utc'].replace(':', '')))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(receipt, f, ensure_ascii=False, indent=1)

    print(json.dumps({'result': verdict, 'receipt': out,
                      'tail': receipt['output_tail']}, ensure_ascii=False, indent=1))

    if a.name and not a.no_consent:
        row = {'organisation': a.org or '(not given)', 'role': 'external reproducer',
               'release_scope': a.release, 'access_route': 'public tables' if a.scope == 'arithmetic'
               else ('redistributed snapshot' if a.scope == 'export' else 'sealed bytes'),
               'scope_of_check': a.scope, 'agreed_on': receipt['checked_at_utc'][:10],
               'public_note': 'receipt %s' % os.path.basename(out),
               'evidence_link': ''}
        print('partner row (append after review):')
        print(','.join(row[k] for k in PARTNER_HEADER))

    return 0 if verdict == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
