# Access to inputs, and who can verify what

Different releases can offer different access to their inputs. This file states,
per release, what an outside reader can actually do, and it names the access
route rather than leaving it implicit.

## Three routes

| Route | Input holder publishes | Outside reader can | Typical case |
|---|---|---|---|
| Open | the snapshot itself | re-run the export and compare | public leaderboards whose terms permit redistribution |
| Hash only | sha256 and byte counts | confirm a copy they already hold, not derive one | licensed or restricted benchmarks |
| Controlled | a named verification route | request a supervised check | sources that forbid redistribution but allow audit |

Controlled access is described as a route, not a promise: a written agreement
naming what may be read, by whom, for how long, and what may be published about
the result. This archive does not implement zero-knowledge proofs or secure
multi-party computation, and does not claim that a hash substitutes for reading
the bytes.

## Per-release state

| Release | Route | Note |
|---|---|---|
| 2026-11-15 | Hash only | snapshot held, hash published |
| 2026-11-17 | Open | snapshot redistributed; L3 reachable by any reader |

## Verification partners

Where a release is hash-only, the asymmetry is real: only the holder can finish
the chain. `governance/verification_partners.csv` records who can, on what terms,
so that the gap is stated rather than hidden. The table is currently empty: no holder
has registered as of 2026-11-18, and the archive does not list parties that have not
agreed. Entries are added at the request of
the holder; the archive does not claim a partner has verified anything beyond the
scope recorded there.

## What this archive will not do

- It will not describe a hash as if it were the data.
- It will not claim "independently verified" for a check performed by the party
  that produced the data.
- It will not accept an input it cannot state the access route for.
