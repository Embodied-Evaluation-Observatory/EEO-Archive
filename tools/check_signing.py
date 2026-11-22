# -*- coding: utf-8 -*-
"""Audit the signature boundary of the repository.

    python3 tools/check_signing.py
    python3 tools/check_signing.py --json signing.json
    python3 tools/check_signing.py --range ac62480

It does three things in one pass: counts the commits reachable from the range, separates
those that carry a signature from those that do not, and verifies every signed commit against
the key published in `governance/keys/`. If `STATUS.md` declares an unsigned range, the
declared list is compared with the computed one, so a stale list fails the run instead of
going unnoticed.

Exit code 0 means: every signed commit verifies against the published key, and the list in
`STATUS.md` is exactly the unsigned set. Exit code 1 means at least one signature fails to
verify or the declared list does not match. Exit code 2 means a precondition is missing — a
shallow clone, or no key file — because either makes the answer wrong rather than false.

One git call does the whole audit (`git log --format` with `%G?`), so this stays fast on a
repository with thousands of commits. It reports, but does not fail on, verified commits made
under an address other than the bound principal: those check out locally and show Unverified
on GitHub.

Why this exists: the numbers in a document go stale the moment a commit lands. The boundary
does not. This tool prints the numbers so the document does not have to.
"""
import argparse
import json
import os
import re
import subprocess
import sys

KEYS = os.path.join('governance', 'keys')
SIGNERS = os.path.join(KEYS, 'allowed_signers')
PUBKEY = os.path.join(KEYS, 'eeo-signing-2026-11.pub')
STATUS = 'STATUS.md'

# %G? output: G good, U good but unknown key, N no signature, B bad, E error, X expired,
# Y expired key, R revoked key. Only G counts as verified here, because the point is whether
# a reader holding the published key can check it.
VERIFIED = {'G'}
UNSIGNED = {'N'}
BROKEN = {'B', 'E', 'X', 'Y', 'R'}


def precondition(message):
    print(message, file=sys.stderr)
    sys.exit(2)


def git(*args, **kw):
    return subprocess.run(('git',) + args, capture_output=True, text=True,
                          check=False, **kw)


def root():
    out = subprocess.run(('git', 'rev-parse', '--show-toplevel'), capture_output=True,
                         text=True, check=False)
    if out.returncode != 0:
        precondition('not inside a git repository')
    return out.stdout.strip()


def is_shallow():
    out = git('rev-parse', '--is-shallow-repository')
    return out.stdout.strip() == 'true'


def read_commits(range_):
    """One git call for the whole range: hash, verification status, author, date."""
    signers = os.path.join(root(), SIGNERS)
    fmt = '%H%x09%h%x09%G?%x09%ae%x09%ad'
    out = git('-c', 'gpg.format=ssh', '-c', 'gpg.ssh.allowedSignersFile=' + signers,
              'log', '--format=' + fmt, '--date=short', range_)
    if out.returncode != 0:
        precondition('git log failed: ' + (out.stderr.strip() or 'unknown error'))
    rows = []
    for line in out.stdout.splitlines():
        parts = line.split('\t')
        if len(parts) < 5:
            continue
        sha, short, state, email, date = parts[:5]
        rows.append({'sha': sha, 'short': short, 'state': state, 'email': email,
                     'date': date})
    return rows


def principals():
    """The identities the published key is bound to, taken from allowed_signers."""
    out = set()
    for line in open(SIGNERS, encoding='utf-8'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        fields = line.split()
        if fields:
            out.add(fields[0])
    return sorted(out)


def declared_unsigned():
    """Read the hash list that STATUS.md declares, if it declares one."""
    if not os.path.exists(STATUS):
        return None
    text = open(STATUS, encoding='utf-8').read()
    marker = 'The unsigned commits'
    if marker not in text:
        return None
    tail = text[text.index(marker):]
    block = re.search(r'```\n(.*?)```', tail, re.S)
    if not block:
        return None
    return set(re.findall(r'\b[0-9a-f]{7,40}\b', block.group(1)))


def compact(shas, per_line=6):
    lines = []
    for i in range(0, len(shas), per_line):
        lines.append('  '.join(shas[i:i + per_line]))
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description='Check the signature boundary of the archive.')
    ap.add_argument('--range', default='HEAD', help='revision range to audit (default HEAD)')
    ap.add_argument('--json', metavar='PATH', help='write a machine-readable summary')
    ap.add_argument('--no-status', action='store_true',
                    help='skip the comparison with STATUS.md')
    a = ap.parse_args()

    os.chdir(root())

    if is_shallow():
        precondition('shallow clone: run "git fetch --unshallow" first, '
                     'or the commit count and the unsigned set are both wrong')
    if not os.path.exists(SIGNERS):
        precondition('missing %s: without the published key nothing here can be '
                     'verified' % SIGNERS)

    rows = read_commits(a.range)
    if not rows:
        precondition('no commits in range %s' % a.range)

    signed = [r for r in rows if r['state'] not in UNSIGNED]
    unsigned = [r for r in rows if r['state'] in UNSIGNED]
    verified = [r for r in rows if r['state'] in VERIFIED]
    broken = [r for r in rows if r['state'] in BROKEN]
    unknown = [r for r in rows if r['state'] == 'U']

    print('range         %s' % a.range)
    print('total         %d' % len(rows))
    print('signed        %d' % len(signed))
    print('unsigned      %d' % len(unsigned))
    print('verified      %d' % len(verified))
    bound = principals()
    if bound:
        print('principal     %s (bound in %s)' % (', '.join(bound), SIGNERS))

    status_state = 'skipped'
    if unsigned:
        print('\nunsigned, newest first:')
        print(compact([r['short'] for r in unsigned]))

    declared = None if a.no_status else declared_unsigned()
    if declared is not None:
        computed = {r['short'] for r in unsigned}
        matched = {d for d in declared for c in computed if c.startswith(d[:7])}
        missing = sorted(computed - matched)
        extra = sorted(declared - matched)
        if missing or extra:
            status_state = 'mismatch'
            if missing:
                print('\ndeclared range misses %d: %s' % (len(missing), '  '.join(missing)))
            if extra:
                print('\ndeclared range lists %d not unsigned: %s'
                      % (len(extra), '  '.join(extra)))
        else:
            status_state = 'match'
            print('\nSTATUS.md     list matches the computed set (%d)' % len(computed))
    elif not a.no_status:
        status_state = 'absent'

    # A good signature under an address other than the bound principal verifies locally but
    # shows Unverified on GitHub, so it is reported as a note rather than a failure.
    others = sorted({r['email'] for r in verified} - set(bound))
    if others:
        print('\nnote: %d verified commit(s) were committed as %s, not the bound principal; '
              'they verify here, and GitHub shows them Unverified'
              % (sum(1 for r in verified if r['email'] not in bound), ', '.join(others)))

    problems = []
    for r in broken:
        problems.append('%s signature does not verify (%s)'
                        % (r['short'], r['state']))
    for r in unknown:
        problems.append('%s signed by a key outside the published set' % r['short'])

    if problems:
        print()
        for p in problems:
            print('FAIL          ' + p)
    print()
    print('RESULT: ' + ('PASS' if not problems and status_state != 'mismatch' else 'FAIL'))

    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump({'range': a.range, 'total': len(rows), 'signed': len(signed),
                       'unsigned': len(unsigned), 'verified': len(verified),
                       'unsigned_shas': [r['short'] for r in unsigned],
                       'principal': bound,
                       'status_md': status_state,
                       'problems': problems}, f, ensure_ascii=False, indent=1)
        print('record: ' + a.json)

    return 0 if not problems and status_state != 'mismatch' else 1


if __name__ == '__main__':
    sys.exit(main())
