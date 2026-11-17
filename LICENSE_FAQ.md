# Licence FAQ

The repository uses three licence blocks, because three different kinds of
material are in it. Read this before redistributing or reusing anything.

| Material | Licence | Where it is stated |
|---|---|---|
| Code: `tools/`, `tests/` | MIT | `LICENSE` |
| Compiled tables: `public/<date>/*.csv`, `boards/<date>/*.csv` | CC BY 4.0 | `LICENSE-DATA.md` |
| Per-attempt fields originating in a third-party archive (benchmark name, model label, task label, outcome label, score, timestamp) | No new licence granted here; cited as facts | field dictionary in `DATASET_CARD.md` |

## Questions

**May I use `attempts.csv` in academic work?**
Yes. CC BY 4.0 applies to the compiled table: cite the archive, the release
date, the version DOI, and state any transformation you applied.

**May I use it in a commercial analysis or a paid report?**
Yes, under the same terms, for the compiled table. If your product is a
re-publication of the table itself rather than an analysis of it, attribute the
source and keep the licence notice.

**May I train a model on it?**
The compiled table is CC BY 4.0, so training is permitted with attribution. Two
cautions: the table is de-identified only in the sense that rig identifiers are
hashed, and the underlying per-attempt facts remain third-party facts. Model
training on third-party benchmark facts is your call, not a right this archive
can grant.

**May I redistribute the raw snapshot?**
`releases/<date>/robocurve_allruns.json` is a copy of a third-party public
snapshot. We publish it so the export step can be re-run. Redistribution follows
the source site's terms, which is why it sits outside the CC BY block and is
described as a cited copy, not a relicensed work.

**What happens if the source terms change?**
Then this archive's position does not change retrospectively: what was published
stays published under the licences stated at that release, and later releases
carry the later terms. Each release records its own licence block for this reason.

**Do you grant any warranty?**
No. See `LICENSE` for the disclaimer. The archive records what public sources
state; it does not certify that a source is accurate.

**Who decides whether my use is compliant?**
Your institution. This FAQ states the archive's own position in plain language;
it is not legal advice.
