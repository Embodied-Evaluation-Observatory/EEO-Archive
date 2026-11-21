# Auditing a loop that evaluates itself

This archive was built to look at records after they were frozen: attempts, cells, rho,
intervals. In embodied evaluation the thing being audited is moving inside a closed loop,
where a policy is scored by a judge that is itself being improved, and where the scores feed
straight back into what gets trained next. Asking whether the numbers are distinguishable
still matters there. What changes is the object, the timing, and what a signal is allowed to
do.

## What transfers, and what becomes a different question

Multiplicity correction, design effect, and zero-variance separation are statements about
identifiability, not about people or benchmarks. They survive the change of setting. What
does not survive is the unit.

| After the loop closes (this archive) | Inside the loop |
|---|---|
| one row per attempt, one cell per model-task | one row per episode, plus judge id, judge version, policy version, curriculum stage |
| rho measured over repeated attempts in a cell | rho over repeated episodes scored by judges that are themselves changing |
| zero-variance means the cell cannot separate policies | zero-variance may mean the judge has stopped being able to see a difference, or the curriculum has stopped producing one |
| intervals computed once, published | intervals must be recomputable at each checkpoint, or the signal arrives too late to matter |

The same arithmetic, applied to different columns. That is the point: the tools are not
obsolete, the input schema is.

## Three failure modes worth measuring

These are testable with logs, not with internals.

1. **Correlated judging.** When several evaluators score overlapping episodes, agreement
   between them is not evidence of correctness; it can be shared bias. Measure the
   correlation matrix over shared episodes and report the effective number of independent
   judges, not the count of judges. Two judges at 0.95 agreement are closer to one judge
   than to two.
2. **Skill-library saturation.** A skill library that keeps growing while its success rate
   sits pinned at the ceiling is not accumulating capability; it is accumulating
   confirmations. Zero-variance across a skill family, with no failure exploration recorded
   anywhere in the logs, is the signal. The question "was this ever attempted under
   conditions where it failed" is answerable from logs.
3. **Suite pruning without a record.** Automatic suite construction can cut a large
   fraction of the evaluation surface while keeping rank correlation with human ordering.
   That number is a compression result, not a coverage result. The audit question is which
   dimensions were dropped and whether any dropped dimension was distinguishable in the
   first place. A dropped dimension that no policy could separate is cheap to lose; one that
   separated policies is the whole point of the suite.

## The signal must not be consumable as a reward

A verifier that returns a number inside the loop becomes a target. This is not a moral
observation, it is a mechanical one: anything the policy can observe and optimise against
will be optimised against, including a statement like "these two policies are
indistinguishable".

Therefore:

- the audited signal is published on a slower cadence than the training loop;
- it is not exposed as a per-episode score the policy can climb;
- it reports properties of the comparison (how many pairs are separable, at what sample
  size), not a scalar to maximise;
- it is versioned and dated, so a later reading can tell what the loop knew when.

This is the "fast loop explores, slow loop consolidates" split, stated as a constraint
rather than a slogan: the fast loop is allowed to be entirely automated; the slow loop has
to remain outside the fast loop's optimisation surface, or it stops being an audit.

## What the archive can and cannot do here

Can, given logs: recompute identifiability at a checkpoint; measure judge agreement and
effective judge count; detect ceiling-pinned families; record which dimensions a compressed
suite dropped; compare a reported rank correlation against a recomputed one.

Cannot: inspect a judge's internals, certify safety, decide whether a curriculum is
pedagogically sound, or tell whether a policy "really" learned a skill rather than
exploiting a scorer. Those need evidence the archive does not have and should not pretend
to.

## A schema to ask for

The minimum that makes an in-loop audit possible, one row per episode:

`episode_id, task, policy_version, curriculum_stage, judge_id, judge_version, score,
outcome, attempts_within_cell, timestamp_minute, skill_id (if a skill library is involved)`

Without `judge_id` and `judge_version` the correlated-judging question cannot be asked. Without
`curriculum_stage` the saturation question cannot be asked. These two fields are the
difference between auditing a loop and auditing a table.

## Status

No in-loop dataset has been received as of 2026-11-21. Everything in this file is a
specification, not a result. It is written down so that a party who wants this check knows
what to send, and so that the archive does not later claim it always had the method.
