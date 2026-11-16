# Claim certificates

A certificate is not a ranking and not a performance result. It is a statement about an
existing measurement: a named estimator, applied to named bytes under named assumptions,
yields a stated number and a stated discernibility resolution.

## What each certificate carries

| field | meaning |
|---|---|
| `claim.claim_level` | `established-by-us` / `imported-cited` / `hypothesis`; the three levels are never mixed in one sentence |
| `input.file_sha256` | the exact bytes the number was computed from |
| `assumptions[]` | every assumption, each with an anchor into the protocol or marked `none` |
| `assertions[]` | each number, its interval, and `verified` / `withdrawn` / `superseded` |
| `resolution.delta_star` | the smallest difference the recorded design can distinguish |
| `not_certified[]` | what the certificate deliberately does not cover |
| `certificate_hash` | sha256 over the canonical JSON excluding this field |

## How to check one

```
python3 tools/verify_certificate.py --cert certificates/<release>/C2.json
```

Exit 0 means: the certificate content is unedited, the input bytes still match their signed
hashes, every asserted number recomputes within tolerance, and the resolution follows from
the design it records.

## Two things this format deliberately does not claim

1. A valid certificate does not make the underlying measurement true. It says the number
   follows from the assumptions. If an assumption is wrong, the certificate is still valid
   and the conclusion is still wrong.
2. Corrections do not delete. A withdrawn claim keeps its file and is marked `superseded`
   in `index.json`, with the reason and the id that replaces it.

## Known limit of the numeric check

A one-byte tamper in `attempts.csv` moves the pooled rho by about 0.0005, which is inside the
0.0006 tolerance. The numeric comparison would pass; only the sha256 gate fails. That is why
the hash gate is the first check and the tolerance is a secondary sanity check, not the
primary protection.
