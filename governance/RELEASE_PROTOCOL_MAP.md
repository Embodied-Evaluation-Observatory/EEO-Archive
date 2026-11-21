# Release to protocol map

An audit tool has to be able to answer: which protocol produced this release, and
what happens to older conclusions when the protocol changes.

## Map

| Release | Protocol | Protocol file hash | Toolchain commit | Certificate |
|---|---|---|---|---|
| 2026-11-15 | ReDA-1.0 | not retained under that name; the file was later renamed and revised | `cd96990` | `certificates/2026-11-15/C1..C6` |
| 2026-11-17 | ReDA-1.1 | `304e8b71bdfb90fa…` (`reda-protocol.md`) | `ffce49f` | `certificates/2026-11-17/layers.json`, `C7.json` |
| 2026-11-18 | ReDA-1.2 | `844040b08bf9…` (documentation revision: 0.787 figure, Holm implemented, §5.1 status matches the code, §1 safety wording) | `550e3eb` | `C7` binds the revision |
| 2026-11-19 | ReDA-1.2 | `844040b08bf9…` (unchanged) | `ce801c9`, card correction in `180ebea` | `certificates/2026-11-19/layers.json`, `C7.json` |

`tools/certify.py` writes the protocol hash into every certificate, so a
certificate cannot silently point at a protocol that has since been edited.

## Deposit identifiers

| Order | Version DOI | Bytes it serves | Note |
|---|---|---|---|
| 1 | `10.5281/zenodo.24269292` | 2026-11-15 release | still citable |
| 2 | `10.5281/zenodo.24288113` | 2026-11-15 files, 2026-11-18 metadata | published before the file swap; superseded, never to be cited |
| 3 | `10.5281/zenodo.24325457` | 2026-11-17 corrected tables plus the redistributed snapshot | previous version, still citable |
| 4 | `10.5281/zenodo.24395810` | 2026-11-19 scene-keyed tables, comparability and frontier tables, probe, certificates, board summary, protocol | current |

Concept DOI `10.5281/zenodo.24269291` is constant across the four. Zenodo does not allow
published files to be edited, so record 2 remains online; its metadata says which bytes it
holds. The chain is recorded here rather than smoothed over, because a reader who lands on
record 2 needs to know why it exists.

## Rules

1. A protocol revision does not rewrite past releases. The earlier release stays
   citable under the protocol it was computed with, and the difference is stated
   in the newer release rather than back-applied.
2. When a revision changes a number, the newer release names the old value, the
   new value, and the reason. The 2026-11-17 notes carry this for the zero-failure
   bound (0.787 finite-J against 0.770 asymptotic).
3. A tool change that alters output requires a new release. Re-running an old
   release with a new toolchain and overwriting its tables is not permitted.
4. Protocol changes are announced before the release that adopts them, and the
   earlier version remains readable.
5. No release or deposit is published until `tools/preflight.py` exits zero and its
   record is committed beside the release. A deposit that cannot be downloaded back and
   hashed does not pass; see `RELEASE_GATE.md`.
6. From the release after 2026-11-18, tags and release commits are signed. Unsigned
   history is listed in `STATUS.md` with the reason; see `SIGNING.md`.

## Known gap

The 2026-11-15 protocol text is no longer present under its original name, so its
hash cannot be reproduced from this repository alone. Its certificates remain
valid as issued; a reader comparing them with 2026-11-17 should expect the
zero-failure treatment to differ. This gap is recorded rather than papered over.
