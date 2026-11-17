#!/usr/bin/env python3
"""Issue a layered certificate for a release.

Layers are independent checks, each recomputable by a reader:

    L1  published tables reproduce from each other (summary from cells/attempts)
    L2  the source bytes present locally hash to the value in the manifest
    L3  the source snapshot is redistributed, so an outsider can redo the export

A release may reach L1 only, L1+L2, or all three. Nothing here certifies
performance or safety; see the `not_certified` field.

    python3 tools/certify.py --release 2026-11-17
"""
import argparse, hashlib, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', required=True)
    ap.add_argument('--root', default=ROOT)
    a = ap.parse_args()
    rel, root = a.release, a.root
    pub = os.path.join(root, 'public', rel)
    rel_dir = os.path.join(root, 'releases', rel)
    man_p = os.path.join(rel_dir, 'manifest.json')

    a_list, evidence = [], {}
    ok1 = ok2 = ok3 = False

    # L1: rerun the public verifier
    try:
        out = subprocess.run([sys.executable, os.path.join(HERE, 'verify_public.py'),
                              '--release', rel, '--root', root],
                             capture_output=True, text=True, timeout=600)
        ok1 = 'PASS' in out.stdout
        evidence['L1'] = {'command': 'python3 tools/verify_public.py --release %s' % rel,
                          'exit': out.returncode, 'tail': out.stdout.strip().splitlines()[-1:]}
    except Exception as e:
        evidence['L1'] = {'error': str(e)}

    # L2 / L3
    snap = os.path.join(rel_dir, 'robocurve_allruns.json')
    if os.path.isfile(man_p):
        m = json.load(open(man_p, encoding='utf-8'))
        entry = next((e for e in m.get('files', []) if e.get('file') == 'robocurve_allruns.json'), None)
        if entry and os.path.isfile(snap):
            size_ok = os.path.getsize(snap) == entry.get('bytes')
            hash_ok = sha256(snap) == entry.get('sha256')
            ok2 = bool(size_ok and hash_ok)
            evidence['L2'] = {'declared_sha256': entry.get('sha256'), 'declared_bytes': entry.get('bytes'),
                              'measured_sha256': sha256(snap), 'measured_bytes': os.path.getsize(snap),
                              'size_matches': size_ok, 'hash_matches': hash_ok}
            try:
                data = json.load(open(snap, encoding='utf-8'))
                key = entry.get('count_key', 'runs')
                counted = len(data.get(key, []))
                ok3 = ok2 and counted == entry.get('record_count')
                evidence['L3'] = {'record_count_declared': entry.get('record_count'),
                                  'record_count_measured': counted,
                                  'redistributed_by_this_repository': True}
            except Exception as e:
                evidence['L3'] = {'error': str(e)}
        else:
            evidence['L2'] = {'note': 'snapshot not redistributed; only a hash is published'}
            evidence['L3'] = {'note': 'cannot be reached by an outside reader; requires the source holder'}
    else:
        evidence['L2'] = {'note': 'no manifest'}

    for layer, ok, q in (
            ('L1', ok1, 'published summary reproduces from the published tables'),
            ('L2', ok2, 'local source bytes match the declared hash and size'),
            ('L3', ok3, 'redistributed snapshot reproduces the declared record count')):
        a_list.append({'id': layer, 'quantity': q, 'status': 'verified' if ok else 'not reached',
                       'evidence': evidence.get(layer, {})})

    cert = {
        'certificate_id': 'LAYER-%s' % rel,
        'schema_version': 'EEO-LAYER-1',
        'issued_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
                      .strftime('%Y-%m-%dT%H:%M:%SZ'),
        'issuer': {'name': 'Embodied Evaluation Observatory', 'role': 'archive operator'},
        'release': rel,
        'layers': {'L1': ok1, 'L2': ok2, 'L3': ok3, 'highest': 'L3' if ok3 else ('L2' if ok2 else ('L1' if ok1 else None))},
        'assertions': a_list,
        'input': {'manifest': 'releases/%s/manifest.json' % rel,
                  'snapshot': 'releases/%s/robocurve_allruns.json' % rel},
        'protocol': {'file': 'reda-protocol.md', 'sha256': sha256(os.path.join(root, 'reda-protocol.md'))
                     if os.path.isfile(os.path.join(root, 'reda-protocol.md')) else None},
        'not_certified': ['model capability', 'benchmark validity', 'safety of any deployed system',
                          'completeness of the upstream source'],
        'verification': {'rerun': 'python3 tools/certify.py --release %s' % rel},
    }
    blob = json.dumps({k: v for k, v in cert.items() if k != 'certificate_hash'},
                      ensure_ascii=False, sort_keys=True)
    cert['certificate_hash'] = sha256_str = hashlib.sha256(blob.encode('utf-8')).hexdigest()

    out_dir = os.path.join(root, 'certificates', rel)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'layers.json')
    json.dump(cert, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('written: certificates/%s/layers.json' % rel)
    print('L1=%s L2=%s L3=%s highest=%s hash=%s'
          % (ok1, ok2, ok3, cert['layers']['highest'], sha256_str[:12]))


if __name__ == '__main__':
    main()
