#!/usr/bin/env bash
# End-to-end self-test on synthetic data: raw snapshot -> export -> verify -> diff.
# No third-party data is used, so anyone can re-run the whole pipeline in seconds.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 tests/fixture/generate.py
rm -rf tests/fixture/public
python3 tools/export_public.py --release 2026-01-01 --root tests/fixture --J 3
python3 tools/verify_public.py --release 2026-01-01 --root tests/fixture --J 3 \
        --input tests/fixture/releases/2026-01-01/robocurve_allruns.json

for f in attempts.csv cells.csv release_summary.csv quality_flags.json; do
  if ! diff -q "tests/fixture/public/2026-01-01/$f" "tests/fixture/expected/$f" >/dev/null; then
    echo "FAIL: $f differs from the committed golden output"
    diff "tests/fixture/expected/$f" "tests/fixture/public/2026-01-01/$f" | head -20
    exit 1
  fi
done
echo "PASS: fixture reproduces byte-for-byte and verification passes"

# Second stage: a benchmark that emits EvalLog records can reach the same table.
python3 tools/ingest_evallog.py --log tests/fixture/evallog/sample.jsonl \
        --release 2026-01-02 --root tests/fixture
rm -rf tests/fixture/public/2026-01-02
python3 tools/export_public.py --release 2026-01-02 --root tests/fixture --J 6 >/dev/null
python3 tools/verify_public.py --release 2026-01-02 --root tests/fixture --J 6 \
        --input tests/fixture/releases/2026-01-02/robocurve_allruns.json | tail -1
echo "PASS: eval-log ingest reaches a verifiable published table"
