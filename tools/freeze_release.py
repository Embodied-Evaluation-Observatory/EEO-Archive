#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EEO Archive — release freezer.

Creates one immutable release directory, hashes every file, extracts record
counts where the JSON shape allows, and appends a release entry to MANIFEST.json.

Immutability rules:
  * a release directory is never overwritten; re-running the same release id fails;
  * a re-freeze of an existing release with different bytes is refused, not merged;
  * MANIFEST.json is append-only, and each release entry carries a release hash
    (sha256 of its own manifest.json) so the index itself can be checked later.

Usage:
  python3 freeze_release.py --release 2026-11-15 \
      --files ../../robo_logs/robocurve_allruns.json \
      --source-note "https://robocurve.org/all-runs/"
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import sys

ARCHIVE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def probe(path):
    """Best-effort record count and shape note; never fatal."""
    info = {'record_count': None, 'shape': 'unknown'}
    if not path.lower().endswith(('.json', '.jsonl')):
        return info
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        info['shape'] = 'unparsed: %s' % e
        return info
    if isinstance(data, list):
        info['shape'] = 'list'
        info['record_count'] = len(data)
    elif isinstance(data, dict):
        keys = list(data.keys())
        info['shape'] = 'dict:%s' % ','.join(keys[:6])
        for k in ('runs', 'records', 'data', 'items', 'trials'):
            if isinstance(data.get(k), list):
                info['record_count'] = len(data[k])
                info['count_key'] = k
                break
    return info


def load_manifest(root):
    p = os.path.join(root, 'MANIFEST.json')
    if not os.path.exists(p):
        return {'archive': 'EEO Archive', 'releases': []}
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', required=True, help='release id, e.g. 2026-11-15')
    ap.add_argument('--files', nargs='*', default=[],
                    help='source files to copy in; may be empty when --reuse covers the snapshot')
    ap.add_argument('--source-note', default='')
    ap.add_argument('--provenance', default='', help='provenance note copied in as SOURCE.md')
    ap.add_argument('--reuse', nargs='*', default=[],
                    help='release:file — reference bytes already frozen in an earlier release '
                         'instead of copying them again, e.g. 2026-11-17:robocurve_allruns.json')
    ap.add_argument('--root', default=ARCHIVE_ROOT)
    args = ap.parse_args()

    manifest_path = os.path.join(args.root, 'MANIFEST.json')
    rel_dir = os.path.join(args.root, 'releases', args.release)
    index = load_manifest(args.root)

    existing = next((r for r in index['releases'] if r['release'] == args.release), None)
    if existing is not None or os.path.isdir(rel_dir):
        print('REFUSED: release %s already exists. Releases are immutable.' % args.release,
              file=sys.stderr)
        print('To correct a release, publish a new release id and state the correction.',
              file=sys.stderr)
        return 2

    os.makedirs(rel_dir)
    entries = []
    if args.provenance:
        if not os.path.isfile(args.provenance):
            print('MISSING: %s' % args.provenance, file=sys.stderr)
            return 3
        dst = os.path.join(rel_dir, 'SOURCE.md')
        shutil.copy2(args.provenance, dst)
        entries.append({
            'file': 'SOURCE.md',
            'bytes': os.path.getsize(dst),
            'sha256': sha256(dst),
            'source_path': os.path.abspath(args.provenance),
            'kind': 'provenance',
            'record_count': None,
        })
    for spec in args.reuse:
        if ':' not in spec:
            print('BAD --reuse value: %s (expected release:file)' % spec, file=sys.stderr)
            return 4
        src_rel, name = spec.split(':', 1)
        src_man = os.path.join(args.root, 'releases', src_rel, 'manifest.json')
        if not os.path.isfile(src_man):
            print('MISSING: %s' % src_man, file=sys.stderr)
            return 3
        sm = json.load(open(src_man, encoding='utf-8'))
        src = next((e for e in sm.get('files', []) if e.get('file') == name), None)
        if src is None:
            print('MISSING: %s not in releases/%s/manifest.json' % (name, src_rel), file=sys.stderr)
            return 3
        target = os.path.join(args.root, 'releases', src_rel, name)
        if not os.path.isfile(target):
            print('MISSING: %s' % target, file=sys.stderr)
            return 3
        if sha256(target) != src['sha256']:
            print('HASH MISMATCH: %s no longer matches its own manifest' % target, file=sys.stderr)
            return 5
        entries.append({
            'file': name,
            'bytes': src['bytes'],
            'sha256': src['sha256'],
            'kind': 'reused_from_release',
            'reused_from': 'releases/%s/%s' % (src_rel, name),
            'record_count': src.get('record_count'),
            'shape': src.get('shape'),
            'count_key': src.get('count_key'),
        })

    for src in args.files:
        if not os.path.isfile(src):
            print('MISSING: %s' % src, file=sys.stderr)
            return 3
        name = os.path.basename(src)
        dst = os.path.join(rel_dir, name)
        shutil.copy2(src, dst)
        info = probe(dst)
        entries.append({
            'file': name,
            'bytes': os.path.getsize(dst),
            'sha256': sha256(dst),
            'source_path': os.path.abspath(src),
            **info,
        })

    rel_manifest = {
        'archive': 'EEO Archive',
        'release': args.release,
        'frozen_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'source_note': args.source_note,
        'files': entries,
        'note': ('Files are stored byte-for-byte as fetched. The Archive does not '
                 'relicense third-party records; redistribution follows the source '
                 'terms stated in SOURCE.md.'),
    }
    rp = os.path.join(rel_dir, 'manifest.json')
    with open(rp, 'w', encoding='utf-8') as f:
        json.dump(rel_manifest, f, ensure_ascii=False, indent=2)

    index['releases'].append({
        'release': args.release,
        'frozen_at_utc': rel_manifest['frozen_at_utc'],
        'release_hash_sha256': sha256(rp),
        'file_count': len(entries),
        'total_bytes': sum(e['bytes'] for e in entries),
    })
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print('frozen %s: %d files, %d bytes' % (
        args.release, len(entries), sum(e['bytes'] for e in entries)))
    print('release hash %s' % sha256(rp))
    return 0


if __name__ == '__main__':
    sys.exit(main())
