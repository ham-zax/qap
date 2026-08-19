# Phase 17 - Product Layer: Market Data and Research Lifecycle

**Status:** M0-M2 are complete and integrated. M3 shared generation/provenance foundation is the current implementation frontier; venue-specific M3 acquisition follows after that seam is integrated.

**Canonical design:** `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`

**Investigation evidence:** `docs/research/2026-08-19-qap-product-layer-investigation.md`

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

### Safe cutoff

Normal Product research uses the backend-selected latest safe cutoff. No primary `as_of` input.

### M4 exit

The user can see exactly what would be researched and through what date before pressing the primary research action.

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

A non-expert can answer "what did QAP research?" and "through what date?" from the primary surface without opening audit details.

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

### Follow-up action

When historical survivors exist, the normal action must enroll all surviving ideas from the relevant generation/horizon according to existing prospective rules.

The product must explain why this is done:

> QAP follows all ideas that passed the historical checks so later results are not cherry-picked after the fact.

### Validation IA

Remove `Validate` as a primary mental-model destination once the integrated Research Idea lifecycle is complete. Existing `/prospective` routes may continue to serve specialist/history links.

### M6 exit

The user can distinguish original, later, and current evidence while experiencing them as one longitudinal research object.

## 10. Milestone 7 - Persistent current public-evidence collection

**Purpose:** Make current-capital qualification honestly usable over real elapsed time.

### Operational store

Use stdlib SQLite for the bounded Product operational state frozen by the design:

- collection plans;
- scheduled slots;
- accepted normalized public observations;
- maintenance task/recovery state.

Do not move completed scientific/economic artifacts into SQLite.

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

A real workspace can accumulate the existing qualification evidence over time and recover after restart without pretending missed observations occurred.

## 11. Milestone 8 - Portfolios, History, and utility Activity convergence

**Purpose:** Complete the new primary IA without changing existing portfolio authority.

### Portfolios

Keep the existing 3-6 asset manual basket and exact-edge selection semantics. Simplify labels around the current Research Idea model where helpful.

Do not preview resolver targets or turn the basket builder into an optimizer.

### History

Compose completed:

- research generations/scans;
- longitudinal idea/forward evidence;
- basket research;
- research runs;
- paper operational evidence where relevant.

History is a navigation/composition layer; exact specialist artifacts remain authoritative.

### Activity

Move Activity to contextual/utility navigation. Running and failed tasks should remain easy to reach from Home and affected workflows.

### M8 exit

The primary shell is `Home | Research | Portfolios | History` and operational status remains available without competing with user goals.

## 12. Milestone 9 - Local packaging/process lifecycle decision

**Purpose:** Decide whether the mature local Product Layer needs a desktop shell.

Do not choose a packaging framework before M1-M8 expose the actual process-lifecycle burden.

Decision gate:

- if the reliable launcher plus local background product service is sufficient, stop there;
- if keeping long-lived collector/API/web processes reliable for nontechnical users remains a demonstrated burden, evaluate the smallest supported desktop shell;
- Tauri is the current candidate, not a preapproved dependency.

Packaging must preserve loopback/local authority and the live-capital `NO-GO` boundary.

## 13. Milestone 10 - Representative-user comprehension closure

**Purpose:** Validate that the Product Layer is understandable, not merely clickable.

Representative users should complete realistic tasks without developer coaching and then explain:

- which assets QAP researched;
- why those assets were included;
- which venue/data cutoff applied;
- why a Research Idea appeared;
- difference between original historical, later forward, and current evidence;
- difference between task failure, incomplete evidence, and negative research;
- what a hypothetical-capital assessment means;
- whether QAP recommends or can place a live trade.

The final answer to the last question must be **no**.

Misunderstanding of a protected concept triggers design review rather than a frontend workaround that changes scientific meaning.

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
- introducing automatic portfolio discovery/optimization.

## 17. Execution order

```text
M0  design freeze                                  COMPLETE
M1  workspace identity + clean zero-state          NEXT
M2  market directory + explicit asset admission
M3  market-data acquisition + provenance/generations
M4  current-approved policy + readiness/safe cutoff
M5  Research experience + primary IA
M6  longitudinal idea + all-survivor follow-up
M7  current-evidence collector
M8  Portfolios + History + utility Activity
M9  packaging/process-lifecycle decision
M10 representative-user comprehension closure
```

Do not start M5 visual/React restructuring before M1-M4 make workspace/universe/data/readiness state authoritative.

## 18. Phase-17 exit criteria

Phase 17 is complete only when:

- a clean local workspace clearly distinguishes Sample versus Local Market mode;
- assets enter automatic Product research only through explicit operator admission;
- current market availability and canonical identity are backend-owned and fail closed;
- required historical market data can be prepared/refreshed with immutable generation/provenance records;
- later data refresh does not invalidate freezing legitimate earlier research merely because the current generation changed;
- default research explicitly uses the current-approved retrospective claim rather than pretending to be historical PIT discovery;
- strict historical PIT research remains available only under its existing evidence rules;
- Research shows backend-owned scope/readiness/safe cutoff before launch;
- Research Ideas integrate historical, forward, and current evidence without collapsing their semantics;
- prospective follow-up preserves all-survivor anti-cherry-picking behavior;
- current public evidence can accumulate persistently for the real 14-day contract without fabricated backfill;
- Portfolios preserve existing QAP target/execution/accounting authority;
- primary IA is `Home | Research | Portfolios | History` with Activity as a utility;
- negative research remains first-class evidence;
- representative users can explain the protected meanings in M10;
- QAP still has no live-capital/private-exchange authority.

## 19. Fresh-agent implementation mission

> Work in `/home/hamza/repo/qap` on `main`. Preserve legitimate concurrent changes. Read `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md` first for the live coordination frontier, then the Product Layer investigation/design and this plan. Phase 16 is closed; do not replay its milestones. Phase 17 M0-M2 are complete and integrated; the current writable frontier is the M3 shared generation/provenance foundation, followed by venue-specific acquisition and then M4. Preserve the strict historical-PIT policy, explicit operator asset admission, immutable evidence, negative research, all-survivor prospective follow-up, QAP financial authority, and the Phase-12 live-capital `NO-GO`. Do not add CCXT, a generic job system, cloud infrastructure, or live/private exchange authority without a concrete separately authorized need. Testing remains opt-in under the current execution policy.

## 20. One-screen status

```text
Research engine / Slices 1-4      COMPLETE
Phase 16 M0-M8                    COMPLETE / CLOSED
Phase 17 M0 design freeze         COMPLETE
Phase 17 M1 workspace identity    COMPLETE
Phase 17 M2 research universe     COMPLETE

NEXT
Phase 17 M3 shared generation/provenance foundation

FUTURE PRIMARY IA
Home | Research | Portfolios | History

DEFAULT PRODUCT CLAIM
Current operator-approved Spot universe + trailing admitted history
(strict historical PIT research remains a separate advanced claim)

CORE RULE
Make operation simple without weakening research truth.
```
