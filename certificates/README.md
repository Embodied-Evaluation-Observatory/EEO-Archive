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

## Protocol revision and the certificate chain

The protocol was revised to ReDA-1.1 on 2026-11-17. Section 4 now states the cell requirement
in its finite-J form, and the counts published in the draft were low: 146 becomes 154 for
λ = 1e-2, 1,470 becomes 1,546 for 1e-3, and 1,470,904 becomes 1,546,000 for 1e-6. The draft
also quoted 30 cells for ρ = 0.01, a figure that holds only in the J → ∞ limit; at J = 20 the
count is 178. Section 3 now states that substituting n_eff into the Clopper–Pearson bound is
first-order, and reports a coverage simulation that came out conservative at all 36 grid
points.

No certificate number changes. C5 was superseded by C6 because the protocol text it anchors
to changed, not because its arithmetic did: ρ = 0.4909, 133 cells, 3,069 attempts, deff = 10.327,
n_eff = 1.937 and δ* = 0.4066 are identical in both. The reason string is in `index.json`.
