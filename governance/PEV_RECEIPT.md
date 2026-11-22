# Modules, matrix, and the two records they emit

This file fixes two artefacts: the process-evidence verification record (PEV) and the
recomputation receipt (REC). It also fixes the matrix that every deliverable here has to
satisfy. It is normative for anything the archive signs.

Chinese term equivalents, for cross-reference only: 样本预算 sample budget ·
过程证据核验 process-evidence verification · 数据体检 data health · 复现核验 reproduction
verification · 可比性纪律 comparability discipline · 分级与收据 grading and receipt.

The module is named for the act, not for its acceptance criterion. What an M1 job decides
is how many attempts, configurations and cells are needed; the target interval width governs
that decision and belongs in column C, not in the module name. A budget that names no
precision is a number without a specification, and is not signed.

## The matrix

Four modules are rows. Two cross-cutting attributes are columns. A cell holds the
requirement that module must meet under that attribute. Nothing in column C or column R is
optional; a module that cannot meet it does not get signed.

| Module | Deliverable | C: comparability (can these two numbers be compared?) | R: grading and receipt (what is delivered, at which level, with what proof?) |
|---|---|---|---|
| M1 sample budget | budget sheet | C1 — budget stated within one stratum (task set × policy × judging rule), with the multiplicity-adjusted **minimum detectable difference**; any figure carried from another stratum names its origin and its non-applicability | R1 — REC carries target interval width, required attempts, simulation assumption, seed |
| M2 process-evidence verification | PEV record | C2 — verified fields and the claimed protocol share one definition; a changed site, collector or judging rule makes the trace non-comparable | R2 — REC carries the field list, tri-state result per field, and the unverified list |
| M3 data health | health report | C3 — rho and the zero-variance share are reported per stratum, never pooled; no rho is carried from another domain | R3 — REC carries derived-table hash, estimator definition, interval method, design effect |
| M4 reproduction verification | reproduction record | C4 — reproduction runs on the claimed task set, prompt and judging rule; changing any of the three downgrades it to partial | R4 — REC carries input hashes, recompute command, tolerance, observed deviation |

C1 and C3 are where domain transfer bites. `DOMAIN_TRANSFER.md` governs the rule; two measured
facts make it non-negotiable. The archive's own strata span 0.4841 to 0.8167 on one snapshot,
so a single number moved between strata erases the variation it is meant to describe. A
public site-level figure of 0.0827, borrowed where 0.5 was assumed, is wrong by roughly
sixfold. Where a module ranks or compares assessors rather than units, C3 splits two variance
sources that are routinely reported as one: inter-rater agreement and within-unit clustering.

## Temporal validity

The constraint on M1 and M2 is not that the work cannot be done late. It is that **the
process metadata has to be captured at the time**. What was never recorded cannot be
verified later; a late record is a partial one.

The minimum set, `eval_log_min` (schema in `schema/eval-log-min.schema.json`):

| Field | Why it cannot be reconstructed | Needed by |
|---|---|---|
| `seed` | the generator state is gone once the attempt ends | M4 recompute |
| `init_state_digest` | proves every attempt started from the same state | M2, M4 |
| `termination_reason` | success, failure, interrupt and timeout are indistinguishable in a bare outcome flag | M2, M3 |
| `scoring_method` | whether a human, a script or both judged the attempt | M2, M3 |
| `rerun_flag` / `replacement_flag` | dropping failed attempts silently changes the denominator | M2, M3 |

When the run is already over — the normal case for public third-party data — two
retrospective variants exist, and they are weaker:

| Variant | Answers | Does not answer | Ceiling |
|---|---|---|---|
| retrospective budget adequacy | was the original budget adequate, given its stated target | was the original budget followed | L1 |
| retrospective trace verification | do the retained records agree with each other | anything about fields never recorded | L1 |

Both rise to L2 only if dated artefacts are supplied (a budget signed before the run, a
review record, a locked analysis file). An undated file proves nothing about sequence.

This is the reason the modules split the way they do. M1 and M2 are embedded and preventive:
captured before and during the run, their marginal cost is near zero. M3 and M4 are late
arrivals by design: they need only data and a claim, and can be delivered long after the run
has ended. A constraint that reads like a limitation is, in practice, the line between the
two product halves.

## PEV record

One PEV per verification. Field names are normative.

| Field | Type | Required | Rule |
|---|---|---|---|
| `pev_id` | string | yes | `PEV-<yyyymmdd>-<slug>` |
| `module` | enum | yes | `M2` |
| `level` | enum | yes | `L1` \| `L2` \| `L3` |
| `window` | object | yes | `{start,end}` of the observation period, ISO dates |
| `claim_under_test` | string | yes | **verbatim quotation** of the claim under test. Paraphrase is a defect, not a style: a reworded claim is a different object, and the record then verifies something nobody said |
| `claim_locator` | object | yes | `{source_file,locator}` — where the quotation sits, so a reader can confirm it is verbatim rather than trusting this record |
| `source_files` | array | yes | one entry per file: `{role,id,bytes,sha256}`; `role` ∈ `log`,`export`,`manifest`,`protocol`; `bytes` ≥ 1, a materialised file only — a remote dataset id is not an input until its bytes are read and hashed |
| `fields_checked` | array | yes | see below; at least one entry |
| `denominator` | object | when applicable | `{randomized,analysed,reported,closed}` with `closed` boolean |
| `anomalies` | array | yes (may be empty) | `{id,description,severity}`; `severity` ∈ `blocking`,`material`,`note` |
| `not_verified` | array | yes, the key must be present (it may be empty) | fields a reader might assume were checked, listed explicitly as not checked. An empty array means nothing was left unchecked. **Omitting the key is invalid**, because absence reads as coverage |
| `signer` | object | yes | `{name,role,date}` |
| `verify` | object | yes | `{command,expected}` — a reader runs it and gets the same record |

`fields_checked` entry:

| Key | Type | Rule |
|---|---|---|
| `field` | string | column name as it appears in the source |
| `rule` | string | the check stated so that a reader could re-run it without asking |
| `result` | enum | `conform` \| `nonconform` \| `undetermined` |
| `evidence` | string | pointer to the row set or file section the result rests on |

Three states, never two. "Not supplied" and "wrong" are different findings; collapsing them
is how a verification record starts implying more than it checked.

## Receipt

One REC per deliverable, all four modules. Field names are normative; extra keys are
allowed, missing required keys are not.

| Field | Type | Required | Rule |
|---|---|---|---|
| `receipt_id` | string | yes | `REC-<yyyymmdd>-<slug>` |
| `receipt_version` | string | yes | `EEO-REC-1` |
| `issued_utc` | string | yes | ISO 8601 with `Z` |
| `module` | enum | yes | `M1`..`M4` |
| `level` | enum | yes | `L1` \| `L2` \| `L3` |
| `claim` | string | yes | one sentence, the narrowest statement the record supports |
| `scope` | object | yes | `{stratum,population,n_units}` |
| `inputs` | array | yes | `{role,id,bytes,sha256}` per input |
| `derivation` | object | yes | `{method,formula,seed,software:{name,version},tolerance}` |
| `outputs` | array | yes | `{name,rows,sha256}` per published artefact |
| `checks` | array | yes | `{id,rule,result,evidence}` per check; same tri-state as PEV |
| `comparability` | object | yes | `{rule_applied,borrowed_from,permitted,note}`; `borrowed_from` is `null` when nothing was borrowed |
| `not_supported` | array | yes, at least one entry | statements a reader might wrongly draw; each phrased as a denial. A record always supports less than it could appear to, so an empty list is a defect rather than a clean bill |
| `signer` | object | yes | `{name,role,date}` |
| `verify` | object | yes | `{command,expected}` |

Skeleton:

A complete, schema-valid record lives in `examples/receipt-example.json`, with real byte counts
and hashes taken from `audits/public-data/2026-11-21/`. There is deliberately no inline
pseudo-skeleton: a skeleton with placeholder hashes would fail the schema, and a normative
document should not ship an artefact that its own validator rejects.

## Validation

The tables above are prose; these two files are the enforceable form:

| File | Applies to |
|---|---|
| `pev-record.schema.json` | PEV records, JSON Schema draft 2020-12 |
| `receipt.schema.json` | receipts, `EEO-REC-1` |
| `eval-log-min.schema.json` | per-attempt logs (`eval_log_min`), an array of attempts |
| `validate.py` | all three; infers the type from `pev_id`, `receipt_id`, or an array |
| `examples/pev-example.json` | a record that passes |
| `examples/receipt-example.json` | a receipt that passes |
| `examples/eval-log-example.json` | two attempts that pass |

```
python3 governance/schema/validate.py governance/schema/examples/pev-example.json
python3 governance/schema/validate.py governance/schema/examples/receipt-example.json
python3 governance/schema/validate.py governance/schema/examples/eval-log-example.json
```

What the schemas enforce, and what they cannot:

| Enforced | Not enforceable |
|---|---|
| `claim_under_test` present, and `claim_locator` present so the quotation can be checked | that the quoted string is actually verbatim — a reader still has to open the located file |
| `not_verified` key present, empty allowed, omission rejected | that the listed unverified fields are the only ones left unchecked |
| `bytes` ≥ 1 and a 64-hex `sha256`; a remote dataset id alone cannot be filed as an input | that the file's content is what the record says it is, beyond re-hashing |
| results restricted to `conform`/`nonconform`/`undetermined` | that a check's stated rule is the rule actually applied |
| `not_supported` at least one entry | that every unsupported reading was anticipated |
| a non-null `borrowed_from` requires a non-empty note | that the borrow was legitimate; that judgement stays with `DOMAIN_TRANSFER.md` |
| `eval_log_min` requires `seed`, `init_state_digest`, `termination_reason`, `scoring_method`, `rerun_flag`, `replacement_flag` | that these were captured at the time rather than backfilled; a backfilled value looks identical |

The right-hand column is the reason these records are signed by a person and not issued by
a script. The schema removes the cheap failures, which are the majority; the remaining ones
are the ones worth a signature.

## Levels

| Level | Basis | Typical material |
|---|---|---|
| L1 | public artefacts only | paper, report, registry entry, public dataset |
| L2 | internal documents supplied | plan, change log, analysis script, table list |
| L3 | rows or line-level data recomputable | raw records, per-case data, runnable program |

A level describes the basis, not the verdict. One record may hold L1 and L3 checks side by
side; the record states which check rests on which basis.

## Refusals

1. No experiment design, model choice, or tuning.
2. No on-site observation, no site access, no monitoring on a sponsor's behalf.
3. No vendor ranking, no better-or-worse statement about a party.
4. No certification, no certificate, no "passed".
5. No paper writing, no journal review, no plagiarism screening.
6. No publication of raw logs, video, or images.
7. No claim of full M1/M2 force in a retrospective case.
8. No regulatory conclusion, no "compliant with <regulation>".

## References

`DOMAIN_TRANSFER.md` governs what C means in practice. `DATA_TERMS.md` governs what may be
published from partner material. Both bind every REC issued under this file.
