#!/usr/bin/env python3
"""Validate a PEV record or a receipt against the schemas in this directory.

Usage:
    python3 validate.py <record.json> [pev|receipt]

The type is inferred from the file when omitted: a record carrying `pev_id` is PEV,
one carrying `receipt_id` is a receipt. Exit code 0 on conform, 1 otherwise.
"""
import json
import os
import sys

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    sys.exit("jsonschema is required: pip install jsonschema")

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMAS = {"pev": "pev-record.schema.json", "receipt": "receipt.schema.json",
               "logmin": "eval-log-min.schema.json"}


def infer(doc):
    if isinstance(doc, list):
        return "logmin"
    if "pev_id" in doc:
        return "pev"
    if "receipt_id" in doc:
        return "receipt"
    return None


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    doc = json.load(open(path, encoding="utf-8"))
    kind = sys.argv[2] if len(sys.argv) > 2 else infer(doc)
    if kind not in SCHEMAS:
        sys.exit(f"cannot infer record type for {path}; pass pev, receipt or logmin")

    schema = json.load(open(os.path.join(HERE, SCHEMAS[kind]), encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))

    if not errors:
        print(f"OK  {os.path.basename(path)}  ({kind})")
        return 0
    print(f"FAIL  {os.path.basename(path)}  ({kind})  {len(errors)} error(s)")
    for e in errors:
        where = "/".join(str(p) for p in e.path) or "<root>"
        print(f"  at {where}: {e.message}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
