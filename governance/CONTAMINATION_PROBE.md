# Contamination probe: the operational protocol for check 5

Five provenance checks are named in `reda-protocol.md` section 5. Check 5 asks whether a
model's result rests on having seen the evaluation items. This page is its operational form:
what a probe can decide, how to run one so the answer means something, and what a result
does not license.

A probe returns a number and an interval. It never returns "contaminated".

## 1. The claim a probe tests

Two things look identical from the outside and must be kept apart:

- **surface memorisation** — the model has seen these items, or items near-identical in
  surface, and reproduces answers from memory rather than from the instruction and scene;
- **distribution similarity** — the model is genuinely good at tasks that look like these.

A probe can separate the first from the second only in the direction surface perturbation
allows. It cannot establish the absence of leakage in a family it did not perturb, and it
cannot see inside a closed model. Everything below is written to make that limit explicit
rather than hidden.

## 2. Why a score drop is not evidence

Perturbing a task makes it harder for everyone. A model scoring 0.80 on the original items
and 0.61 on perturbed ones has lost 0.19; that number alone is a difficulty statement, not a
contamination statement. The signal is the **excess** loss: how much more a model loses than
a model known not to have seen the items loses on the same perturbed cells.

    delta_m   = score(perturbed, m) - score(original, m)          per cell, then averaged
    delta_ref = score(perturbed, ref) - score(original, ref)      same cells, same harness
    Delta_m   = delta_m - delta_ref                               the excess loss

`Delta_m` near zero means the model behaves like something that never saw the items.
`Delta_m` clearly negative means it lost information that the reference model kept — which is
what memorisation looks like when the surface it memorised is removed.

The reference model is not optional. Without it the design cannot tell difficulty from
contamination, and a probe without a reference is a difficulty measurement wearing a
contamination label.

## 3. Perturbation families

Each family removes a different channel. They are reported separately, never pooled, because
they answer different questions.

| Family | What changes | What it detects | What it does not |
|---|---|---|---|
| P1 surface | colours, textures, asset identities, object placement within the same scene, prompt wording order, label names | memorised surface: the model keyed on appearance rather than on the task | leakage of the answer distribution itself |
| P2 paraphrase | instruction rewritten with the same meaning, example reordered, same answer required | memorised instruction strings and template matching | memorised visual scenes |
| P3 reseed | new instances from the same generator and task definition, fresh seeds | instance-level leakage, seeds seen during training | memorisation of the whole generator family |
| P4 time shift (optional) | items drawn after a declared cutoff date | training-set leakage where the cutoff is known and honoured | anything, where the cutoff is unverifiable |

A probe that runs P1 only, and reports null, has said something about surface appearance and
nothing about instruction strings or instance seeds. The report must name the families run.

## 4. Validity requirements for a perturbed set

A perturbed set that fails any of these is not a probe; a null result from it is
uninterpretable.

1. **Label preserved.** The correct outcome for every perturbed cell equals the correct
   outcome for its original cell. Verified by a second person, cell by cell, on a sample of at
   least ten cells, with disagreements resolved before the run.
2. **Difficulty not moved beyond tolerance.** The reference model's own drop `|delta_ref|`
   must sit inside a pre-registered tolerance. Exceeding it means the perturbation changed the
   task, not the surface, and the set must be rebuilt rather than analysed with a correction.
3. **Perturbation applied by someone other than the model's owner**, and the per-cell diff
   recorded, so the transformation is reproducible and auditable by a third party.
4. **Commit, then reveal.** Before the run, publish the sha256 of the perturbed set and its
   cell count. Publish the set itself only after the run completes. A perturbed set circulated
   in advance is a new training opportunity and defeats the check.

## 5. Controls

| Control | Requirement | Consequence if missing |
|---|---|---|
| Reference model | open weights, run locally, no plausible exposure to the items, same harness and same attempt count as the model under test | the excess loss is undefined |
| Positive control | a model deliberately trained on a stated number of original-surface items, built locally for this purpose, run on the same cells and harness | a null result proves the probe is insensitive, not that the model is clean |
| Harness identity | identical attempt count per cell, identical success criterion, identical scoring code, hash recorded for both variants | the difference mixes harness drift with contamination |

The positive control is the part that is usually skipped and is the reason this check is
expensive. It must be published as a **description** — architecture, number of training items,
procedure — and not as weights: releasing a model trained on the probe's original items hands
out the leakage the probe exists to detect. A probe whose positive control fails to show a
negative `Delta` has failed as an instrument; report that, do not report the model.

## 6. Decision rule

Pre-registered before the run, written into the plan, not chosen after seeing the numbers:

1. Smallest excess loss worth detecting, `Delta_min`, fixed before the run and written into
   the plan. Refuse to run below 0.05: the cell count grows with the inverse square of the
   target, so a smaller `Delta_min` is not a stricter probe but an unaffordable one.
2. Cell count from the table in section 7 at the ρ assumed for this fleet, taking the
   conservative rung as `governance/SAMPLE_BUDGET_SURFACE.md` requires.
3. Test: cell-paired difference `Delta_m` with a cluster bootstrap interval resampling cells,
   one-sided at the pre-registered level. Flag when the interval excludes zero and
   `|Delta_m| >= Delta_min`. Report the interval either way.

Three outcomes, all of them numbers:

| Outcome | Reading | Not a reading |
|---|---|---|
| interval excludes zero, `|Delta| >= Delta_min`, positive control passed | the model lost more than the reference did when the surface was removed | anything about which item reached training, or about intent |
| interval includes zero, positive control passed | no excess loss detected at this resolution | clearance: the families run were the families tested |
| positive control failed | the probe cannot see memorisation at this resolution | a statement about the model |

A flag is a prompt for the record's owner to respond, with the same standing as the other
four checks: a number and a flag, never a deletion.

## 7. Cells needed

Conservative closed form, used because it ignores the pairing benefit and therefore
overstates the requirement rather than understating it. For a two-series comparison of
proportions with intraclass correlation ρ and J attempts per cell:

    sigma2 = p(1-p) * (1 + (J-1) rho) / J
    cells  = ceil( 2 * sigma2 * ((z_0.95 + z_0.80) / Delta_min)^2 )

at one-sided alpha = 0.05 and power 0.80. Worst case `p = 0.5`:

| J | rho | cells for Delta_min = 0.05 | 0.10 | 0.20 |
|---|---|---|---|---|
| 20 | 0.1 | 180 | 45 | 12 |
| 20 | 0.3 | 415 | 104 | 26 |
| 20 | 0.5 | 650 | 163 | 41 |
| 10 | 0.1 | 235 | 59 | 15 |
| 10 | 0.3 | 458 | 115 | 29 |
| 10 | 0.5 | 681 | 171 | 43 |

At `p = 0.8` the requirement falls by about a third: 266, 67, 17 cells at J = 20 for rho = 0.3
and Delta_min = 0.05, 0.10, 0.20.

Worked budget: 4 models (3 panel + 1 under test), 2 variants, J = 20, rho = 0.3,
Delta_min = 0.10 → 104 cells × 8 series × 20 = 16,640 attempts. Probe cost is dominated by the
`Delta_min` chosen: halving it quadruples the run.

## 8. When to run

Not on every release. A probe is triggered when:

- a submitted score exceeds the current frontier by more than the published discernibility
  interval, so the claim is the one worth testing;
- a model's report does not state its training data provenance;
- the record's owner asks for it.

Running it on every model in a table buys nothing: the check exists for claims that move a
ranking, and each run costs weeks of field time.

## 9. What this protocol does not claim

- It does not certify that a model is uncontaminated. It reports excess loss for the
  families, cells, and resolution it ran.
- It does not attribute intent. A negative `Delta` is consistent with memorisation, with
  training on a near-duplicate corpus, and with a benchmark whose answers are inferable
  without exposure; the report names the possibilities and does not choose among them.
- It does not rank. The statistic compares a model with a reference on the same cells and
  says nothing about capability in general.
- It does not replace checks 1 to 4. Share concentration, temporal clustering, pairwise
  consistency and selective submission remain separate evidence, and a clean probe does not
  clear a concentrated submitter.

## 10. Recording sheet

`governance/pilots/contamination_probe_sheet.csv` carries one row per attempt, with the
variant family, the cell, the outcome, the harness hash, and the model's stated exposure.
Rows for the reference and both variants go in the same file, because the statistic is a
difference and separating them invites the difference to be computed across mismatched cells.

## 11. Status relative to the signed protocol

`reda-protocol.md` section 5.1 still reads "not implemented: no perturbed variant has been
run", and that text is not edited here. The protocol binds certificates by hashing its own
bytes (`tools/preflight.py`, check 5 of the gate), so an edit to section 5.1 would detach the
2026-11-17, 2026-11-18 and 2026-11-19 certificates from the text they were signed against.
The status row changes when a probe run exists to report, in a protocol revision issued with
new certificates — 1.3, not by editing 1.2.

What exists now: this protocol, its recording sheet, and a cell-count table anyone can
recompute. What does not exist: a run.
