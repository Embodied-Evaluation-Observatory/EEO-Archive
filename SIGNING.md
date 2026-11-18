# Signing policy

Trust is the product here, so the project's own identity has to be checkable. An audit
archive whose commits cannot be attributed is asking readers to extend a trust it has not
earned.

## Current state

Commits through 2026-11-18 are unsigned. The repository was operated through a cloud
workspace without access to a private key, and GitHub marks those commits `Unverified`.
They are not retroactively signable: a signature covers the commit object, so changing the
commit to add one changes its hash and invalidates every tag and reference that points at
it. The honest sequence is to sign from the next commit onward and keep the earlier range
as a documented exception, not to rewrite history.

## Set up signing, once, on the machine that pushes

SSH signing is used here because it needs no GPG agent. GPG works the same way with
`gpg.format=openpgp`.

```
ssh-keygen -t ed25519 -C "maintainer@embodied-evaluation.org" -f ~/.ssh/eeo_signing
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/eeo_signing.pub
git config --global commit.gpgsign true
git config --global tag.gpgsign true
```

Register the public key on GitHub: Settings → SSH and GPG keys → New SSH key → Key type
`Signing key`, paste `~/.ssh/eeo_signing.pub`. The email in the key and in
`git config user.email` must match an address on the account, or GitHub shows the commit
but not the `Verified` badge.

Verify locally before pushing:

```
git log --show-signature -1
git tag -v v2026.11.18.1
```

## Tags

Annotated tags are signed with the same key. A release tag that is not signed leaves the
release artifact itself unattributable, whatever the commits say.

```
git tag -s v2026.11.18.1 -m "EEO Archive, release 2026-11-18, citation metadata fix"
git push origin v2026.11.18.1
```

`v2026.11.18` was created before this policy and cannot be signed in place: GitHub
immutable releases lock the tag. If a signed release tag is wanted for the 2026-11-18
contents, it has to be a new tag pointing at the same commit, and the old one stays as a
documented unsigned predecessor.

## Rules

1. From the next release onward, every release tag and every release commit is signed.
2. Unsigned commits reachable from `main` are listed as an exception in `STATUS.md`, with
   the reason, rather than silently tolerated.
3. A signature says the commit came from the holder of the key. It says nothing about
   whether the analysis is correct; that is what the recompute path is for.
4. Losing the key is not a reason to rewrite history. Start a new key, publish the
   transition, and keep the old range verifiable against the old key.
