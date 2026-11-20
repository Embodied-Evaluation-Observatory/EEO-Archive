# Attribution and category, release 2026-11-17

ReDA says how much of a difference may be noise. It does not say what the noise is made of.
This document defines the layer that would, and states plainly how much of it exists today.

## The three buckets

Every source of variance in these records falls into one of three buckets, and they are
fixed by different actors:

| Bucket | Examples in the current records | Who can fix it |
|---|---|---|
| Harness / engine | physics engine contact thresholds, collision margins, rendering artifacts, simulator version drift | benchmark maintainer |
| Protocol | reset cost, episode length, safety interruption, operator intervention, re-grading with a changed rubric | benchmark maintainer |
| Task composition | which tasks exist, how hard they are, how many of each | benchmark author, not fixable after publication |

The current release cannot split rho across these three. It records proxies:
`has_log`, `video_count`, `replacement`, `rerun`, `grading_method`, `source_tag`, `mode`.
None of them identifies an engine artifact.

## What the literature already shows

SimuGuard (arXiv 2610.41857) traced failure on RoboTwin to a single PhysX parameter:
geometry reported as penetrating roughly 2 cm when parts were 1–2 cm apart, objects then
ejected at metres per second. Changing that one constant took artifact episodes from 12/100
to 0 and lifted five container tasks from 89% to 98%.

That is the shape of the layer this archive lacks: a failure that is 100% attributable to
the harness, discovered by inspecting episodes, not by re-estimating a correlation. It also
sets the standard of proof — a named mechanism, a changed constant, a measured recovery.
Anything weaker is a hypothesis.

## What can be probed now, without new data

The 104 cells at 0% are the right first probe: "always fails" admits only policy, harness,
or impossible task, and no correlation analysis is needed to separate them. Available
signals are thin — `has_log` and `video_count` say whether an episode exists, not what
happened in it. So the probe answers coverage, not cause:

```
python3 tools/sensitivity.py --release 2026-11-17   # frontier counts by benchmark
```

Nine of the 106 zero cells have 30 or more attempts, which is enough repetition for a
"never succeeded" claim to be stable; it is not enough to say why.

## Category: what must not be compared at all

Two numbers can be statistically separable and still not comparable, because they sit on
different causal layers:

- execution layer — contact force tracking, impedance error, cycle time, on a controlled
  arm;
- decision layer — end-to-end task success on a learned policy.

An industrial force-control spec and an embodied success rate are not two estimates of one
quantity. Reporting them side by side, with overlapping or non-overlapping intervals, invites
a comparison that no interval can license. The archive's rule is therefore a tag, not a test:

```
incomparable: <layer_a> vs <layer_b> — different causal layer, no common estimand
```

Applied to this release: no cross-layer comparison is published, and none should be added
until a mapping states what the common estimand would be. Absent a mapping there is none,
and saying so is the correct output.

## Real-machine gap

All records here come from simulation or controlled benches. Real-machine noise —
reset cost, safety stops, operator intervention, hardware drift — has a different structure,
and no audit tool in this archive addresses it. Benchmarks and paper repositories that
publish per-trial real-robot logs are the only route in; until one is ingested, this gap
stays open and is stated here rather than papered over.
