# Roles

This archive was started by one person and is published by one person. Those are the same
person today, but they need not stay the same, and this file separates the two so that a
reader can tell who set the direction from who holds the keys.

## Roles

| Role | Who | Can | Cannot | Recorded in |
|---|---|---|---|---|
| Founder | `Zimo Li` (`lee8745`) | set scope and method; decide what the archive does and refuses; originate work | merge to `main`, sign releases, or publish deposits, because those need a GitHub session and a signing key | this file, `CONTRIBUTORS.md` |
| Maintainer | `JiaxiLEE622` | merge, cut releases, sign commits and tags, publish deposits, edit protocol and tooling | issue a Layer 3 certificate for work done inside the archive | `CONTRIBUTORS.md`, `SIGNING.md` |
| Contributor | anyone credited in `CONTRIBUTORS.md` | submit files, tooling and analysis; be credited | merge or sign | `CONTRIBUTORS.md`, `contributions/` |
| Verification partner | named in `governance/verification_partners.csv` | check a defined scope, publish its own finding | be named without written agreement, or be cited beyond the recorded scope | `governance/PARTNERS.md` |
| Reader | anyone | reproduce any `open` release from the published snapshot | — | `ACCESS.md` |

Founder and maintainer are different jobs even when they sit in one head. The founder's
decisions show up as what the archive contains; the maintainer's show up as commits. When
the two disagree, the archive pauses rather than picks a side silently.

## Who puts work into the repository

Work by the founder and by contributors reaches `main` through the maintainer's session,
because merging and signing require credentials only the maintainer holds. Authorship is
preserved: commits are authored by the person who wrote the work and signed by the
maintainer's key. A reader can therefore separate "who wrote it" (author field) from "who
put it in" (committer and signature), and both facts are stated here rather than inferred.

This is a mechanical arrangement, not a hierarchy: it exists because the people doing the
work are not at a machine that can sign, not because their judgement is worth less.

## Publishing authority

Only the maintainer merges to `main` and signs release tags. The signing key is registered
with GitHub and described in `SIGNING.md`; adding or replacing a key is a commit of its own,
so a key change is visible in history.

Tags are protected by a ruleset that denies deletion of `v*`. A release that turns out to
be wrong is superseded by a new release; the old tag and its bytes stay.

## Certificates and self-assessment

L1 and L2 certificates describe arithmetic and byte identity; the maintainer may issue them
because anyone can recompute them. Layer 3 means an outside party reran the check and
cannot be self-issued: no commit may mark L3 as reached on the strength of an internal run.
`REPRODUCTION.md` states the same rule and the route for an outside party.

Layer 1 claims in `audits/` concern other people's papers. They are arithmetic checks of
published numbers, issued by the maintainer, and are neither peer review nor a judgement
about the authors.

## Absence and continuity

One signing key, one deposit account, no succession arrangement, no escrow. If the
maintainer is unavailable, no release is cut and no deposit is published; the archive stays
readable and citable, because published releases depend on nothing outside their own bytes.

A reader who needs durability should rely on the deposits and the referenced snapshots, not
on the archive's continuity.

## Changes to this file

Changes are commits by the maintainer, and the commit message says which role changed and
why. If a second signing key is ever registered, this file changes in the same commit that
registers it, so the two records cannot disagree.
