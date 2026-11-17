# Licence for data and derived tables

This repository's data is released in three blocks. They are not interchangeable.

## Block 1 — our compilation, CC-BY-4.0

The table structure, the de-identification, the anonymous device ids, the stratum
estimates, the design-effect and effective-sample columns, the summary rows, the
dataset cards, and the protocol specification are released under the Creative Commons
Attribution 4.0 International licence (CC-BY-4.0).

Attribute as: `EEO Archive, release <id>. Embodied Evaluation Observatory.`

## Block 2 — source records, source terms

The per-attempt result fields — model, task, scene, outcome, score, and the
configuration fields — originate in the public archive named in each
`provenance/<release>.md` and each `public/<release>/DATASET_CARD.md`.

Their rights remain with the source. This repository cites them as facts, not as
licensed content, and grants no rights over them. Anyone redistributing those fields
must comply with the source's terms, which may differ from CC-BY-4.0.

Release 2026-11-15 redistributes no source bytes: only hashes are published, so a
holder can verify a copy. From 2026-11-17 the snapshot is redistributed as a cited copy
under block 4, which is the single exception to this rule.

## Block 3 — quoted text

Where a dataset card quotes the source's own rule (for example its exclusion criteria),
the text is quoted, not asserted. Quotation does not make it our claim or our licence.

## What is not claimed

No licence here covers any third-party log file, video, or image. Those are not
redistributed. Only their availability is reported, as two flags: whether a log exists
and how many videos were attached.

## Block 4 — redistributed source snapshot (from 2026-11-17)

`releases/2026-11-17/robocurve_allruns.json` is a copy of a third-party public snapshot,
published so that the export step can be re-run by any reader. It is **not** relicensed
here: the fields remain the source's facts, and redistribution follows the source site's
terms. The archive's own contribution — table structure, de-identification, estimates —
is covered by block 1.

If a source withdraws redistribution permission, later releases stop carrying the copy
and this block records the change; earlier releases are not rewritten, and the hash in
their manifests still identifies the bytes concerned.
