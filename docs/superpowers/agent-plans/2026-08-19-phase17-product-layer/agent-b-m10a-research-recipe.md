# Agent B — M10-A Typed Research Recipe + Capability Preflight

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** executable backend / API / immutable lineage
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m10a-research-recipe`
**Branch:** `phase17-m10a-research-recipe`
**Isolation reason:** Agent A concurrently performs read-only M10-B reconnaissance on stable `main`; M10-A is the only writer and must not mutate the read-only baseline.
**Can start:** immediately after the Wave-12 coordination base is committed and this worktree is created
**Depends on:** M10-0 approved at the Wave-12 coordination base; Agent B reconnaissance against `052aaaf`
**Execution lifetime:** persistent-agent-loop required
**Developer visibility:** headless; report progress/checkpoints without treating steering as a stop

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M10-A is authoritative
- `docs/research/2026-08-20-qap-research-cockpit-investigation.md`
- `docs/plans/07-experiments-controls-and-research-protocol.md`
- current `qap.experiment` manifest/provenance/artifact/final-OOS owners
- current Product current-approved readiness and immutable-generation owners

Before the first mutation apply:

`causal-coding → ponytail → mcp-harness-router → mcp-harness-local`

Testing remains opt-in. Do not create, modify, or run tests unless explicitly authorized or independently mandatory.

## Objective

Implement the smallest typed research-recipe boundary above the existing experiment engine so QAP can answer **before execution** whether one declared `pair | fixed_basket` recipe is structurally valid, executable, authority-compatible, ready, and faithful to its declared methodology, then compile only legitimate recipes into ordinary existing `ExperimentManifest` objects and preserve immutable recipe/compilation lineage.

Do not build another research engine. Recipe code stops at validated current `ExperimentManifest` objects; the existing runner, controls, economics, artifacts, and final-OOS reservation remain authoritative below that point.

## Frozen M10-0 contract

### Executable research objects

Only:

- `pair`
- `fixed_basket`

Universal Scan remains under existing scanner authority. Focus Scan is not part of this mission.

### Exact recipe identity versus family continuity

`recipe_sha256` is the exact semantic execution identity and must include compilation-affecting immutable data semantics such as role, selected/precommitted variants, exact evaluation/holdout semantics, exact Product generation/data bindings, and direct execution-market binding where relevant.

`research_family_id` is a stable QAP family-continuity anchor and is **not derived from `recipe_sha256`**.

The required continuity example is:

```text
development recipe [A,B]
  exact recipe_sha256 = X
  research_family_id = FAMILY
  compilation_sha256 = C

selected final-OOS recipe [A]
  exact recipe_sha256 = Y
  selected_from_compilation_sha256 = C
  research_family_id = SAME FAMILY
```

A final-OOS recipe must prove that its one selected variant was predeclared in the referenced immutable exploratory/development compilation. Family ID equality alone is insufficient proof.

`derived_from_recipe_sha256` remains reserved for a scientifically different adaptation and must not be reused for final-OOS selection lineage.

### SupportReportV1

Backend truth remains compositional:

```text
structure: valid | invalid
capability: executable | diagnostic_only | unimplemented | unknown
authority: allowed | constitution_blocked | claim_incompatible
readiness: ready | needs_setup
fidelity: native | faithful_replication | adaptation_required | not_applicable
runnable: boolean
reasons[]
suggestions[]
```

Return all applicable reasons. Do not invent precedence by collapsing these axes to one backend status.

Required final-OOS reasons include:

- `final_oos_requires_single_precommitted_variant`
- `final_oos_requires_frozen_family_selection`
- `final_oos_family_mismatch`

### Final-OOS preflight

Before compilation, persistence, or reservation:

- exactly one already-selected frozen executable variant;
- no holdout-time grid/search/sibling comparison;
- `selected_from_compilation_sha256` resolves an immutable prior exploratory/development compilation;
- selected variant is proven to have been predeclared in that prior recipe/compilation;
- final-OOS `research_family_id` equals the referenced frozen family.

Leave current `research_family_id + holdout_id` reservation/consumption unchanged as runtime authority.

## Ownership

You own the complete M10-A vertical slice:

1. typed draft/recipe/support/compilation domain contracts;
2. canonical exact recipe hashing and compilation hashing;
3. explicit versioned capability metadata/resolution;
4. current-approved readiness and exact immutable Product data binding needed by recipe compilation;
5. pure compiler to existing `ExperimentManifest` objects;
6. immutable recipe/compilation family artifacts and integrity verification;
7. read-only `Check support` API;
8. asynchronous supported-recipe execution handoff through the existing operation framework;
9. any minimal public canonical composition seam needed to reuse current runner validation instead of duplicating it.

## Canonical owners to reuse

Prefer current owners over new rule copies, including as applicable:

- `qap.experiment.manifest.ExperimentManifest` and its cross-field validation;
- `qap.experiment.model_policies.compose_model_strategy_policy(...)`;
- `qap.experiment.basket_policy.compose_basket_strategy_policy(...)`;
- `qap.experiment.basket_manifest.validate_basket_manifest_contract(...)`;
- current runner strategy/policy composition dispatch;
- existing `BasketDefinition` / basket replay-manifest preparation where scanner-derived `basket_graph` genuinely applies;
- current-approved Product readiness/scope and immutable-generation resolution;
- `manifest_sha256(...)`, `RunProvenance`, experiment artifact integrity, and current run readers;
- current final-OOS commitment/reservation/permit machinery;
- `OperationManager` / `OperationStore` / detached operation worker / `OperationRefDto`.

If the runner's canonical strategy dispatcher is private, expose/reuse the smallest public seam rather than copying its dispatch table. Change no scientific rule while doing so.

## Capability catalog boundary

The initial catalog is explicit, boring, and versioned. It may describe existing QAP capabilities plus a small number of known-but-unimplemented methods for explanation.

It must contain explanatory/static metadata and references/handlers that delegate to canonical validators/composers. It must **not** become:

- a duplicate schema registry;
- a duplicate combination-rule engine;
- a plugin framework;
- dynamic imports/entry points;
- arbitrary user Python;
- a second backtester.

Student-t Copula is an explanatory non-executable capability example only. Do not implement Copula or any new research method here.

## Fixed-basket truth

Preserve current basket authority exactly.

In particular, current `basket_graph` is development-only. M10-A must report that truth; it must not advertise `basket_graph + final_oos` merely because the generic experiment engine supports final-OOS elsewhere.

Distinguish scanner-derived `basket_graph` from an ordinary manually declared fixed basket using another already-supported current policy. Do not invent equivalence where the existing basket evidence contract is absent.

## Product data binding

Do not compile against "whatever generation is current later."

Freeze every compilation-affecting Product input into exact recipe identity before scientific execution, using current immutable-generation authority. The final manifest's existing dataset IDs/relative paths/fingerprints remain authoritative below the recipe boundary.

If identity/admission/data/direct-market setup is missing, `Check support` reports `readiness=needs_setup` plus typed reasons. It does not download data, mutate approval, or start preparation.

Strict historical PIT evidence remains separately owned; do not move PIT reconstruction rules into the recipe compiler.

## Immutable lineage

Persist the complete immutable recipe declaration and immutable compilation record before scientific execution.

The compilation record must bind at minimum:

```text
compilation_sha256
recipe_sha256
stable research_family_id
compiler_version
capability_catalog_version
ordered compiled manifest_sha256[]
```

Because lineage-only fields are deliberately excluded from `recipe_sha256`, do not treat `recipe_sha256` alone as a complete file-integrity seal. Protect/verify the complete stored recipe/compilation artifacts with the repository's existing artifact-integrity primitives or the smallest current equivalent.

Existing low-level run artifacts remain recipe-unaware. Membership can be proved through stable family ID plus exact manifest hash.

Existing immutable records must never be overwritten with a different recipe/manifest set under the same identity.

## API / operation boundary

Provide the smallest Product/application surface needed for M10-B:

- synchronous, read-only `Check support` for a recipe draft;
- asynchronous supported-recipe launch returning the existing operation reference contract.

Before submitting execution, re-run the same preflight and require `runnable=true`. The detached worker must revalidate exact recipe/binding before compilation/persistence so callers cannot bypass the HTTP check or use stale readiness.

Do not change `/api/experiments` away from its current completed-evidence meaning unless the existing API contract makes a narrowly compatible extension clearly better.

## Observable success conditions

M10-A is complete only when direct non-test evidence demonstrates at least:

1. a currently admitted pair recipe can be canonicalized and produce a truthful compositional support report;
2. an unknown method remains non-executable and returns `unknown_method` rather than dynamic dispatch;
3. a known-unimplemented method such as Student-t Copula returns method-unimplemented truth without blaming the pair;
4. simultaneous authority/capability/fidelity reasons can coexist in one support report;
5. `basket_graph + final_oos` is reported unsupported by current canonical basket authority rather than weakening that rule;
6. development `[A,B]` and selected final-OOS `[A]` use different exact recipe hashes but the same stable `research_family_id`;
7. the final-OOS selection resolves the immutable prior compilation and proves variant A was predeclared there;
8. missing selection lineage, family mismatch, and multi-variant final-OOS each fail during preflight before reservation;
9. a runnable recipe compiles to ordinary validated `ExperimentManifest` objects whose exact hashes are bound by the immutable compilation record;
10. execution delegates to the existing experiment/artifact/final-OOS machinery without adding recipe awareness to the low-level runner.

## Required validation

No tests.

Use direct deterministic non-test evidence for the observable claims above, then one relevant candidate-final static/contract pass only. At minimum, if affected by the final implementation, include the appropriate subset of:

- Ruff lint / format check for changed Python;
- Pyright for changed Python/API surfaces;
- import-linter contracts;
- OpenAPI export/generated TypeScript synchronization when the public API changes;
- frontend TypeScript typecheck only if generated API contracts change;
- `git diff --check`.

Do not run broad test suites or add tests.

## Out of scope

- Universal Scan implementation or scanner policy changes;
- Focus Scan;
- M10-B React/product UX beyond the smallest generated/public API synchronization required by M10-A;
- Copula implementation;
- Palazzi implementation or automatic paper interpretation;
- arbitrary custom strategy execution;
- generic plugin/runtime registration;
- new backtester/economics engine;
- scientific threshold/objective/control/final-OOS rule changes;
- live/private exchange authority;
- M10-C acceptance proof as a separate milestone;
- M10-D representative-user study.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. branch/worktree/commit and final Git state;
3. exact domain contracts and public API/operation surfaces added;
4. exact recipe hash, stable family, immutable data-binding, compilation-hash and final-OOS selection semantics implemented;
5. canonical owners reused and any minimal public seam exposed;
6. direct non-test evidence actually exercised, including family continuity and final-OOS rejection cases;
7. final static/contract checks actually run; explicitly state that no tests were run;
8. protected files/semantics confirmed unchanged;
9. M10-B handoff: the stable frontend/API contract Agent A should consume;
10. unresolved risk, deliberate non-scope, or decision needed.
