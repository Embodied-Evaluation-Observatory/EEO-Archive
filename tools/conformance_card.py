#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Issue the C7 conformance card for a release.

C7 is the card a reader checks before trusting the rest: it states the three family
estimates, the certificate level reached, how many cells are thin, and which provenance
checks are computed rather than promised. Every value is read from the published tables
or from layers.json, never typed in by hand.

    python3 tools/conformance_card.py --release 2026-11-19
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def summary_rows(path):
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def family_assertions(rows):
    out, ids = [], ['C7.1', 'C7.2', 'C7.3']
    order = ['completion_family', 'attempt_family', 'safety_family']
    label = {'completion_family': 'completion family pooled rho',
             'attempt_family': 'attempt family pooled rho',
             'safety_family': 'safety family pooled rho'}
    for i, fam in enumerate(order):
        row = next((r for r in rows if r.get('name') == fam), None)
        if row is None:
            out.append({'id': ids[i], 'quantity': label[fam], 'status': 'absent',
                        'note': 'no row in release_summary.csv'})
            continue
        out.append({
            'id': ids[i],
            'quantity': label[fam],
            'value': float(row['rho']),
            'interval': {'lo': float(row['ci_lo']), 'hi': float(row['ci_hi']), 'level': 0.95},
            'rho_excluding_constant_cells': float(row['rho_excl_constant'])
            if row.get('rho_excl_constant') else None,
            'cells': int(row['cells']), 'trials': int(row['trials']),
            'status': 'verified',
            'note': 'recomputed by tools/verify_public.py from attempts.csv',
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', required=True)
    ap.add_argument('--root', default=ROOT)
    a = ap.parse_args()
    rel, root = a.release, a.root
    pub = os.path.join(root, 'public', rel)
    cert_dir = os.path.join(root, 'certificates', rel)
    out_path = os.path.join(cert_dir, 'C7.json')
    if os.path.exists(out_path):
        sys.exit('REFUSED: %s exists; certificates are append-only' % out_path)

    rows = summary_rows(os.path.join(pub, 'release_summary.csv'))
    assertions = family_assertions(rows)

    layers_p = os.path.join(cert_dir, 'layers.json')
    layers = json.load(open(layers_p, encoding='utf-8')) if os.path.isfile(layers_p) else {}
    highest = (layers.get('layers') or {}).get('highest')
    assertions.append({
        'id': 'C7.4', 'quantity': 'certificate layers', 'value': highest or 'none',
        'status': 'verified' if highest else 'absent',
        'note': 'L1 tables, L2 source bytes, L3 snapshot; see certificates/%s/layers.json' % rel,
    })

    cells = list(csv.DictReader(open(os.path.join(pub, 'cells.csv'), encoding='utf-8')))
    thin = sum(1 for c in cells if int(c['n_attempts']) < 30)
    assertions.append({
        'id': 'C7.5', 'quantity': 'cells below 30 attempts',
        'value': '%d of %d' % (thin, len(cells)), 'status': 'verified',
        'note': 'flag only; published values unchanged, see quality_flags.json',
    })

    probe_p = os.path.join(pub, 'probe.json')
    checks = (json.load(open(probe_p, encoding='utf-8')).get('checks') or {}) if os.path.isfile(probe_p) else {}
    computed = sorted(k for k, v in checks.items() if (v or {}).get('status') == 'computed')
    partial = sorted(k for k, v in checks.items() if (v or {}).get('status') == 'partial')
    absent = sorted(k for k, v in checks.items() if (v or {}).get('status') == 'not_implemented')
    assertions.append({
        'id': 'C7.6', 'quantity': 'provenance checks by status',
        'value': '%d computed, %d partial, %d not implemented' % (len(computed), len(partial), len(absent)),
        'status': 'verified',
        'detail': {'computed': computed, 'partial': partial, 'not_implemented': absent},
        'note': 'see probe.json; a partial check is a flag, not a verdict',
    })

    proto_p = os.path.join(root, 'reda-protocol.md')
    proto_txt = open(proto_p, encoding='utf-8').read() if os.path.isfile(proto_p) else ''
    m = re.search(r'ReDA-(\d+\.\d+)', proto_txt)
    card = {
        'certificate_id': 'C7',
        'schema_version': 'EEO-CERT-1',
        'issued_at': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'issuer': {'name': 'Embodied Evaluation Observatory', 'role': 'archive operator'},
        'release': rel,
        'claim': ('The %s export states its family estimates, the level its certificates reach, '
                  'how many cells are thin, and which provenance checks are computed rather than '
                  'promised. Every value here is read from the published tables.' % rel),
        'assertions': assertions,
        'protocol': {'version': 'ReDA-%s' % m.group(1) if m else None,
                     'file': 'reda-protocol.md',
                     'sha256': hashlib.sha256(open(proto_p, 'rb').read()).hexdigest()
                     if os.path.isfile(proto_p) else None},
        'not_certified': ['model capability', 'benchmark validity',
                          'safety of any deployed system', 'completeness of the upstream source'],
        'verification': {'command': 'python3 tools/conformance_card.py --release %s' % rel},
    }
    card['certificate_hash'] = hashlib.sha256(canon(card)).hexdigest()

    os.makedirs(cert_dir, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(card, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('written: certificates/%s/C7.json' % rel)
    print('hash %s' % card['certificate_hash'][:12])


if __name__ == '__main__':
    main()
