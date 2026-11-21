# Verification partners

Some releases are hash-only: the input holder publishes a sha256 and a byte count, not the
bytes. A reader with only the hash cannot finish the chain, and this archive cannot finish
it either. A named third party can. This file states who may be named, what the entry
means, and how one is added or removed. `verification_partners.csv` holds the entries.

## What an entry means

An entry says: this organisation, on these terms, is able to check these releases, and has
said so in writing. It does **not** say the check was performed, that it passed, or that
the organisation endorses anything here. Those would be different claims, recorded
elsewhere or not at all.

Registration is never used as evidence in a certificate. A certificate can record that a
route exists; it cannot record that a partner used it.

## Who can be named

Any of these, provided the person or organisation controls something the archive does not:

- the holder of a restricted input, able to recompute a published estimate from its own
  copy;
- an institution able to run the checker against a copy it already holds under a licence;
- a reader who obtained a copy through the source's own access route.

An entity that only has the published tables is not a partner for a hash-only release: it
has nothing the archive lacks, and the check it can run is the one any reader can run.

## What is recorded

The columns in `verification_partners.csv`:

| Column | Meaning |
|---|---|
| `organisation` | name as the party writes it |
| `role` | `input holder`, `independent recheck`, or `route provider` |
| `release_scope` | the release ids the agreement covers, comma separated |
| `access_route` | `hash only`, `open`, or `controlled`, per `ACCESS.md` |
| `scope_of_check` | what they agreed to check, in their words, not ours |
| `agreed_on` | date of the written agreement, `YYYY-MM-DD` |
| `public_note` | one sentence the party has approved for publication |
| `evidence_link` | public artifact produced by the check, if any; empty until one exists |

No phone numbers, no personal mailboxes, no internal contacts. The contact route is
`archive@embodied-evaluation.org`, which receives mail and does not send; see `ACCESS.md`.

## How an entry is added

1. Request arrives, in writing, at `archive@embodied-evaluation.org`, or is proposed by the
   maintainer and accepted in writing by the party.
2. The maintainer confirms the scope in the party's own words. If the party has not stated
   a scope, the entry waits; a scope written by the archive and attributed to someone else
   is not acceptable.
3. The row is added in a commit. The commit message names the date of the agreement.
4. `agreed_on` is the agreement date, not the commit date.
5. `public_note` is published only in wording the party has seen and approved.

## How an entry is removed or changed

On request, at any time, without a reason being required: the row is deleted, or set to
`withdrawn` in `public_note` when the fact of earlier registration matters. Git history
keeps the earlier state; the archive does not rewrite it.

Adding a release to an existing entry's scope needs the party's agreement for that release.
Silence is not agreement.

## What is not offered

No payment, no exclusivity, no co-authorship, no logo placement, no claim of endorsement,
no confidentiality beyond whatever the source's own terms impose. A partner is free to
publish its own findings, including findings that contradict this archive.

## Current state

No entry as of 2026-11-21. The table has a header and no rows. This is stated rather than
implied: a hash-only release currently has no named route, and a reader relying on one
should know that before citing it.

The 2026-11-19 release is `open`, so the gap does not apply to it; a reader can rerun the
export from the referenced snapshot without any partner at all.
