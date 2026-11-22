# Certificate layers

A single certificate hides a question: verified against what? This archive issues
one certificate per release with three independent layers, so a reader can see
which claim is backed by which evidence.

| Layer | What is verified | Who can check it | Cost |
|---|---|---|---|
| L1 | The published summary reproduces from the published tables | anyone, from the repository alone | one command, seconds |
| L2 | The source bytes held locally hash to the value in the manifest | anyone holding the same bytes | one command, seconds |
| L3 | The source snapshot is redistributed, so an outsider can redo the export from source | anyone, from the repository alone | one command, minutes |
| — | Source record completeness, upstream measurement validity | nobody through this archive | out of scope |

## Issue or re-check

```
python3 tools/certify.py --release 2026-11-17
```

Writes `certificates/<release>/layers.json`, which records each layer's status,
the measured and declared hashes, the protocol file hash, and an explicit
`not_certified` list.

To check the committed certificate instead of writing a new one:

```
python3 tools/certify.py --release 2026-11-17 --check
```

This writes nothing. It recomputes the hash over the file's own content and
recomputes L1/L2/L3 from the same bytes; exit 0 means the certificate on disk is
the certificate that was issued for these inputs. `tools/preflight.py` uses this
form, because a gate that reissues the certificate it checks cannot notice a
change to it.

## Current state

| Release | L1 | L2 | L3 |
|---|---|---|---|
| 2026-11-17 | reached | reached | reached |

L3 is reached for this release because the snapshot is redistributed with it.
Where upstream terms forbid redistribution, a release can reach L2 only; the
certificate then states that plainly instead of implying a check nobody outside
can perform.

## Reading a layered certificate

L1 alone means the arithmetic is honest and the archive's own derivation is
reproducible. It says nothing about whether the source recorded every case.
L1 + L2 means the specific bytes named in the manifest are the bytes used.
L1 + L2 + L3 means an outside reader can rebuild the published tables from the
source and compare. None of the three says the benchmark measures what it claims
to measure.
