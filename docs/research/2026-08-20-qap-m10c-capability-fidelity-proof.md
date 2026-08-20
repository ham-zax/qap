# QAP Phase 17 M10-C Capability / Fidelity Proof

**Date:** 2026-08-20
**Milestone:** M10-C — Capability / Fidelity Proof
**Verdict:** **APPROVE M10-C**

## Baseline

This proof ran from:

- branch: `phase17-m10c-capability-proof`
- coordination baseline: `ac0cfbc97d5842161d75a47823b62ef7845e3608`
- M10-A integrated ancestor: `12ed08a` — typed Research Recipe, support preflight, compilation lineage
- M10-B integrated ancestor: `f39b4b4` — Research Cockpit, Experiment Lab, Product presentation

No production source was changed during the proof. The only repository deliverable is this report.

## Proof environment and method

The direct runtime proof used an isolated temporary Product workspace under `/tmp/qap-m10c-capability-proof-runtime`; it did not use or mutate the normal Product workspace.

The fixture declared two approved assets, `AAA` and `BBB`, with resolved Binance Spot identities and three real-orientation fixture markets:

- `AAA/USDT`
- `BBB/USDT`
- direct `AAA/BBB`

It published immutable `4h` and `1d` Product generations for the Swing horizon through `ProductMarketData.publish_generation`, then used the real ownership path:

```text
ProductUniverse
  -> ProductMarketData
  -> CurrentApprovedResearch
  -> ResearchRecipeService
  -> compile_research_recipe
  -> existing ExperimentManifest / policy owners
  -> existing run_experiment_to_artifacts
  -> existing final-OOS reservation authority
```

The resulting Product readiness was:

- horizon: `swing`
- `ready_for_research=true`
- approved/ready assets: `2`
- ready venue paths: `2`
- direct `AAA/BBB` market: `ready`
- safe cutoff: `2026-08-01T00:00:00+00:00`
- readiness ID: `0ca13e23e5c1c10355af01a6424de939a50508d3edf74683c33154f983c8bf9e`
- current-approved claim identity: `fa0cab29e54b19655841aa4235a0908a528c1ce6ddf563b6823264306ef1c145`

The exact `1d` data fingerprints consumed by the executed pair/final-OOS runs were:

| Dataset | Semantic fingerprint |
| --- | --- |
| `AAA/USDT` | `a84231eb6d6a150fddcbc75bfe9d1112c23dd8e25a543af89ce24bb139ee7333` |
| `BBB/USDT` | `7ab766fca6101d06829aad6990e7da543cbf0d3c8245531ff50af3c2153bd59f` |
| `AAA/BBB` | `f1acdc68373b20329597fed9568560fec4e5b3f06f7bba448aa5ffffd25fe263` |

A bounded Product rendering pass then launched the same isolated workspace on temporary loopback ports and inspected the integrated React application with `agent-browser`. The temporary servers and browser session were shut down after evidence capture.

No test files were created or modified, and no tests were run.

## Eight frozen cases

| # | Case | Expected core truth | Observed result | Disposition |
| --- | --- | --- | --- | --- |
| 1 | Rolling-residual pair | valid, executable, allowed; ready fixture can run | `valid / executable / allowed / ready / native`, `runnable=true`; ordinary run completed | PASS |
| 2 | Slow momentum | asset/policy semantics, not silently a pair-relationship model | Correct declaration is `relationship=none`, `decision_rule=slow_momentum_tilt`, runnable; putting that ID in relationship slot is `unknown_method` | PASS |
| 3 | Student-t Copula | known unimplemented, non-runnable; no false pair incompatibility | `capability=unimplemented`, `known_method_not_implemented`, nearest `residual_mean_reversion`; no pair/data incompatibility reason | PASS |
| 4 | Palazzi exact | short block + missing selection/risk + adaptation required, all preserved | simultaneous authority/capability/structure/fidelity reasons returned; non-runnable | PASS |
| 5 | Palazzi-inspired adaptation | distinct exact identity; adaptation lineage separate from final-OOS lineage | new recipe hash, `derived_from_recipe_sha256` points to exact declaration, no `selected_from_compilation_sha256` | PASS |
| 6 | Invalid final-OOS multi-variant | invalid and rejected before reservation | required single-precommitted-variant reason present; no commitment/registry entry created | PASS |
| 7 | Development `[A,B]` -> final `[A]` | different recipe hashes, same family, frozen compilation selection; sibling holdout protected | exact immutable lineage verified; sibling B preflight-runnable but runtime reservation rejects same family+holdout | PASS |
| 8 | Unknown method | unknown, non-runnable, no arbitrary dispatch | `capability=unknown`, `unknown_method`, `runnable=false` | PASS |

### 1. Current rolling-residual pair

The proof reduced the backend Product pair draft to the admitted `residual_mean_reversion` variant and a fixed selection.

Observed support:

```text
structure  = valid
capability = executable
authority  = allowed
readiness  = ready
fidelity   = native
runnable   = true
reasons    = []
```

Exact identity/evidence:

- recipe SHA-256: `a9918decb3ffc3da06c3d6b2020bea39d7c77918f1af80d0a5ed1242813e3607`
- family: `m10c-case1-residual`
- compilation SHA-256: `2e8e234746a3fa1787177e3e85d68bac2ace8854bd5945a82bc417accfe491a9`
- run: `run-c93b6fda930726f4c7142e0e`

This reached the existing ordinary experiment artifact path; the proof did not add another runner.

### 2. Current slow-momentum semantics

The correctly typed declaration used:

```text
relationship  = none
decision_rule = slow_momentum_tilt
allocation    = long_only_relative_tilt
```

Observed support was `valid / executable / allowed / ready / native`, `runnable=true`, with no reasons.

Recipe SHA-256: `0db6b6f9ad4ddd33514458aa7fd29a7469d87f1cbeef3a6a11010617d91cee07`.

A negative semantic probe then placed the same `slow_momentum_tilt` ID in the **relationship** slot. The backend returned:

```text
capability = unknown
runnable   = false
reason     = unknown_method
component  = variants.slow-momentum.relationship
```

This matches the integrated canonical owner in `qap.experiment.model_policies`: slow momentum is a decision policy over asset evidence and requires relationship `none`; it is not silently reclassified as a pair-relationship method.

### 3. Student-t Copula

The exact relationship declaration `student_t_copula` returned:

```text
structure  = valid
capability = unimplemented
authority  = allowed
readiness  = ready
fidelity   = native
runnable   = false
```

Typed reason:

- `known_method_not_implemented`
- component: `variants.student-t-copula.relationship`
- nearest capability: `residual_mean_reversion`

Recipe SHA-256: `90c924a722f984844b5c37dbf7e5f9b1e4deff128f7aff7d9181d07f9414f456`.

No `unsupported_research_object`, data-readiness, or pair-incompatibility reason was emitted. The truth is that current QAP does not execute the method; the selected pair itself was not blamed.

### 4. Palazzi 2025 exact-replication declaration

The proof manually declared the methodology source as `doi:10.1002/fut.70018`; no automatic paper interpretation was used. The typed recipe declared the nearest current relationship/signal path plus paper-required semantics that current QAP cannot reproduce exactly:

- relationship: `residual_mean_reversion`
- decision rule: `evidence_tilt`
- allocation: `long_short_spread`
- risk: `volatility_filter`, `adaptive_trailing_stop`
- selection: `grid_search`
- fidelity intent: `faithful_replication`

Observed axes:

```text
structure  = invalid
capability = unimplemented
authority  = constitution_blocked
readiness  = ready
fidelity   = adaptation_required
runnable   = false
```

All applicable blockers survived together:

- `known_method_not_implemented` — `long_short_spread`
- `requires_short_position`
- `requires_unimplemented_risk_overlay` — `volatility_filter`
- `requires_unimplemented_risk_overlay` — `adaptive_trailing_stop`
- `requires_unimplemented_parameter_selection` — `grid_search`
- `incompatible_component_combination` — current `evidence_tilt` allocation semantics do not admit the required long/short allocation
- `cannot_claim_faithful_replication`
- `adaptation_available`

Recipe SHA-256: `d98f2efc304d24da0645dacf726a7eba8474ca1a154ec026bb274534bc2280e9`.

The extra `structure=invalid` result is a truthful additional blocker, not a precedence collapse: current `evidence_tilt` admits different allocation semantics from the declared exact long/short methodology. The support report still preserved the independent authority, capability, and fidelity blockers required by M10-C.

### 5. Palazzi-inspired QAP adaptation

A separate long-only QAP adaptation used current executable residual/evidence-tilt semantics and explicitly declared `fidelity_intent=adaptation`.

Identity/lineage:

- exact-source recipe: `d98f2efc304d24da0645dacf726a7eba8474ca1a154ec026bb274534bc2280e9`
- adaptation recipe: `105390151d506838fc8de5c84b15ca3e838864c381faa13d7623926819c205fb`
- `derived_from_recipe_sha256=d98f2efc304d24da0645dacf726a7eba8474ca1a154ec026bb274534bc2280e9`
- `selected_from_compilation_sha256=null`

Observed support:

```text
structure  = valid
capability = executable
authority  = allowed
readiness  = ready
fidelity   = adaptation_required
runnable   = true
```

`runnable=true` does not claim exact replication. The independent fidelity axis says this is an adaptation, while the capability/authority/readiness axes say the separately declared QAP strategy is executable. Adaptation lineage is not reused as final-OOS selection lineage.

### 6. Invalid final-OOS multi-variant recipe

The proof first created a real immutable development compilation, then submitted a final-OOS recipe that still contained both variants `[A,B]`.

Observed support:

```text
structure = invalid
runnable  = false
```

Reasons included the required:

- `final_oos_requires_single_precommitted_variant`

and the additional truthful lineage consequence:

- `final_oos_requires_frozen_family_selection` — a multi-variant final recipe has no single exact selected variant to match to the frozen compilation.

Reservation evidence:

```text
final-OOS commitment count before = 0
final-OOS commitment count after  = 0
registry entries before           = 0
registry entries after            = 0
```

The invalid attempt therefore failed before final-OOS reservation/consumption.

### 7. Development `[A,B]` to final-OOS `[A]`

Development evidence:

```text
recipe_sha256      = bfb08fce6514e9d6a87fbe42ad4ab0087eafd504b1374e1db0403c7edde8cb4c
research_family_id = m10c-family-continuity
compilation_sha256 = 0e3d4d7c8f772aed8c6c7394d7423f77bb1da8dc54b201eba2f0c28f2a442616
variants           = [A, B]
run_ids            = [run-b001a0f0eaecda583465c0c9, run-0cdab23f030ba5f5c82fe7d4]
manifest_sha256    = [
  466ae72597f8306f923e1b07e60699251abf2fc845ff75bfae20bbafbae5134f,
  802b14ca0330e89bed16f0ae14664293436f67357e1ddc27dd0829e2dc116d7b
]
```

The immutable compilation read returned both stored manifests with `research_family_id=m10c-family-continuity` and exact variants `A` and `B`.

Selected final-OOS `A`:

```text
recipe_sha256                    = a5b390133263b7ea51a041aec7f2540bb6ad511c79fa0be312b57fe4e7896060
research_family_id               = m10c-family-continuity
selected_from_compilation_sha256 = 0e3d4d7c8f772aed8c6c7394d7423f77bb1da8dc54b201eba2f0c28f2a442616
compilation_sha256               = 7ef930d9547c70cf6484f4108c812c60b30409c560499702f80dd3f976cf8725
run_id                           = run-3912d584b7fba8f9f2382ef1
manifest_sha256                  = c8b0eee3b4a07ca210d666be40bb8eb1288a41878691e31863d31344ab4c1223
```

The exact development/final recipe hashes differ, while the stable family is identical. Final `A` support was fully runnable before execution.

The resulting final-OOS commitment was consumed exactly once:

- family: `m10c-family-continuity`
- holdout: `holdout-c46d80d9713b49da75ac3676`
- status: `completed`
- consumed: `true`

Sibling final-OOS `B` was also correctly preflight-runnable because it was predeclared in compilation `C`. Runtime then rejected it through the existing final-OOS authority:

```text
HoldoutAlreadyCommittedError:
final OOS holdout is already committed for research family
m10c-family-continuity: holdout-c46d80d9713b49da75ac3676
```

After the sibling attempt, the commitment set still contained only the single completed/consumed `A` commitment. The proof did not change final-OOS reservation logic.

### 8. Unknown method ID

A relationship component `m10c_unknown_relationship_v99` returned:

```text
structure  = valid
capability = unknown
authority  = allowed
readiness  = ready
fidelity   = native
runnable   = false
reason     = unknown_method
```

Recipe SHA-256: `c587c08324a179c0fdff6f7747233e96e2626beaddfd3ce0bf56318075384950`.

No dynamic import, plug-in lookup, or arbitrary dispatch was attempted.

## Product presentation proof

### Capability choices remain backend-described

The isolated Product API returned:

- `capability_catalog_version=qap.research-capabilities.v1`
- `default_recipe_version=qap.product.default-research-recipe.v1`

Rendered Experiment Lab controls reflected that catalog directly. Representative visible options included:

- relationships: `rolling_log_ratio_zscore · executable`, `residual_mean_reversion · executable`, `student_t_copula · unimplemented`
- decision rules: `evidence_tilt · executable`, `slow_momentum_tilt · executable`
- allocation: `long_only_relative_tilt · executable`, `long_short_spread · unimplemented`
- selection: `fixed · executable`, `precommitted_variants · executable`, `grid_search · unimplemented`, `walk_forward · unimplemented`

No React-side method registry was observed.

### SupportReport axes/reasons are independent and visible

With `student_t_copula` selected in Experiment Lab, the rendered support section showed:

```text
Not runnable
structure  valid
capability unimplemented
authority  allowed
readiness  ready
fidelity   native
```

It also rendered the backend reason `known method not implemented`, its component path, nearest current capability `residual mean reversion`, and the backend suggestion. `Run canonical recipe` was disabled.

After restoring the backend default executable relationship, the rendered support section changed to:

```text
Runnable
structure  valid
capability executable
authority  allowed
readiness  ready
fidelity   native
```

`Run canonical recipe` then became enabled. The browser did not infer run authority independently of the support result and canonical recipe.

### Exact operation result navigation

The positive Experiment Lab launch completed through operation:

- operation ID: `6226cc92-c613-490a-bebb-498c337320fe`
- kind: `run_research_recipe`
- status: `completed`
- compilation SHA-256: `80640bd59ab0557fb7aede864d703eb71c020e1c7c137bafc397d8ffb962a5b0`
- exact backend `run_ids[]`:
  - `run-0d4faf9526d0df2a6004fe21`
  - `run-22813eb0156578021c9570fa`

The rendered Product result block exposed exactly two links:

- `Exact result 1` -> `/experiments/run-0d4faf9526d0df2a6004fe21`
- `Exact result 2` -> `/experiments/run-22813eb0156578021c9570fa`

### Advanced recipe/compilation lineage remains inspectable

The experiment detail for `run-0d4faf9526d0df2a6004fe21` rendered technical provenance plus an integrity-verified Research Recipe lineage block:

- recipe SHA-256: `ef97cb5c460b0545e7d63c71e216bc302f69c541441f8499b94fe740e061052c`
- compilation SHA-256: `80640bd59ab0557fb7aede864d703eb71c020e1c7c137bafc397d8ffb962a5b0`
- compiler: `qap.research-recipe-compiler.v1`
- capability catalog: `qap.research-capabilities.v1`
- selected-from compilation: `none`
- derived-from recipe: `none`
- exact run manifest: `df743b9986ce78d379a5910744e4d193d89b200bf30c826d849baee73183f1f4`
- ordered sibling manifest list also included `6ab018aa8c0aa098f3fe90bd5403adb5728418dd76bee6e38b0a86bd52f84719`

The Product copy identifies this as audit lineage rather than a second scientific verdict.

### Manual recipe runs do not become scanner Research Ideas

After the direct and Product-launched recipe runs, `/api/history` returned:

```text
research_generation_count = 0
research_idea_count       = 0
```

The six completed manual/recipe experiment runs were present under `other_research_runs`, including families:

- `m10c-case1-residual`
- `m10c-family-continuity`
- `product-pair-cc9803e48ab471ede836258c4cf1e1c2`

Rendered History likewise showed `No completed research generations are available yet` and listed these runs under `Unowned QAP research runs`. Manual Experiment Lab evidence therefore did not manufacture scanner Research Ideas.

### Universal Scan remains scanner-owned

The rendered Research page keeps `Scan my universe` as a separate Product section from `Experiment Lab`.

The integrated client wiring remains distinct:

```text
Universal Scan:  /api/product-research
Experiment Lab:  /api/research-recipes/run
```

`ProductResearch.tsx` calls `runProductResearch`; `ExperimentLab.tsx` calls `runResearchRecipe`. No recipe compiler was inserted into the Universal Scan path.

## Protected-boundary checks

This milestone did not change production source. In particular it did not change:

- `qap.experiment.manifest` scientific contracts;
- `qap.experiment.model_policies` or basket policy owners;
- scanner protocol, candidate generation, replay, promotion, or Research Idea ownership;
- final-OOS reservation/permit/consumption behavior;
- immutable generation/provenance semantics;
- economic replay/backtester behavior;
- live/private trading authority.

It also did not add Copula, Palazzi, another method, a plug-in architecture, a second backtester, focus-scan mechanics, or private exchange execution.

## Deviations and defects

No blocking production defect was found.

Two cases returned additional truthful reasons beyond the minimum frozen acceptance text:

1. Palazzi exact returned `structure=invalid` / `incompatible_component_combination` because the current executable `evidence_tilt` policy does not admit the paper-required `long_short_spread` allocation. The independent shorting, missing-risk, missing-selection, and fidelity blockers were all still preserved.
2. The invalid multi-variant final-OOS recipe returned `final_oos_requires_frozen_family_selection` in addition to `final_oos_requires_single_precommitted_variant`, because a two-variant recipe has no single exact variant that can be matched to the frozen development selection.

Neither behavior hides or weakens a frozen truth, and neither requires production remediation for M10-C.

## Validation actually run

The proof used only acceptance/evidence commands required by M10-C:

- deterministic direct runtime fixture through existing Product/recipe/experiment/final-OOS entry points;
- immutable compilation reads and final-OOS commitment inspection;
- focused source inspection of canonical policy/capability/Product ownership;
- isolated loopback API/Product rendering with `agent-browser`;
- focused API reads for operation, capability context, and History ownership;
- final docs-only `git diff --check` and Git diff/status inspection.

**No tests were created, modified, or run.** No broad test, lint, typecheck, or build suite was run.

## Verdict

**APPROVE M10-C.**

The integrated M10-A/B machinery distinguishes capability, authority, readiness, fidelity, structure, and lineage without collapsing them into one verdict; protects the existing final-OOS family/holdout authority; and keeps Product presentation subordinate to backend truth.

## M10-D human handoff

No M10-C product defect blocks the representative-user acceptance work. After this proof is accepted/integrated, M10-D can run the human-led tasks already frozen in the Phase 17 plan. Representative users must be asked, without developer coaching, to:

1. find exact `W` without substring hunting;
2. start `W / BTC` Pair Research;
3. run and explain `Scan my universe`;
4. open Experiment Lab and determine whether a named method/recipe is supported;
5. explain the difference between method unsupported, pair/data not ready, QAP-constitution blocked, and valid negative research;
6. inspect a paper recipe's relationship evidence, decision rule, allocation/rebalance, risk, selection/tuning, benchmark, and OOS declaration;
7. distinguish exact replication from a QAP adaptation;
8. distinguish model/evidence from economic replay and later/current evidence;
9. recover from identity/data setup without needing provenance vocabulary;
10. distinguish approved assets from data-ready assets;
11. distinguish Product current-approved research from strict historical PIT;
12. explain a hypothetical-capital assessment;
13. answer correctly that QAP does not recommend, authorize, or place live trades.

M10-D remains human-led: this proof does not fabricate participant reactions, comprehension scores, or usability metrics. Any protected-concept misunderstanding in M10-D returns to design review rather than moving scientific meaning into React.
