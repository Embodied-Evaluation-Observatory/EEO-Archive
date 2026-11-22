# Reproduction invitation

Layer 1 and Layer 2 certificates in this archive are issued by the maintainer. Layer 3 —
"an outside party re-ran the check and got the same numbers" — cannot be self-issued. This
file is the request, and the procedure, for anyone willing to do it.

## What to run

```
git clone https://github.com/Embodied-Evaluation-Observatory/EEO-Archive.git
cd EEO-Archive
python3 tools/verify_public.py --release 2026-11-17 \
    --input releases/2026-11-17/robocurve_allruns.json
python3 tools/preflight.py --release 2026-11-17 \
    --input releases/2026-11-17/robocurve_allruns.json --zenodo-dir <path to deposit copy>
```

The first command recomputes the published summary from the published attempts and
compares hashes. The second adds the deposit check and the certificate chain; without a
local copy of the deposit it blocks that item by design and says so.

## What to report

- `verify_public.py` output, verbatim, and the exit status.
- the machine: OS, Python version, and whether the checkout was clean (`git rev-parse HEAD`,
  `git status --porcelain`).
- anything that differed, including differences you consider cosmetic.
- whether you consent to being named in `governance/verification_partners.csv`; if not, the
  run can be recorded as an anonymous independent check.

## Where it goes

A completed run is recorded in `governance/verification_partners.csv` with date, scope
(L1 / L2 / L3), and the outcome. No partner rows exist as of this release; the file carries
only its header. That is a fact about the archive, not a placeholder to be filled in with
friendly-sounding entries.

## What it does not cover

Reproduction confirms that the published tables follow from the published attempts and that
the deposit matches the release. It does not confirm that the attempts reflect the original
evaluations — that requires source access the archive does not have. A Layer 3 check is
therefore a statement about the arithmetic chain, and is described that way wherever it is
cited.
