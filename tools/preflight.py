#!/usr/bin/env python3
"""Pre-publication gate.

Runs the checks that must all pass before a release or a Zenodo deposit is
published. Any failure exits non-zero, so a release script cannot continue past
it. Written after the 24288113 mistake: a deposit was published whose files had
not been replaced.

Checks, in order:
  1. manifest: the frozen snapshot on disk matches its recorded bytes and sha256
  2. public tables: checksums.txt matches every published file
  3. recompute: verify_public.py reproduces the summary from attempts.csv
  4. certificates: certify.py reports L1, L2 and L3 reached
  5. protocol binding: the certificate carries the current protocol hash
  6. deposit: files downloaded from the deposit match the manifest and the tables
     (optional, but a release may not be published without it)

Usage:
  python3 tools/preflight.py --release 2026-11-17 \
      --input releases/2026-11-17/robocurve_allruns.json
  python3 tools/preflight.py --release 2026-11-17 \
      --input releases/2026-11-17/robocurve_allruns.json \
      --zenodo-dir ~/Downloads/zenodo-24325457

The optional --zenodo-dir should hold the files exactly as downloaded from the
deposit page. The gate hashes them and compares against the local release. Use
--zenodo-checksums instead when only the deposit's checksums.txt is available.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def rel(path):
    return os.path.relpath(path, ROOT)


def parse_checksums(path):
    out = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line.strip():
                continue
            digest, name = line.split(None, 1)
            out[name.strip()] = digest.strip().lower()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', required=True)
    ap.add_argument('--input', default=None, help='frozen snapshot for verify_public')
    ap.add_argument('--zenodo-dir', default=None, help='files as downloaded from the deposit')
    ap.add_argument('--zenodo-checksums', default=None, help='checksums.txt from the deposit')
    ap.add_argument('--out', default=None, help='write a JSON record of the run')
    a = ap.parse_args()

    results = []

    def check(name, ok, detail):
        results.append({'check': name, 'ok': bool(ok), 'detail': detail})
        print(('PASS  ' if ok else 'BLOCK ') + name + ': ' + detail)
        return ok

    pub = os.path.join(ROOT, 'public', a.release)
    cert_dir = os.path.join(ROOT, 'certificates', a.release)
    man_path = os.path.join(ROOT, 'releases', a.release, 'manifest.json')

    # 1. manifest against disk
    ok = True
    detail = ''
    if not os.path.exists(man_path):
        ok, detail = False, 'no manifest at %s' % rel(man_path)
    else:
        man = json.load(open(man_path, encoding='utf-8'))
        for entry in man.get('files', []):
            p = os.path.join(ROOT, 'releases', a.release, entry['file'])
            if not os.path.exists(p):
                ok, detail = False, 'missing snapshot %s' % entry['file']
                break
            size, digest = os.path.getsize(p), sha256(p)
            if size != entry['bytes'] or digest != entry['sha256']:
                ok, detail = False, '%s: bytes %d vs %d, sha %s vs %s' % (
                    entry['file'], size, entry['bytes'], digest[:12], entry['sha256'][:12])
                break
        else:
            detail = '%d snapshot file(s) match bytes and sha256' % len(man.get('files', []))
    check('manifest', ok, detail)

    # 2. published tables against checksums.txt
    ck_path = os.path.join(pub, 'checksums.txt')
    ok = True
    detail = ''
    if not os.path.exists(ck_path):
        ok, detail = False, 'no checksums.txt in %s' % rel(pub)
    else:
        listed = parse_checksums(ck_path)
        bad = []
        for name, digest in listed.items():
            p = os.path.join(pub, name)
            if not os.path.exists(p):
                bad.append(name + ' (missing)')
            elif sha256(p) != digest:
                bad.append(name + ' (hash differs)')
        extra = sorted(set(os.listdir(pub)) - set(listed) - {'checksums.txt'})
        if bad:
            ok, detail = False, 'mismatch: ' + ', '.join(bad)
        elif extra:
            ok, detail = False, 'published but unlisted: ' + ', '.join(extra)
        else:
            detail = '%d published file(s) match checksums.txt' % len(listed)
    check('public tables', ok, detail)

    # 3. recompute the summary from attempts.csv
    if a.input:
        cmd = [sys.executable, os.path.join(ROOT, 'tools', 'verify_public.py'),
               '--release', a.release, '--input', a.input]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        tail = (r.stdout.strip().splitlines() or [''])[-1]
        check('recompute', r.returncode == 0, tail or r.stderr.strip()[-120:])
    else:
        check('recompute', False, 'no --input given; the summary cannot be reproduced')

    # 4. certificates
    cmd = [sys.executable, os.path.join(ROOT, 'tools', 'certify.py'), '--release', a.release]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    layers_path = os.path.join(cert_dir, 'layers.json')
    if os.path.exists(layers_path):
        layers = json.load(open(layers_path, encoding='utf-8'))
        reached = [k for k, v in (layers.get('layers') or {}).items() if v is True]
        check('certificates', r.returncode == 0 and len(reached) == 3,
              'reached %s' % ', '.join(reached) if reached else 'none reached')
    else:
        check('certificates', False, 'no layers.json written')

    # 5. certificate binds the current protocol
    proto = os.path.join(ROOT, 'reda-protocol.md')
    c7_path = os.path.join(cert_dir, 'C7.json')
    if os.path.exists(c7_path):
        c7 = json.load(open(c7_path, encoding='utf-8'))
        bound = (c7.get('protocol') or {}).get('sha256', '')
        current = sha256(proto)
        check('protocol binding', bound == current,
              'certificate %s, protocol %s' % (bound[:12] or '(none)', current[:12]))
    else:
        check('protocol binding', False, 'no C7.json in %s' % rel(cert_dir))

    # 6. deposit, when supplied
    if a.zenodo_dir:
        ok = True
        detail = ''
        man = json.load(open(man_path, encoding='utf-8')) if os.path.exists(man_path) else {'files': []}
        expect = {e['file']: (e['bytes'], e['sha256']) for e in man.get('files', [])}
        for name, digest in parse_checksums(os.path.join(pub, 'checksums.txt')).items():
            expect[name] = (None, digest)
        for name, (size, digest) in expect.items():
            p = os.path.join(os.path.expanduser(a.zenodo_dir), name)
            if not os.path.exists(p):
                ok, detail = False, name + ' absent from the deposit folder'
                break
            if sha256(p) != digest:
                ok, detail = False, name + ': deposit hash differs from the release'
                break
            if size is not None and os.path.getsize(p) != size:
                ok, detail = False, '%s: deposit bytes %d vs %d' % (name, os.path.getsize(p), size)
                break
        else:
            detail = '%d file(s) downloaded from the deposit match the release' % len(expect)
        check('deposit files', ok, detail)
    elif a.zenodo_checksums:
        z = parse_checksums(os.path.expanduser(a.zenodo_checksums))
        local = parse_checksums(os.path.join(pub, 'checksums.txt'))
        diff = [k for k in local if z.get(k) != local[k]]
        check('deposit files', not diff,
              'deposit checksums match the release' if not diff
              else 'differs for: ' + ', '.join(diff))
    else:
        check('deposit files', False,
              'not verified: pass --zenodo-dir or --zenodo-checksums before publishing')

    blocked = [r['check'] for r in results if not r['ok']]
    print()
    print('GATE: ' + ('PASS — safe to publish' if not blocked
                      else 'BLOCKED — do not publish (%s)' % ', '.join(blocked)))
    if a.out:
        with open(a.out, 'w', encoding='utf-8') as f:
            json.dump({'release': a.release, 'gate': 'pass' if not blocked else 'blocked',
                       'checks': results}, f, ensure_ascii=False, indent=1)
        print('record: ' + rel(a.out))
    return 0 if not blocked else 1


if __name__ == '__main__':
    sys.exit(main())
