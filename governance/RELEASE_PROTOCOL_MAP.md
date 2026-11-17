# Release to protocol map

An audit tool has to be able to answer: which protocol produced this release, and
what happens to older conclusions when the protocol changes.

## Map

| Release | Protocol | Protocol file hash | Toolchain commit | Certificate |
|---|---|---|---|---|
| 2026-11-15 | ReDA-1.0 | not retained under that name; the file was later renamed and revised | `cd96990` | `certificates/2026-11-15/C1..C6` |
| 2026-11-17 | ReDA-1.1 | `304e8b71bdfb90fa…` (`reda-protocol.md`) | `ffce49f` | `certificates/2026-11-17/layers.json`, `C7.json` |
| 2026-11-18 | ReDA-1.2 | `97f1afa36366…` (documentation revision: 0.787 figure, max-T implemented with Holm, §5.1 status) | current | `C7` binds the revision |

`tools/certify.py` writes the protocol hash into every certificate, so a
certificate cannot silently point at a protocol that has since been edited.

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

## Known gap

The 2026-11-15 protocol text is no longer present under its original name, so its
hash cannot be reproduced from this repository alone. Its certificates remain
valid as issued; a reader comparing them with 2026-11-17 should expect the
zero-failure treatment to differ. This gap is recorded rather than papered over.
