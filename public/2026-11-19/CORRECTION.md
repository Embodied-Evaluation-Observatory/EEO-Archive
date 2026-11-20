# Correction: protocol label on this release's data card

`DATASET_CARD.md` in this release states the protocol as "ReDA, version 1.0". That label
was hard-coded in the export template and never updated when the protocol was revised. It
is wrong: the certificate issued with this release binds `reda-protocol.md` at version
ReDA-1.2, sha256 `844040b08bf914211444ec30cb8c8809b9c638a565f7cad173ae217e2b07fad2`.

What is affected: the protocol row of `DATASET_CARD.md`, and the same row in the
2026-11-17 card, which carries the identical stale label. Nothing else. No table, stratum,
estimate, interval, certificate or snapshot byte changes; `release_summary.csv` and the
C7 card already state the correct binding.

What is not done: the card files are not edited. The release is tagged, and rewriting a
shipped file would leave the published bytes disagreeing with the tag. A reader should
take the protocol version from this note, from `certificates/2026-11-19/C7.json`, or from
`reda-protocol.md` itself, and treat the card row as stale.

Root cause and fix: `tools/export_public.py` formatted the version as a literal. It now
reads the version and the file hash out of `reda-protocol.md` at export time, so the card
cannot drift from the protocol again. The fix applies to exports after this note; it does
not retroactively change the two cards already published.
