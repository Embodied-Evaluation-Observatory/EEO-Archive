# Terms for partner data

When a party hands over logs rather than pointing at a public snapshot, the archive is
holding something it did not have before, and the terms have to be settled before the files
arrive, not after. This file states the default terms. A written agreement can narrow them;
none of them can be widened by silence.

## What arrives, what leaves

| Stage | What the archive holds | What it publishes |
|---|---|---|
| intake | the logs as supplied, plus the de-identification record | nothing |
| analysis | derived attempt rows, cell structure, estimates, intervals | derived tables only |
| certificate | hashes of the supplied bytes, the derivation record | hashes, estimates, limits |

Raw partner logs are not published. The default output is a derived table plus a hash of
the input, so a reader can confirm that the same input produced the same table without
receiving the input. That is the hash-only route in `ACCESS.md`, applied to a private
source.

## What to send: files, not links

Intake is a file transfer. The archive accepts an actual file, hashes it on arrival, and
records the hash in the certificate. A link is not an input: it can be edited, rate-limited,
taken down or resolved to different bytes on a second request, and none of that is visible in
the certificate.

| Accepted | Not accepted as input |
|---|---|
| CSV, JSONL, Parquet, or a database dump, with a field dictionary | a URL to a dashboard, bucket or repository |
| the attempt-level log described below | screenshots of a dashboard, or a PDF report |
| a declaration file naming the fields that were not captured | an aggregate summary table on its own |

An aggregate table can support a data-health reading and a budget-adequacy reading, both
capped at L1. It cannot support process-evidence verification or reproduction, because
neither can be recovered from totals. If a party has only aggregates, that is where the work
stops, and saying so at intake is cheaper than saying it in the report.

## Required attempt fields

The minimum is `eval_log_min`, schema in `schema/eval-log-min.schema.json`. One object per
attempt. Ten fields are required: `attempt_id`, `cell_id`, `task_id`, `config_id`, `seed`,
`init_state_digest`, `termination_reason`, `scoring_method`, `rerun_flag`,
`replacement_flag`.

| Field group | Feeds | If absent |
|---|---|---|
| `attempt_id`, `cell_id`, `task_id`, `config_id` | cell structure, every module | nothing can be joined; intake is declined |
| `seed`, `init_state_digest` | reproduction | reproduction is not attempted; recorded as not verified |
| `termination_reason`, `scoring_method` | trace verification, data health | the outcome flag is read as reported, and the mix of human and script judging cannot be separated |
| `rerun_flag`, `replacement_flag` | denominators | attempts dropped after the run are invisible; the stated count stands unchallenged |

Fields a party did not capture are declared absent in the declaration file, in the same
transfer. They are recorded in the verification record as not checked. They are not
backfilled later: a value supplied after the run is indistinguishable from one supplied
before it, which is why the record names the date of each field's arrival rather than trusting
the order.

## De-identification

Removed or coarsened before analysis, recorded field by field in the de-identification
record:

- operator identity, shift rosters, and any name attached to an intervention;
- site names and coordinates, coarsened to region or replaced by a site code;
- customer or patient identifiers, order numbers and internal ticket ids;
- free-text notes that can re-identify a person or a site.

Kept, because the statistics need them: outcome, task family, attempt index, timestamps to
the minute, the intervention type (remote takeover, on-site reset, retry), and the model or
fleet version.

Timestamps are kept coarse on purpose. A minute-level timestamp is enough to measure
clustering and not enough to identify an individual worker's shift pattern.

## No redistribution

The archive does not redistribute partner logs, in whole or in part, and does not pass them
to a third party, including a verification partner, without the holder's written agreement
for that specific transfer. If a verification partner is to check the derivation, the holder
names the partner and the scope; the partner receives what the holder agrees to, under the
holder's terms.

This is the same rule as `LICENSE-DATA.md` applies to source archives: facts in the records
belong to whoever produced them, and a compiled table does not carry a licence over the
underlying facts.

## Attribution and disclosure

- The partner is named in public only with its consent, in wording it has seen.
- A commissioned analysis is disclosed in the release it touches, in one line: who asked,
  what was asked, what was paid for if anything.
- Being commissioned changes who asked, not what is checked; the certificate uses the same
  layers and the same wording as a self-initiated one. This repeats `SERVICES.md` because it
  is the clause most likely to be tested.
- The party may publish its own account of the result, including disagreement, and the
  archive will link to it rather than restate it.

## Review before publication

The party sees the draft table and the draft wording before publication and may correct
factual errors: a mislabelled task, a wrong version, a miscounted attempt. It may not
require the removal of a finding it dislikes. If it withdraws consent, the analysis is not
published; the fact of withdrawal may be recorded without the data.

## Retention

Raw logs are deleted after the certificate is issued, or earlier on request, and the
deletion is recorded with a date in the certificate's notes. What remains is the derived
table, the hashes, and the derivation record: enough to re-run the analysis from the same
input, not enough to reconstruct the input.

## What the archive will not do with partner data

- Train or fine-tune anything on it.
- Use it to benchmark a competitor without the holder's agreement.
- Present a partner's numbers in a comparison the partner has not seen.
- Claim ownership of the facts.
- Accept data whose terms forbid the derived publication described above. If only a private
  opinion is wanted, that is a different service and is declined here.

## Current partners

None as of 2026-11-21. Two parties have offered records in conversation; no agreement has
been signed, so no intake has happened and no file has been received.
