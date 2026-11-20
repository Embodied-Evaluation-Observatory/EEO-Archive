# Getting an outside run, and recording it

The certificate has three layers. L3 says an outsider *can* rebuild the published tables
from the redistributed snapshot; it does not say anyone *did*. This file is about the second
thing: a named outside run, its receipt, and the register that records it. The two are kept
apart so that neither the word "verified" nor the certificate pretends to more than it has.

## What an outside run costs

Two minutes on an ordinary laptop, no account, no data sent anywhere:

```
git clone https://github.com/Embodied-Evaluation-Observatory/EEO-Archive.git
cd EEO-Archive
python3 tools/reproduce.py --release 2026-11-17
```

That prints a receipt JSON and a verdict. If they hold the snapshot and want the harder
check, add `--input releases/2026-11-17/robocurve_allruns.json`. Anyone who would rather
not touch a terminal can drop the two tables into `verify.html`, which computes the
deterministic checks in the browser and downloads the same receipt shape.

Forking the repository and running the **Reproduce a release** workflow also works; the
receipt lands as a build artifact. GitHub Actions is then the "backend", and the runner is
theirs, not ours.

## Who to ask, and how

Ten invitations, expecting two or three replies, is a realistic ratio. Ask people whose
incentive is already aligned with checking rather than believing:

| Profile | Where to find them | Why they might say yes |
|---|---|---|
| Meta-science and evaluation-methodology researchers | NeurIPS Datasets & Benchmarks authors, ICLR/ACL evaluation papers | the object of study is the audit itself |
| Maintainers of smaller benchmarks | RoboTwin, RoboDojo, RoboSpoof repositories | an outside number about their own board is useful |
| Course instructors | robotics courses that teach benchmarking | a two-minute exercise with a real receipt |
| Journal and conference reviewers | reviewers of papers that cite this archive | a checkbox they can point to |
| Standards and governance staff | national AI institutes, MLCommons working groups | claim verification is their remit |
| Competing vendors' engineers | teams that publish "first place" claims | a cheap way to test a rival's claim |

The message that works is short and specific. Do not send a white paper.

> Subject: two minutes to check a robot-evaluation claim
>
> We publish a small audit of public robot benchmarks. One command re-derives every number
> the summary reports, and it produces a receipt with file hashes. Would you run it once on
> your machine and send the receipt? Named or anonymous, your choice. If it fails, that is
> the more useful outcome and we will publish the failure too.
>
> `git clone … && python3 tools/reproduce.py --release 2026-11-17`

Send it to individuals, one at a time, with the specific release id and the specific command.
A broadcast to a mailing list gets nothing.

## What counts as independent

- a different person from the maintainer, on a different machine;
- a clean clone at a recorded commit, no local edits, no environment variables that change
  the computation;
- no payment, no shared grant, no employment relationship — a reviewer who has reviewed this
  archive's papers is still independent for this purpose, and the relationship is disclosed;
- the receipt is attached unedited, including failures.

Affiliation is recorded because readers need to judge conflicts, not because it disqualifies
anyone.

## Recording it

`governance/verification_partners.csv` takes one row per run:

| Column | Meaning |
|---|---|
| organisation | lab, university, company, or "independent" |
| role | `external reproducer` |
| release_scope | the release id checked |
| access_route | `public tables`, `redistributed snapshot`, or `sealed bytes` |
| scope_of_check | `arithmetic`, `export`, or `deposit` |
| agreed_on | date the receipt was issued |
| public_note | receipt filename, or "anonymous" |
| evidence_link | issue or artifact URL |

A row is added only after the receipt has been looked at and the verdict reproduced by the
maintainer. No placeholder rows, no "in conversation" entries.

## How the certificate wording changes

`CERTIFICATE_LEVELS.md` keeps L3 as reachability. A separate field records the outside run:

```
"external_reproductions": [{"scope": "arithmetic", "result": "pass",
                            "receipt": "receipts/2026-11-17.json",
                            "organisation": "…", "date": "…"}]
```

Until that array is non-empty, every public statement says "L3 reachable, no outside run
recorded". After the first passing run it says "L3 reachable; independently re-run once
(arithmetic, <date>)". It never says "independently verified" without naming the scope,
because arithmetic reproduction and source access are different claims.

## If the run fails

Publish the failure in the same place as the pass. A failed outside run against a frozen
release means either the receipt environment differs or the archive has a defect; both are
worth knowing. Fixing a defect means a new release with a note, never a silent edit of the
old one.

## Why anyone should bother

Credit is the only currency available here: a named line in the register, an acknowledgement
in the release notes, and the ability to cite a check they performed rather than one they
trusted. No co-authorship is implied, and no money changes hands.
