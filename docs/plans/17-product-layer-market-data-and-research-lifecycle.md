# Phase 17 - Product Layer: Market Data and Research Lifecycle

**Status:** M0-M9 are complete and integrated. M10 is REOPENED IN DESIGN REVIEW after a real-user iPhone walkthrough showed that the Product exposes setup/governance machinery before the primary research jobs. Follow-up review clarified that the missing capability is broader than a Pair Research UI: QAP needs a typed Research Recipe / capability-preflight layer so a researcher can declare a method, check whether QAP can reproduce it faithfully, understand exact unsupported/blocked/data-readiness reasons, and only then execute it through existing experiment/scanner authority. M10-0 owns this design amendment; no M10 implementation is authorized until review.

**Canonical design:** `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`

**Investigation evidence:** `docs/research/2026-08-19-qap-product-layer-investigation.md`

**Legacy salvage evidence:** `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`

**Research cockpit investigation:** `docs/research/2026-08-20-qap-research-cockpit-investigation.md`

**Trigger:** Phase 16 is complete, but a clean QAP workspace still depends on expert/manual preparation of admissible assets, scanner market-data catalog state, longitudinal refreshes, and current public-evidence collection. That makes the application understandable only after hidden operational prerequisites have already been satisfied.

**Goal:** Make QAP usable from a clean local workspace by adding the smallest operational Product Layer that prepares honest research inputs, exposes backend-owned readiness, preserves all existing scientific/economic authority, and presents research as a longitudinal user object rather than a collection of backend subsystems.

**Primary product claim:** In the default mode, QAP researches the operator-approved assets that are currently available on selected supported Spot venues using trailing admitted historical data through a backend-owned safe cutoff. Historical point-in-time discovery remains a separate strict advanced claim.

## Global constraints

- Preserve the economic objective: QAP wealth relative to matched HODL/declared controls after costs.
- Preserve owned-inventory, long-only, Spot-only, no leverage/borrowing/derivatives/interest mechanics.
- Preserve the Phase-12 live-capital `NO-GO` boundary.
- Preserve QAP/scanner ownership of models, freezes, outcomes, capacity, basket targets, fills, accounting, benchmarks, and OOS state.
- Preserve negative, invalid, rejected, incomplete, and unavailable research evidence.
- Preserve the finite seven-command research mutation vocabulary; Product maintenance is a separate bounded owner.
- Do not infer historical point-in-time eligibility from current market metadata.
- Do not automatically admit every current venue asset into the research universe.
- Do not treat ticker equality as canonical asset identity.
- Do not use archived order-book data to retroactively satisfy the existing current-capture qualification contract.
- Do not add a generic queue, workflow engine, cloud service, private exchange connection, or live broker layer.
- Product operational persistence may use stdlib SQLite only within the frozen scope in the canonical design.
- CCXT is not required for Product V1; prefer existing Binance/Gate adapters until a concrete later requirement justifies it.
- Tests remain opt-in under the repository execution policy. This plan does not independently authorize creating, modifying, or running tests.

## Legacy-QAP salvage overlay - approved planning input

The legacy `tradingview_ratio` repository is a source of accumulated engineering and research knowledge, not a runtime architecture to transplant.

Phase 17 selectively adopts the following patterns inside current QAP owners:

- **M3:** gap-aware prepare/refresh planning, bounded API-pressure handling, and request-amplification measurement;
- **M4:** first-class freshness/readiness reasons rather than opaque ready/not-ready state;
- **M5:** truthful discovery-funnel counts, phase purpose/authority explanations, and backend-authorized next actions;
- **M6:** explicit separation of which evidence layer survived, weakened, or failed;
- **M7:** ownership/hidden-state review before adding long-lived collector state;
- **M8:** inventory/HODL-relative product-intent evidence in Portfolio/History presentation, without changing current QAP economics;
- **M9:** explicit process/state ownership and recovery analysis before any packaging decision;
- **M10:** research-intent-first Pair/Universe UX plus a typed Research Recipe/capability-preflight layer that can explain exact support, fidelity, readiness, and constitution blockers before execution; representative-user comprehension remains the final gate.

The following legacy patterns are explicitly rejected for Phase 17:

- monolithic `DataFetcher`-style ownership;
- CCXT-driven fallback as Product truth;
- presentation-derived research/trading authority;
- synthetic direct-market execution semantics;
- live/grid/rotation runtime machinery;
- global mutable API-guardian architecture or stale hard-coded exchange quotas;
- a universal translator/authority-metadata framework without a demonstrated current consumer.

Legacy absence/availability evidence is **not** historical-universe authority:

```text
earliest retrievable bar / missing historical range
    !=
historical point-in-time eligibility evidence
```

This overlay refines implementation and acceptance criteria only. It does not reopen the frozen economic, scientific, admission, or live-capital boundaries.

## 1. Product architecture

Phase 17 introduces one focused layer between local public-market inputs and the existing application/research boundary:

```text
Supported public Spot venues
          |
          v
Product market directory / identity / admission
          |
          v
Market-data preparation + immutable generations + provenance
          |
          v
Backend research-readiness / safe-cutoff composition
          |
          +------------------------------+
          |                              |
          v                              v
Current-approved research policy     strict historical PIT policy
          |                              |
          +---------------+--------------+
                          |
                          v
                  existing QAP/scanner
                          |
                          v
                 immutable evidence
                          |
                          v
                Product read composition
                          |
                          v
             React user experience
```

Current public liquidity collection is a sibling Product-maintenance responsibility that feeds the already-authoritative qualification path; it does not become scanner economic authority.

## 2. Frozen primary information architecture

The next Product Layer primary navigation is:

```text
Home | Research | Portfolios | History
```

Historical/specialist URLs may remain stable.

- `Research` composes discovery plus the longitudinal forward/current-evidence lifecycle.
- `Portfolios` retains the existing manual basket research authority boundary.
- `History` composes completed research and links to authoritative specialist evidence.
- `Activity` becomes a contextual utility surface rather than equal-weight primary navigation.

Do not migrate URLs unless a concrete implementation constraint requires it.

## 3. Milestone 0 - Product Layer design freeze

**Status:** COMPLETE - 2026-08-19.

Canonical output:

`docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`

Frozen decisions include:

- explicit operator-approved research universe;
- current-approved retrospective versus historical-PIT claim separation;
- fail-closed asset identity;
- Binance/Gate Product-V1 boundary;
- existing adapters before CCXT;
- immutable logical datasets with physical generations;
- automated acquisition provenance;
- scan-refresh-freeze lineage correction direction;
- direct-pair market preparation;
- backend-owned readiness and safe cutoff;
- one normal research timeframe;
- longitudinal Research Idea composition;
- all-survivor prospective follow-up;
- persistent current-evidence collection;
- no retroactive depth certification;
- stdlib SQLite operational-state boundary;
- `Home | Research | Portfolios | History` primary IA;
- explicit Sample versus Local Market workspace identity;
- packaging deferred until the product core works.

No source/runtime implementation is part of M0.

## 4. Milestone 1 - Workspace identity and clean zero-state

**Purpose:** Make a clean install and the currently running workspace unambiguous before adding market acquisition.

### Backend/product state

Add the smallest backend-owned workspace status needed to distinguish:

```text
workspace_mode: sample | local_market
workspace_root / stable workspace identity
market-data readiness summary
data last updated / no data yet
active product-maintenance task summary
```

Do not derive identity from port occupancy.

### Launcher

The local launcher must distinguish:

- the intended QAP workspace already running;
- a different/sample QAP workspace on expected ports;
- an unrelated process occupying a required port;
- only API or only web running;
- clean not-running state.

Do not build a generic process manager.

### UI

A clean `local_market` workspace should present a true zero-state:

> Choose the assets QAP is allowed to research, then prepare public market data.

A `sample` workspace must show a persistent Sample Workspace marker on all primary product surfaces.

### M1 exit

- workspace mode is backend-owned and visible;
- zero-state does not pretend fixture data is real market state;
- launcher does not equate any listener with the intended workspace;
- no research/economic contract changes.

## 5. Milestone 2 - Current market directory and explicit asset admission

**Purpose:** Replace hand-authored implied universe state with a user-understandable operator-approved Research Universe.

### Market directory owner

Reuse the existing Binance/Gate public adapters for current public Spot metadata.

The directory must preserve:

- venue;
- venue symbol;
- base/quote economic identity;
- current Spot/trading state;
- identity/lifecycle uncertainty;
- source/observation provenance.

### Admission owner

Persist explicit operator asset admission separately from current exchange availability.

The Product Layer must never turn `currently listed` into `approved to own` automatically.

### Identity

Reuse existing lifecycle/canonical identity concepts. Add only the minimum mapping/persistence necessary to support current Binance/Gate directory rows.

Unresolved identity is an exclusion/readiness reason, not a guessed mapping.

### UI

The normal surface is an asset-oriented Research Universe, not a raw exchange-symbol table.

Show:

- approved/not approved;
- which supported venues currently have the asset;
- ready/needs data/identity review state;
- explanatory action-space language;
- exact venue symbols under disclosure.

### M2 exit

A user can explain which assets QAP is allowed to research before any scan is launched.

## 6. Milestone 3 - Historical market-data acquisition, provenance, and generations

**Purpose:** Make the approved universe research-ready without manual catalog authoring.

### Acquisition

Implement bounded Binance/Gate OHLCV acquisition for only the approved/current scope and the intervals required by the selected QAP timeframe(s).

Prefer, in order:

1. official bulk files/checksums when they match the needed interval and semantics;
2. existing public REST adapters with bounded pagination for gaps/tail/missing intervals;
3. a small deterministic aggregation owner only where a required interval has no admitted native bulk path.

Do not add CCXT in this milestone unless the existing adapters are demonstrably insufficient for the required Binance/Gate operations.

### Gap-aware prepare and refresh

Before acquiring a requested Product window, compare the desired interval/window with the currently published immutable generation for the same logical dataset.

Use the smallest truthful acquisition plan that current owners can support:

```text
desired window
    + current validated coverage
    -> already covered / missing head / missing tail / unavailable
    -> acquire only what is actually required when safe
    -> publish one new complete immutable generation
```

Current published generations are already validated as contiguous; do not invent a second internal-gap registry merely to copy legacy `AdaptiveFetcher`. If an upstream page/archive contains an internal gap, fail acquisition explicitly under the current validation contract.

When only a head/tail extension is missing, reuse the existing immutable generation as source lineage where the current QAP generation/derivation contract can compose it safely instead of reflexively downloading the full history again. If the current implementation cannot do that without weakening provenance or validation, bounded full reacquisition is acceptable for V1, but the M3 exit report must quantify the request amplification and record the upgrade trigger.

Do not infer listing history or PIT eligibility from a missing head range.

### API pressure and source-efficiency policy

Historical preparation may involve many public requests across approved assets and intervals. M3 must therefore establish a bounded operational policy for exchange pressure without reviving the legacy global `APIGuardian`.

- use current venue responses/status/headers such as `Retry-After` when available rather than legacy constants;
- bound retries/backoff and fail explicitly after the declared retry budget;
- do not hold synchronization locks while waiting;
- do not create a global mutable singleton or generic request scheduler;
- if realistic M3 exit evidence does not encounter meaningful rate pressure, keep the implementation minimal and record the stronger throttle as deferred rather than manufacturing infrastructure.

Binance's daily-archive implementation must be evaluated for realistic request amplification. Monthly archive support is **not automatically required**; add it only if measured preparation shows that complete historical months materially reduce request count/latency without weakening source reconciliation, checksums, or provenance. Daily archives remain suitable for exact-day/tail behavior where appropriate.

### Provenance

Each new generation records exact acquisition/derivation provenance defined by the design freeze.

### Generations

Keep stable logical dataset IDs and immutable physical generations. Update the current catalog pointer only after the complete new generation is valid.

### Forward compatibility repair

Correct the scan-refresh-freeze ownership mismatch so a later current-catalog generation does not invalidate freezing an older completed historical survivor.

The repair must preserve original run/source lineage and tamper detection.

### Direct markets

For approved assets, discover and prepare real same-venue direct pair markets where they exist and are needed for authoritative replay.

Do not synthesize direct crosses from USDT legs.

### M3 exit

- a clean approved universe can become research-ready through Product operations;
- every generated dataset has exact source provenance;
- refreshing data creates immutable generations rather than overwriting research inputs;
- prepare/refresh does not blindly reacquire an already-satisfied window, or explicitly records why bounded full reacquisition remains the V1 choice;
- realistic multi-asset preparation either stays within bounded public API pressure or demonstrates bounded retry/failure behavior without a global request framework;
- acquisition availability remains separate from historical PIT eligibility;
- completed historical research remains freezeable after an unrelated later refresh;
- unsupported direct markets remain explicit unavailable evidence.

## 7. Milestone 4 - Current-approved research policy and readiness

**Purpose:** Give the default product an honest research claim that does not pretend current survivors form a historical PIT universe.

### Policy

Introduce a separate versioned current-approved/current-survivor research scope. Do not rename or weaken the existing strict Scanner-V1 PIT policy.

The new policy must bind:

- approved economic assets;
- selected supported venues;
- current availability observation;
- trailing admitted data slices;
- safe analysis cutoff;
- existing candidate/replay/economic rules that remain applicable;
- an explicit claim label making the retrospective scope distinguishable from strict historical PIT research.

Changing universe semantics is search-bearing; use a new protocol/policy identity rather than reusing old identities.

### Readiness

Add one backend-composed readiness read model for the selected timeframe and current approved scope.

It owns:

- eligible/ready assets;
- exclusions and reasons;
- required interval availability;
- direct-market readiness summary;
- latest safe completed-data cutoff;
- scope size;
- active acquisition state.

Readiness should preserve structured reasons/gates rather than collapse everything into one boolean. At minimum the backend must be able to distinguish operator scope, identity/current-market preconditions, required historical coverage, direct-market evidence, and Product-maintenance state.

Examples of distinct meanings include:

```text
not approved                 -> outside Product research scope
identity review required     -> Product identity precondition unresolved
approved but no current path -> current supported-market limitation
history missing/insufficient -> evidence incomplete
refresh running/failed       -> Product maintenance state
direct market unavailable    -> replay limitation, not asset invalidity
```

Do not import legacy eligibility thresholds or promotion labels. Do not use historical bar availability as a substitute for Scanner-V1 PIT lifecycle evidence.

The readiness contract may carry an internal authority declaration such as `DATA_READINESS_ONLY` when it materially prevents misuse, but do not add authority metadata to every DTO by convention.

### Safe cutoff

Normal Product research uses the backend-selected latest safe cutoff. No primary `as_of` input.

### M4 exit

The user can see exactly what would be researched, through what date, and why any approved asset/path is excluded before pressing the primary research action.

## 8. Milestone 5 - Self-explanatory Research experience

**Purpose:** Replace backend-subsystem navigation with the frozen product mental model.

### Primary flow

The normal Research page shows, in order:

1. approved research universe summary;
2. data readiness and latest safe cutoff;
3. one timeframe choice: Short-term / Medium-term / Longer-term;
4. one primary action: Find research ideas;
5. plain-language result summary;
6. prioritized Research Ideas;
7. complete ledger and protocol/audit data under progressive disclosure.

### Truthful discovery funnel and progress

Reuse the legacy discovery-funnel idea, but source every count from current authoritative backend/scanner state.

The Product may explain progress using concrete stage counts such as:

```text
24 approved assets
276 possible relationships
83 passed the first relationship check
12 received deeper historical evaluation
3 produced Research Ideas
```

Exact stage labels must reflect the current scanner implementation. Do not expose legacy cointegration terminology merely because it existed, and do not invent percentages or ETAs that the backend cannot measure.

Each major Research state should answer:

```text
What is happening?
What can this stage conclude?
What can it not conclude?
What valid action comes next?
```

Valid next actions must come from authoritative backend state. React may translate stable enums/states into plain language, but it may not infer scientific/economic conclusions from raw metrics.

### No-primary-internals rule

Normal flow does not require:

- scan IDs;
- protocol versions;
- candidate IDs;
- manual replay IDs;
- checkpoint IDs;
- venue symbols;
- explicit UTC `as_of`;
- model-family/template selection.

Advanced Research retains already-authorized controls.

### Result taxonomy

Keep these presentation states separate:

- Task failed;
- Evidence incomplete;
- Research rejected;
- Research supported.

### M5 exit

A non-expert can answer "what is QAP researching?", "how far did it get?", "what did QAP research?", "through what date?", and "what can I do next?" from the primary surface without opening audit details.

## 9. Milestone 6 - Longitudinal Research Idea and all-survivor follow-up

**Purpose:** Make later evidence feel like the evolution of a research idea rather than a new technical application.

### Research Idea page

Compose:

```text
Original historical evidence
Later forward evidence
Current market-evidence readiness
Hypothetical-capital assessment
```

Keep exact evidence classes and timestamps visible under deeper disclosure.

The Product must identify **which layer** a negative or weakening result belongs to. Do not collapse all failures into "the pair failed" or rewrite earlier evidence after later evidence changes.

Use current QAP evidence classes to preserve distinctions equivalent to:

```text
historical relationship evidence
economic/replay implementation evidence
later forward evidence
current public-market/capacity evidence
portfolio-expression evidence
```

Examples of acceptable semantics:

```text
Historical relationship evidence was present, but the declared economic replay did not survive its checks.

The original historical Research Idea survived, but later prospective evidence weakened it.
```

This adopts the legacy Research Operating System's separation of economic/mechanism/expression/strategy truth as research-method guidance only; it does not create a new Product navigation hierarchy or scientific authority.

Where useful, History/Idea detail may summarize:

- what was tested;
- what was learned;
- what was falsified;
- what remains uncertain;
- the next valid action.

### Follow-up action

When historical survivors exist, the normal action must enroll all surviving ideas from the relevant generation/horizon according to existing prospective rules.

The product must explain why this is done:

> QAP follows all ideas that passed the historical checks so later results are not cherry-picked after the fact.

### Validation IA

Remove `Validate` as a primary mental-model destination once the integrated Research Idea lifecycle is complete. Existing `/prospective` routes may continue to serve specialist/history links.

### M6 exit

The user can distinguish original, later, and current evidence, explain which layer weakened or failed, and still experience the evidence as one longitudinal research object without earlier evidence being rewritten.

## 10. Milestone 7 - Persistent current public-evidence collection

**Purpose:** Make current-capital qualification honestly usable over real elapsed time.

### Operational store

Use stdlib SQLite for the bounded Product operational state frozen by the design:

- collection plans;
- scheduled slots;
- accepted normalized public observations;
- maintenance task/recovery state.

Do not move completed scientific/economic artifacts into SQLite.

Before expanding collector persistence/process ownership, apply a focused ownership/hidden-state audit covering only this stateful boundary:

```text
state owner
allowed mutator(s)
consumers
lifetime
recovery behavior
failure mode
authority impact
```

Do not create repository-wide ledgers for ordinary changes; the legacy ownership/hidden-state methodology is required here only because M7 introduces long-lived mutable operational state.

### Collector

Collect only required approved/promoted/pinned instruments.

Preserve the existing scientific capture cadence semantics:

- nominal L1 60-second slots;
- nominal top-20 depth 5-minute slots;
- real observation timestamps;
- missing slot stays missing;
- one admitted observation per instrument/kind/scheduled slot.

### Qualification bridge

The qualification path may read/compose the collected normalized evidence through a backend-owned adapter/projection, but the existing qualification/capacity policy remains authoritative.

No frontend coverage math.

### No archive backfill

Historical depth archives do not satisfy the existing current-evidence qualification contract.

### UI

Show measured readiness, for example:

```text
Current market evidence
Day 3 of the required 14-day window
Coverage is still incomplete
QAP is collecting public market evidence in the background
```

Do not invent a completion ETA.

### M7 exit

A real workspace can accumulate the existing qualification evidence over time, expose measured slot/window progress, and recover after restart without pretending missed observations occurred or creating ambiguous mutable-state ownership.

## 11. Milestone 8 - Portfolios, History, and utility Activity convergence

**Purpose:** Complete the new primary IA without changing existing portfolio authority.

### M8-0 shared Product basket compatibility foundation

Before parallel Portfolio/History presentation work, land one shared basket provenance/source-binding foundation.

Current Product-v1 preserves the basket-relevant model/economic primitives, but the current basket implementation is not truthfully Product-compatible because:

- `SCANNER_V1_BASKET` explicitly commits to strict `scanner-v1-s1` as its source pair protocol;
- basket definition/replay require current-catalog identity to match the source scan;
- execution datasets are re-resolved from the current catalog;
- an M3 refresh may advance a logical dataset to a newer immutable generation after the Product source scan has frozen an older generation.

M8-0 must therefore:

- introduce a separately-versioned Product-compatible basket source/protocol identity rather than relabeling the strict basket protocol;
- admit only the exact current-approved Product-v1 source contract, not arbitrary future scanner protocols;
- preserve all existing basket economics and manual 3-6 / exact-edge selection semantics;
- resolve Product execution sources from the source scan's immutable input slices plus M3 generation provenance;
- seal exact `dataset_id + relative_path + semantic fingerprint` execution bindings into the basket definition/artifact before replay;
- make Product basket replay/recovery read those frozen physical generations rather than whichever generation the current catalog points to later;
- fail closed on missing, ambiguous, or tampered historical Product generations;
- keep existing strict historical-PIT basket behavior unchanged when exact physical lineage is not already available.

Do not make historical replay survivors the only eligible basket edges; existing basket relationship-edge eligibility remains authoritative and is broader than M6 Research Ideas.

Once M8-0 is integrated, M8 may fan out into independent History/Activity and Portfolio-presentation writers that consume the same stable basket claim/read contract.

### Portfolios

Keep the existing 3-6 asset manual basket and exact-edge selection semantics. Simplify labels around the current Research Idea model where helpful.

Do not preview resolver targets or turn the basket builder into an optimizer.

Use the legacy inventory/HODL thesis only as product-intent evidence for explanation. Current experiment/evaluation manifests remain authoritative for the actual economic objective.

Portfolio presentation should continue to answer, where the authoritative run supports it:

- how the declared result compares with matched passive holding/controls;
- which assets/relationships contributed;
- whether the result is concentrated;
- how much turnover/cost was required.

Do not replace the declared objective with a generic headline USD return.

### History

Compose completed:

- research generations/scans;
- longitudinal idea/forward evidence;
- basket research;
- research runs;
- paper operational evidence where relevant.

History is a navigation/composition layer; exact specialist artifacts remain authoritative.

History should preserve the distinction between:

```text
operator asset approval
market/data readiness
relationship/candidate evidence
economic replay evidence
portfolio evidence
```

Therefore a temporarily unavailable dataset must not remove operator approval, a rejected candidate must not imply an asset is invalid, and a later-stage failure must not rewrite the original research artifact.

For completed work, History should make it possible to understand what was tested, what was learned, what was falsified, what remains uncertain, and the valid next action without promoting those summaries above the authoritative artifacts.

### Activity

Move Activity to contextual/utility navigation. Running and failed tasks should remain easy to reach from Home and affected workflows.

### M8 exit

The primary shell is `Home | Research | Portfolios | History`; current-approved Product research can truthfully source the existing manual basket economics from exact immutable historical generations; operational status remains available without competing with user goals; Portfolio/History language preserves the declared HODL/control economic frame and distinguishes asset approval from downstream research outcomes.

## 12. Milestone 9 - Local packaging/process lifecycle decision

**Purpose:** Decide whether the mature local Product Layer needs a desktop shell.

Do not choose a packaging framework before M1-M8 expose the actual process-lifecycle burden.

Read-only process/state ownership reconnaissance may begin after M7 because M7 establishes the last planned long-lived Product process and M8 is forbidden from adding another service, scheduler, queue, or mutable Product store. The actual packaging decision and any executable M9 work still wait for completed M8.

Decision gate:

- if the reliable launcher plus local background product service is sufficient, stop there;
- if keeping long-lived collector/API/web processes reliable for nontechnical users remains a demonstrated burden, evaluate the smallest supported desktop shell;
- Tauri is the current candidate, not a preapproved dependency.

Before selecting a packaging/process solution, produce a focused process/state ownership matrix for the mature local runtime:

```text
process/state
current owner
allowed mutator
consumer
lifetime
restart/recovery rule
failure mode
first safe packaging move
```

This is the appropriate place to reuse the legacy ownership-boundary/hidden-state audit discipline. Do not import legacy process managers or runtime module organization.

Packaging must preserve loopback/local authority and the live-capital `NO-GO` boundary.

### M9 outcome

M9 completed without a desktop dependency. The mature Product-V1 runtime remains launcher + loopback API + web + one Local Market collector + detached bounded scientific workers. Product market-data maintenance now persists exact PID/process-start ownership and converts an orphaned `running` row into explicit failed/interrupted operational evidence on owner restart. The launcher proves API health, exact workspace identity, web readiness, and Local Market collector health before printing `QAP workbench ready.`; the open shell refreshes workspace/collector health periodically. Tauri remains deferred because no representative-user or runtime evidence currently shows that a desktop shell is the smallest required solution.

## 13. Milestone 10 - Research Cockpit + typed Experiment Lab + representative-user closure

**Status:** REOPENED / DESIGN REVIEW. The first real-user mobile walkthrough invalidated the assumption that M10 was only a final comprehension study. The follow-up clarification makes the correction broader than a Pair Research UI: QAP needs a first-class **research recipe / capability-preflight layer** so an operator can declare a method, type-check it, learn exactly why it is or is not supported, and execute it only when it compiles faithfully to current QAP authority.

**Investigation:** `docs/research/2026-08-20-qap-research-cockpit-investigation.md`

### M10-0 - Research Cockpit + Experiment Contract design amendment - CURRENT

**Purpose:** Freeze the corrected Product research journey and the smallest typed experiment contract before further implementation.

The normal Research surface remains organized around user intent:

```text
Research
  -> Research a pair
  -> Scan my universe
  -> Focus scan (deferred; scanner-owned only if scope reuse is mechanical)
  -> Experiment Lab (advanced)
```

The advanced experiment flow is deliberately split from scanner discovery:

```text
PAIR / FIXED-BASKET EXPERIMENT
ResearchRecipeDraft
-> structural validation
-> capability / authority / readiness resolution
-> SupportReportV1
-> if runnable: Recipe Compiler
-> frozen QAP ExperimentManifest(s)
-> immutable recipe/compilation family record
-> existing replay / controls / economics

UNIVERSAL / FOCUS DISCOVERY
Research intent
-> current-approved readiness / scope
-> existing scanner protocol
-> candidate discovery
-> existing candidate ExperimentManifest replay
```

Do not create a generic compile-target abstraction to unify these paths.

M10-0 freezes these contract decisions before implementation:

- executable `ResearchRecipeV1.research_object` is limited to `pair | fixed_basket`;
- Universal Scan remains under the existing current-approved scanner owner;
- Focus Scan is deferred unless it reuses scanner scope almost mechanically, and if added remains scanner-owned;
- `ResearchRecipeV1` separates relationship/evidence method, decision rule, allocation/rebalance, risk overlays, parameter-selection/calibration, execution/costs, benchmarks/evaluation, data role, fidelity intent, and source/reference metadata;
- backend support truth is compositional `SupportReportV1`, not one exclusive status;
- canonical recipe identity plus immutable compilation lineage must bind the declared methodology to `research_family_id` and exact compiled manifest hashes;
- `final_oos` permits exactly one already-selected frozen executable variant and no sibling/grid/search comparison on the holdout;
- one explicit versioned capability catalog provides explanatory/static metadata and canonical-owner references rather than duplicating runtime schemas/rules;
- exact-first asset search and mobile selected-item behavior;
- just-in-time identity/admission/data setup that preserves the user's unfinished research draft;
- what independent identity evidence can be shown safely to a non-expert user.

No runtime/scientific implementation is authorized by M10-0. Do not amend the frozen design spec until these decisions are reviewed.

### M10-A - Typed Research Recipe + Capability Preflight - BLOCKED ON M10-0 APPROVAL

Implement the smallest backend domain/API owner that can answer **before execution** whether a declared recipe is representable, executable, claim-compatible, and data-ready.

#### ResearchRecipeV1 identity and decomposition

Do not treat `model` as one catch-all field. The executable recipe object is only `pair | fixed_basket`, and the canonical semantic recipe declares:

```text
ResearchRecipeV1
  schema_version
  recipe_sha256
  research_family_id             # stable family-continuity anchor; not derived from recipe hash
  research_object                # pair | fixed_basket
  relationship / evidence method
  signal / decision rule
  allocation / rebalance policy
  risk overlays
  selection / calibration protocol
  execution + costs
  benchmarks + exact immutable data binding / evaluation role
  fidelity_intent
  source / reference metadata
  parameters / precommitted variants
  selected_from_compilation_sha256?  # final_oos selection lineage
  derived_from_recipe_sha256?    # required for explicit adaptations
```

`recipe_sha256` is exact recipe identity, not family identity. It hashes canonical semantic execution content including compilation-affecting immutable data bindings while excluding lineage-only fields (`recipe_sha256`, `research_family_id`, `selected_from_compilation_sha256`, `derived_from_recipe_sha256`). It changes whenever the method declaration, variant set, fidelity intent, source claim, immutable data binding, or evaluation role changes. `research_family_id` is established once for the research question/family and remains stable across intentional siblings and the selected final-OOS descendant.

#### SupportReportV1 is compositional

Do not force simultaneous truths into one status enum. The backend contract is:

```text
SupportReportV1
  structure: valid | invalid
  capability: executable | diagnostic_only | unimplemented | unknown
  authority: allowed | constitution_blocked | claim_incompatible
  readiness: ready | needs_setup
  fidelity: native | faithful_replication | adaptation_required | not_applicable
  runnable: true | false
  reasons[]
  suggestions[]
```

`runnable` is backend-owned and can be true only when the recipe is structurally valid, executable, authority-allowed, ready, and does not require an undeclared adaptation. Native QAP executability and faithful reproduction of an external methodology are separate questions. UI headline text is derived presentation, not backend truth. `adaptation_available` is a reason/suggestion, not an exclusive state.

#### Required typed reason categories

The checker needs a bounded reason vocabulary that can distinguish, for example:

```text
unknown_method
known_method_not_implemented
method_not_admitted_for_replay
method_has_no_current_data_contract
unsupported_research_object
incompatible_component_combination
requires_short_position
requires_leverage_or_borrow
requires_derivative
requires_unimplemented_risk_overlay
requires_unimplemented_parameter_selection
requires_unimplemented_walk_forward_protocol
requires_unavailable_numerical_backend
requires_missing_identity_confirmation
requires_operator_asset_approval
requires_market_data
requires_real_direct_market
current_claim_incompatible
strict_pit_evidence_required
cannot_claim_faithful_replication
adaptation_available
final_oos_requires_single_precommitted_variant
final_oos_requires_frozen_family_selection
final_oos_family_mismatch
```

Each reason must identify the failing recipe component, distinguish missing implementation from missing setup/data from a protected constitution/research-integrity boundary, and identify the nearest current capability when one exists. Return all applicable reasons together rather than choosing one by precedence.

#### Capability catalog

Use one explicit in-code/versioned catalog. Do **not** add generic plugins, dynamic imports, arbitrary Python execution, or runtime strategy registration. The catalog contains explanatory/static metadata and references canonical validators/compiler/composition owners; it must not duplicate the authoritative config schemas, combination rules, or constraints already enforced by the manifest/runner/model/basket owners.

The initial catalog should describe existing QAP capabilities first:

- rolling log-ratio relationship evidence;
- rolling residual/OLS relationship evidence;
- slow momentum;
- cross-sectional relative log return;
- scheduled targets;
- basket graph policy;
- current control specifications;
- direct and admitted bridge execution modes;
- current data-role/final-OOS and economic-claim constraints.

The catalog may include a small number of **known but unimplemented** named methods solely to explain support status, such as Student-t Copula. Such entries are non-executable and cannot dispatch code.

#### Compile down, do not build a second backtester

Only `pair` and `fixed_basket` recipes compile. Universal/focus discovery remains scanner-owned. A runnable recipe may compile to:

- one existing `ExperimentManifest`; or
- for `exploratory` / `development` only, an explicit finite family of sibling manifests under one `research_family_id` when the recipe declares precommitted variants.

`final_oos` requires exactly one already-selected frozen executable variant. A recipe that declares multiple variants, grid/search selection, or holdout-time comparison is rejected in preflight with `structure=invalid`, `runnable=false`, and `final_oos_requires_single_precommitted_variant`. Existing `research_family_id + holdout_id` reservation/consumption remains the runtime authority.

Entering `final_oos` also requires `selected_from_compilation_sha256` to resolve an immutable prior exploratory/development compilation. The selected variant must have been predeclared in that family, and the final-OOS recipe must reuse the referenced `research_family_id`. Its exact `recipe_sha256` is expected to change when the role, holdout/data binding, or variant set changes; that exact-identity change must not create a new research family.

Missing/invalid prior selection returns `final_oos_requires_frozen_family_selection`; changing the referenced family returns `final_oos_family_mismatch`. Both are preflight failures before compilation/reservation. `final_oos_requires_single_precommitted_variant` remains specific to multiple variants or holdout-time grid/search/comparison.

Before execution, persist one immutable family-level compilation record:

```text
ResearchRecipeCompilationV1
  schema_version
  compilation_sha256
  recipe_sha256
  research_family_id
  compiler_version
  capability_catalog_version
  ordered_compiled_manifest_sha256[]
```

`compilation_sha256` is the canonical hash of the compilation record excluding its own hash field. Every compiled manifest carries the compilation record's stable `research_family_id`. The compilation record binds one exact `recipe_sha256` plus compiler/catalog interpretation to the exact ordered manifest hashes without deriving or changing the research family. Existing run artifacts remain authoritative below that boundary and can verify membership through family ID + manifest hash without making the low-level runner recipe-aware.

Existing immutable data fingerprints, code provenance, controls, HODL/economic comparison, negative results, final-OOS reservation/consumption, and artifact ownership remain authoritative.

The check/preflight operation is read-only: it must not download data, mutate admission, consume OOS, or start a scientific run.

### M10-B - Research Cockpit + Experiment Lab Product Surface - BLOCKED ON M10-A

Build the user-facing surface on top of the typed recipe/preflight boundary.

Required modes:

```text
PAIR RESEARCH
select Asset A + Asset B
-> choose one Product timeframe
-> default versioned QAP pair recipe
-> Check support / resolve genuine setup blockers without losing the draft
-> compile to existing ExperimentManifest sibling family
-> run existing experiment replay / controls / economics
-> compare relationship/model/economic evidence

UNIVERSAL SCAN
show approved/ready scope
-> choose one Product timeframe
-> Scan my universe through existing scanner authority
-> truthful backend stage funnel
-> inspect retained/replayed/rejected/Research-Idea relationships

EXPERIMENT LAB
choose pair or fixed_basket research object
-> choose/define catalogued research recipe and declared parameters/variants
-> choose data role/evaluation protocol
-> Check support
-> inspect all applicable blockers/adaptations
-> run only if SupportReportV1.runnable=true and the recipe compiles faithfully
```

Focus Scan is deferred for M10 V1 unless the existing scanner scope can support it almost mechanically; if added, it remains scanner-owned and is not a `ResearchRecipeV1` compile target.

Default Pair Research should keep a versioned QAP method family so novices do not accidentally redefine the Product claim. Experiment Lab may allow explicit method/parameter selection because those variants are predeclared. Multiple sibling variants are valid only for exploratory/development roles; `final_oos` always requires one already-selected frozen variant.

Asset/setup behavior still requires:

- exact symbol match before prefix before substring/other matches;
- selecting an asset collapses/replaces the long result list on mobile;
- unresolved identity becomes a bounded `needs one-time setup` interruption;
- identity and approval remain separate backend authorities;
- ticker equality never becomes identity proof;
- pair/universe readiness is shown in user-task language;
- protocol IDs, fingerprints, physical generation paths, and other audit vocabulary remain available under progressive disclosure.

### M10-C - Capability/Fidelity proof with real research methods - BLOCKED ON M10-A/B

Prove the machinery with deliberately different cases. This milestone validates the support checker; it does **not** require implementing every method.

1. **Current rolling-residual pair recipe** — `structure=valid`, `capability=executable`, `authority=allowed`; readiness depends on setup and backend-owned `runnable` follows it.
2. **Current slow-momentum recipe** — explains through capability/research-object reasons that it is asset evidence/policy rather than automatically a pair-relationship model.
3. **Student-t Copula recipe** — `capability=unimplemented`, `runnable=false`, `known_method_not_implemented`; it must not falsely claim the selected pair itself is incompatible.
4. **Rafael Baptista Palazzi 2025 exact-replication recipe** — returns all applicable truths together: related OLS/z-score capability, constitution blocking for shorting, unimplemented selection/risk semantics, `fidelity=adaptation_required`, and `runnable=false`.
5. **Palazzi-inspired QAP adaptation** — if intentionally created, it gets a new `recipe_sha256`, `derived_from_recipe_sha256`, and separate fidelity claim.
6. **Final-OOS multi-variant recipe** — `structure=invalid`, `runnable=false`, `final_oos_requires_single_precommitted_variant` before compilation/reservation.
7. **Development-to-final-OOS family continuity** — development `[A,B]` and final-OOS `[A]` have different exact recipe hashes but the final-OOS recipe references the frozen development compilation and reuses the same `research_family_id`; sibling `B` cannot consume the same family holdout afterward.
8. **Unknown method ID** — `capability=unknown`, `runnable=false`, `unknown_method`; no dynamic dispatch.

Published methodologies are manually curated into typed recipes with source metadata. Phase 17 does **not** attempt automatic paper-to-code interpretation.

### M10-D - Representative-user comprehension / authority closure - FINAL

Only after M10-A/B/C exist should representative users complete realistic tasks without developer coaching. At minimum they must be able to:

- find exact `W` without hunting through substring matches;
- start `W / BTC` Pair Research;
- run/understand Scan My Universe;
- open Experiment Lab and check whether a named method/recipe is supported;
- explain the difference between `method unsupported`, `pair/data not ready`, `blocked by QAP constitution`, and valid negative research;
- inspect what a paper recipe actually declares about relationship evidence, decision rule, rebalance/allocation, risk, tuning/selection, benchmark, and OOS evaluation;
- distinguish an exact replication from a QAP adaptation;
- distinguish model/evidence from economic replay and later/current evidence;
- recover from identity/data setup without needing provenance vocabulary;
- distinguish approved versus data-ready assets;
- distinguish Product current-approved research from strict historical PIT;
- explain what a hypothetical-capital assessment means;
- answer correctly that QAP does **not** recommend, authorize, or place live trades.

Misunderstanding of a protected concept still triggers design review rather than changing scientific meaning in React.

## 14. Performance policy

The design investigation measured the existing Scanner-V1 benchmark at 2,079 assets / 720 bars:

```text
2,160,081 valid pair comparisons
~697 s SSD graph
~200 s projected scout workload
~550 MiB peak RSS
```

This is sizing evidence, not a promise.

Product consequences:

- prepare/scan the operator-approved universe by default;
- show scope/readiness before launch;
- do not make all-current-venue-ticker search the novice default;
- optimize only a measured bottleneck and preserve research semantics.

Market-data preparation follows the same rule: optimize request/source strategy only after measuring realistic approved-universe acquisition. Daily-versus-monthly archive choice, gap-aware incremental refresh, and pacing/backoff are operational optimizations; they may not change admitted bar semantics, provenance, or research scope.

## 15. Verification policy for this phase

Testing is not automatically authorized by this plan.

During implementation, use direct repository/browser/runtime evidence and the smallest relevant non-test checks capable of disproving the milestone claim.

Near a candidate final state, use applicable normal static/build/contract checks only once unless later edits invalidate them.

Create/modify/run tests only when the user separately requests them or an independently authoritative repository requirement specifically mandates them.

M10 user-comprehension work is product research/acceptance, not an excuse to fabricate quantitative usability metrics.

## 16. Stop conditions

Stop and return to design review before:

- changing economic objective, inventory authority, HODL/control semantics, costs/fills/timing, OOS state, or action-space rules;
- replacing the strict historical PIT rule instead of adding the separately-versioned current-approved claim;
- automatically approving newly listed assets;
- guessing ambiguous canonical asset identity;
- synthesizing a direct market from quote legs for authoritative Slice-1 replay;
- retroactively using historical L2 archives as current capture evidence;
- adding private exchange authentication/order placement;
- adding a generic job/queue framework;
- moving economic/capacity/readiness math into React;
- adding CCXT or another dependency without a concrete Product-V1 need;
- treating missing/earliest retrievable bars as historical eligibility proof;
- recreating a global mutable legacy API guardian, cache/fetcher monolith, or presentation-derived verdict authority;
- introducing automatic portfolio discovery/optimization.

## 17. Execution order

```text
M0  design freeze                                           COMPLETE
M1  workspace identity + clean zero-state                   COMPLETE
M2  market directory + explicit asset admission             COMPLETE
M3  adaptive market-data prepare/refresh + provenance       COMPLETE
    + immutable generations + request-pressure discipline
M4  current-approved policy + explainable readiness/cutoff  COMPLETE
M5  Research experience + truthful discovery funnel/IA      COMPLETE
M6  longitudinal idea + evidence-layer semantics/follow-up  COMPLETE
M7  ownership-safe persistent current-evidence collector    COMPLETE
M8  objective-aware Portfolios + History + utility Activity COMPLETE
M9  process/state ownership + packaging decision            COMPLETE
M10-0 Research Cockpit + Experiment Contract design        CURRENT / REVIEW
M10-A typed Research Recipe + capability preflight         BLOCKED ON M10-0
M10-B Research Cockpit + Experiment Lab                    BLOCKED ON M10-A
M10-C capability/fidelity proof with real methods          BLOCKED ON M10-A/B
M10-D representative-user comprehension/authority closure  FINAL / BLOCKED
```

Do not start M5 visual/React restructuring before M1-M4 make workspace/universe/data/readiness state authoritative.

## 18. Phase-17 exit criteria

Phase 17 is complete only when:

- a clean local workspace clearly distinguishes Sample versus Local Market mode;
- assets enter automatic Product research only through explicit operator admission;
- current market availability and canonical identity are backend-owned and fail closed;
- required historical market data can be prepared/refreshed with immutable generation/provenance records;
- preparation avoids unnecessary reacquisition where current immutable coverage already satisfies the requested window, or records the bounded V1 limitation and measured upgrade trigger;
- sustained public acquisition has bounded request-pressure behavior and does not rely on stale legacy quota constants/global mutable request state;
- acquisition availability/earliest history never substitutes for strict historical PIT eligibility evidence;
- later data refresh does not invalidate freezing legitimate earlier research merely because the current generation changed;
- default research explicitly uses the current-approved retrospective claim rather than pretending to be historical PIT discovery;
- strict historical PIT research remains available only under its existing evidence rules;
- Research shows backend-owned scope/readiness/safe cutoff before launch;
- Research exposes truthful scanner funnel counts/progress and backend-authorized next actions without fake ETAs;
- Research Ideas integrate historical, forward, and current evidence without collapsing their semantics;
- negative/later evidence identifies the affected evidence layer rather than rewriting earlier claims;
- prospective follow-up preserves all-survivor anti-cherry-picking behavior;
- current public evidence can accumulate persistently for the real 14-day contract without fabricated backfill;
- Portfolios preserve existing QAP target/execution/accounting authority;
- History preserves approval/readiness/research/economic-stage distinctions and explains what was learned/falsified/uncertain without becoming scientific authority;
- primary IA is `Home | Research | Portfolios | History` with Activity as a utility;
- negative research remains first-class evidence;
- the normal Research page exposes Pair Research and an explicit Scan My Universe flow before setup/audit machinery;
- exact asset search prioritizes exact matches and selected setup does not disappear below a long mobile result list;
- Pair Research preserves the selected research draft across identity/admission/data interruptions;
- default Pair Research uses a versioned admitted fixed-pair QAP recipe, while advanced Experiment Lab may select declared method/parameter variants only for `pair | fixed_basket` recipe objects;
- Universal Scan remains scanner-owned and uses backend-owned scanner stages without inventing a frontend “interestingness” score; Focus Scan is absent unless it can reuse scanner scope without new mechanics;
- `ResearchRecipeV1` separates relationship evidence, decision rule, rebalance/allocation, risk overlay, parameter-selection protocol, execution/costs, benchmarks/evaluation, data role, fidelity intent, and source/reference metadata;
- `SupportReportV1` is read-only and compositionally reports structure, capability, authority, readiness, fidelity, runnable state, and all applicable typed reasons rather than one precedence-based status;
- canonical exact recipe identity plus immutable compilation lineage binds each declared methodology/data-role instance to a stable `research_family_id`, compiler/catalog interpretation, and exact compiled manifest hashes before execution without deriving family identity from the recipe hash;
- exploratory/development recipes may compile finite predeclared sibling variants, while `final_oos` accepts exactly one already-selected frozen variant and rejects any grid/search/sibling comparison before reservation;
- final-OOS selection references the exact frozen exploratory/development compilation and reuses the same research family even though the exact final-OOS recipe hash changes;
- supported pair/fixed-basket recipes compile downward to existing `ExperimentManifest`/replay/economic authority rather than a second backtester or plugin runtime; the capability catalog points at canonical rule owners instead of duplicating them;
- a published method can be represented as an exact-replication recipe and receive a truthful blocked/unsupported report without being silently adapted;
- Student-t Copula can be reported as known-but-unimplemented without claiming the selected pair itself is incompatible;
- representative users can complete the M10-D research tasks and explain the protected meanings;
- QAP still has no live-capital/private-exchange authority.

## 19. Fresh-agent implementation mission

> Work in `/home/hamza/repo/qap` using the live coordination arrangement in `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`. Preserve legitimate concurrent changes. Read the frozen Product Layer design, this plan, `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`, and `docs/research/2026-08-20-qap-research-cockpit-investigation.md`. Phase 17 M0-M9 are complete and must not be replayed. M10 is reopened in design review: M10-0 must be approved before executable M10-A work. M10-A owns only the typed `ResearchRecipeV1` / compositional `SupportReportV1` / immutable compilation-lineage boundary for executable `pair | fixed_basket` research. Universal Scan remains under existing scanner authority; Focus Scan stays deferred unless scanner-scope reuse is nearly mechanical. Preserve strict PIT as Advanced Research, current-approved claim/readiness truth, fail-closed identity, immutable data provenance, research-family/final-OOS semantics, longitudinal evidence, manual Portfolio authority, and no-live-trade authority. Exact recipe hashes may change across development-to-final-OOS selection, but the frozen `research_family_id` must remain continuous; final-OOS must reference the exact prior compilation and reject multi-variant/search use before compilation. The capability catalog must reuse canonical validators/composers rather than duplicate runtime rules. Do not build a generic plugin runtime or auto-adapt published research. Copula is an example known-unimplemented method, not a required milestone. Testing remains opt-in under the current execution policy.

## 20. One-screen status

```text
Research engine / Slices 1-4      COMPLETE
Phase 16 M0-M8                    COMPLETE / CLOSED
Phase 17 M0 design freeze         COMPLETE
Phase 17 M1 workspace identity    COMPLETE
Phase 17 M2 research universe     COMPLETE
Phase 17 M3 shared foundation      COMPLETE
Phase 17 M3 Binance acquisition    COMPLETE
Phase 17 M3 Gate acquisition       COMPLETE
Phase 17 M3 Product orchestration  COMPLETE
Phase 17 M4 current-approved policy + explainable readiness/safe cutoff  COMPLETE
Phase 17 M5 Research / truthful funnel / primary IA  COMPLETE
Phase 17 M6 longitudinal Research Idea + evidence-layer semantics / all-survivor follow-up  COMPLETE
Phase 17 M7 persistent current-evidence collector / qualification bridge  COMPLETE

Phase 17 M8-0 Product basket provenance / immutable source binding  COMPLETE
Phase 17 M8-A History / utility Activity                           COMPLETE
Phase 17 M8-B Product Portfolio presentation                      COMPLETE
Phase 17 M9 process / state ownership + lifecycle hardening        COMPLETE

CURRENT / DESIGN REVIEW
Phase 17 M10-0 Research Cockpit + Experiment Contract design

BLOCKED UNTIL REVIEW / DEPENDENCIES
Phase 17 M10-A typed Research Recipe + capability preflight
Phase 17 M10-B Research Cockpit + Experiment Lab
Phase 17 M10-C capability/fidelity proof with real methods
Phase 17 M10-D representative-user acceptance

CURRENT PRIMARY IA
Home | Research | Portfolios | History

DEFAULT PRODUCT CLAIM
Current operator-approved Spot universe + trailing admitted history
(strict historical PIT research remains a separate advanced claim)

CORE RULE
Make operation simple without weakening research truth.
```
