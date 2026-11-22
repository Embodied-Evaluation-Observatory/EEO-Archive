# Status

- Started by one founder (`Zimo Li`) and published by one maintainer (`JiaxiLEE622`);
  roles and the reason the two are separate are in `governance/ROLES.md`. Started 2026-11. No institutional backing, no
  funding, no staff. The name describes an intention — to keep a standing record
  of how embodied evaluation is reported — not an existing organisation.
- What exists today: a frozen input snapshot per release, a deterministic export
  and verification pipeline, four ingested public boards, and a disclosure
  audit over 94 claims. Each release is small and reproducible rather than
  comprehensive.
- What does not exist: cross-release trend tracking, failure-cause coverage
  beyond a 16-log pilot, video verification, and any certification of safety or
  performance. None of these are promised.
- Scale, stated plainly: one maintainer, a handful of releases, no external
  users yet. Treat the outputs as a working record, not as an authority.
- Corrections are published as new releases; earlier releases stay citable and
  are not rewritten.

## Deposit identifiers

| Record | Version DOI | Holds | Status |
|---|---|---|---|
| 2026-11-15 | `10.5281/zenodo.24269292` | the 2026-11-15 bytes | citable, not withdrawn |
| intermediate | `10.5281/zenodo.24288113` | the 2026-11-15 files under 2026-11-18 metadata | superseded: published before its files were replaced |
| 2026-11-18 | `10.5281/zenodo.24325457` | the corrected 2026-11-17 tables and the redistributed snapshot | previous version, still citable |
| 2026-11-19 | `10.5281/zenodo.24395810` | the scene-keyed tables, comparability and frontier tables, the probe, the certificates, the board summary and the protocol, 21 files plus a checksum list | current |

Concept DOI `10.5281/zenodo.24269291` covers the series. The 2026-11-19 deposit was
published only after `tools/preflight.py` passed all six gate items against the files
downloaded back from the Zenodo draft; that run is recorded in
`releases/2026-11-19/preflight.json`. Cite the version DOI for a
specific release, the concept DOI for the series. The intermediate record is kept online
because Zenodo does not allow a published deposit to be edited or deleted; its description
states which bytes it serves.

## Verification state

- Every commit before `68bf1a5` is unsigned: `8d1944c` (2026-11-16) through `f2664a7`
  (2026-11-18). They were made from a workspace without a private key, and GitHub marks them
  `Unverified`. They cannot be signed retroactively without rewriting hashes. Signing began
  at `68bf1a5` on 2026-11-18, and every commit since carries a signature that verifies
  against `governance/keys/`. Policy: `SIGNING.md`.
- Each release runs the gate in `RELEASE_GATE.md` before publication; the gate record sits
  beside the release.

The unsigned commits, oldest first:

```
8d1944c  86b2426  bc99bef  5a2e803  96f25b3  cd96990
9228771  ffce49f  9016d64  60e3c8b  4fe30fa  9669953
49892ad  07ec856  91563ba  d26252a  4b45f9f  550e3eb
b033426  b48612a  3a94744  f2664a7
```

The list above is the unsigned set, not a sample: it stays complete as commits are added,
because new commits fall on the signed side of `68bf1a5`. Two commands reproduce the
membership without trusting this file:

```
git rev-list --count HEAD
for c in $(git rev-list --abbrev-commit HEAD); do git cat-file -p $c | grep -q gpgsig || echo $c; done
```

The first prints the total; the second prints the same set of abbreviated shas, newest first.
Neither number is written down here, so neither can go stale.

