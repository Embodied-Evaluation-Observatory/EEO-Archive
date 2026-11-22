# Verification key

`eeo-signing-2026-11.pub` is the public half of the key that signs commits and release tags
from 2026-11-22 onward. `allowed_signers` is the same key in the format `git` expects, bound to
the two addresses that appear as committer and tagger: the maintainer's own address and the
archive's operational mailbox, which forwards to it. One key, two principals, no second key
to rotate.

| Item | Value |
|---|---|
| key type | ssh-ed25519 |
| fingerprint | `SHA256:IMoazGr4HNXbNdMuT7UM1w1CQZXtN3iwb3L6RwsVfP0` |
| principals | `jiaxi999@163.com` and `archive@embodied-evaluation.org` |
| first signed commit | `6af19d5` (2026-11-22) |
| first signed tag | `v2026.11.22` |

## Where this key came from

It was read out of the `SSHSIG` block inside the `v2026.11.22` tag object, not copied from a
person or a web page. An `SSHSIG` block carries the public key it was made with, so the file
here is the exact key that produced that signature by construction.

That removes one dependency and leaves one open: this file proves that the key in it verifies
the signatures in this repository. It cannot by itself prove who holds the private half. For
that, compare the fingerprint above against GitHub's `Verified` badge for `1f2d114`, or
against a fingerprint exchanged out of band before the tag was pushed.

## Rotation

If the key is lost or replaced, a new file is added here under a new name and the old one
stays. Verifying an older tag uses the older key; nothing is rewritten. `SIGNING.md` rule 4
applies.
