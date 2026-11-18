# Release gate

Written after record `24288113`: a deposit was published whose metadata described the
2026-11-18 release while its files were still the 2026-11-15 set, because the upload
happened before the files were replaced. Zenodo does not allow published files to be
edited, so the record had to be superseded. The gate exists so that cannot happen again.

## Rule

No release and no deposit is published until `tools/preflight.py` exits zero and writes a
record next to the release. A gate record is a file, not a claim.

## Order

1. Commit and push the tables. Confirm `main` carries what you think it carries.
2. Create the tag and the draft release, but do not publish it. Upload the assets to the
   draft: the snapshot, the public tables, the certificates, the board summary, the
   protocol.
3. Upload the same set to the Zenodo draft. Do not press Publish.
4. Download the files back from the draft into one folder. This is the point of the gate:
   hash what the deposit actually serves, not what you remember uploading.
5. Run:

```
python3 tools/preflight.py --release 2026-11-17 \
  --input releases/2026-11-17/robocurve_allruns.json \
  --zenodo-dir ~/Downloads/zenodo-draft \
  --out releases/2026-11-17/preflight.json
```

6. All six checks must read `PASS`. If any reads `BLOCK`, fix the files and upload again
   to the still-unpublished draft; nothing is public yet, so nothing has to be superseded.
7. Publish the GitHub release, then the Zenodo deposit, in that order, so the deposit's
   related identifiers point at a tag that already exists.
8. Commit the gate record. Cite the DOI it records.

## What the checks mean

| Check | Blocks when |
|---|---|
| manifest | the frozen snapshot on disk differs from its recorded bytes or sha256 |
| public tables | a published file is missing, altered, or not listed in checksums.txt |
| recompute | `verify_public.py` cannot reproduce the summary from attempts.csv |
| certificates | fewer than L1, L2, L3 are reached |
| protocol binding | the C7 protocol hash differs from the current `reda-protocol.md` |
| deposit files | a file downloaded from the deposit differs from the release, or cannot be checked |

The last check is the one that would have caught `24288113`. It refuses to pass when
nothing was downloaded, so an unverified deposit cannot slip through on a technicality.

## Limits

The gate checks that the deposit serves the bytes the release publishes. It does not check
that the release is statistically sound, and it does not replace a reader re-running the
tooling. It also cannot see a deposit that was published in the past; those records are
listed in `governance/RELEASE_PROTOCOL_MAP.md` with their status.
