# QAP Product Layer Design Freeze

**Status:** FROZEN IMPLEMENTATION BASELINE - 2026-08-19

**Phase:** 17 - Product Layer: Market Universe, Data Workspace, and Research Lifecycle

**Authority:** Explicitly requested by the user after the post-Phase-16 product investigation. This design supersedes the Phase-16 `single-stakeholder provisional` information-architecture baseline for future Product Layer work. It does not rewrite completed Phase-16 history.

**Primary rule:** Simplify operation and presentation without weakening research truth.

**Investigation evidence:** `docs/research/2026-08-19-qap-product-layer-investigation.md`

## 1. Why this phase exists

Phase 16 made the existing workbench substantially easier to read, but it still assumes that an expert has already prepared the market-data catalog, selected admissible assets, arranged longitudinal data updates, and supplied enough current public evidence for qualification.

That assumption is not acceptable for the intended local product.

A clean QAP installation must be able to answer, without requiring the user to understand scanner internals:

> Among the assets I have explicitly approved and that QAP can research on supported spot venues, are there historical relationships worth researching further?

The Product Layer therefore owns the operational bridge between a clean workspace and the already-authoritative QAP research engine.

It does **not** become a second research engine, accounting authority, execution engine, historical-universe oracle, or live-trading system.

## 2. Product mental model

The default user journey is frozen as:

```text
Set up QAP
    -> approve assets
    -> prepare public market data
    -> choose one research timeframe
    -> find research ideas
    -> review one idea
    -> follow all surviving ideas prospectively
    -> collect current public liquidity evidence
    -> evaluate a hypothetical amount
    -> combine selected research into a portfolio study
    -> review research history
```

The default primary navigation is frozen as:

```text
Home | Research | Portfolios | History
```

`Validate`, `Results`, and `Activity` remain valid implementation/history concepts but stop being equal-weight primary destinations:

- forward validation becomes a stage of a Research Idea;
- completed research becomes History;
- background/research operations become contextual task status and a utility Activity surface;
- specialist pair, experiment, paper, operation, candidate, scanner, and audit routes may remain stable underneath.

Route-path migration is not required merely to match these labels. Presentation composition may change before URLs do.

## 3. Authority model

The Product Layer may own:

- workspace identity and mode;
- current supported-market directory reads;
- explicit operator asset admission;
- current market-data preparation and refresh;
- immutable market-data generation pointers;
- upstream acquisition/derivation provenance;
- product maintenance task state;
- current public-evidence collection scheduling;
- backend-composed readiness/read models;
- plain-language presentation state.

The Product Layer may **not** own:

- portfolio inventory or balances;
- fills, costs, accounting, HODL/control wealth, or economic verdicts;
- scanner model fitting or candidate scoring truth;
- prospective outcome truth;
- capacity/qualification math;
- basket resolver targets or financial replay;
- final-OOS consumption authority;
- historical point-in-time eligibility by inference from current metadata;
- live/private exchange credentials, order placement, or capital deployment.

Existing QAP/scanner artifacts remain the scientific/economic authority.

## 4. Frozen research claim classes

The Product Layer must make two different universe claims explicit. They must never be silently collapsed.

### 4.1 Default: Current Approved Market Research

This is the normal product mode.

Claim:

> Research the assets the operator has explicitly approved and that are currently available on selected supported spot venues, using trailing admitted historical market data through an explicit safe cutoff.

This is a **current-survivor retrospective**. It is not a claim that the same complete asset set was historically investable at every point in the trailing window.

The backend must use an explicit versioned policy/claim identity for this mode. Do not mutate the existing strict Scanner-V1 point-in-time policy and silently reuse its name.

### 4.2 Advanced: Historical Point-in-Time Research

The existing strict Scanner-V1 lifecycle policy remains authoritative for historical point-in-time discovery claims.

Only instruments with sufficient historical lifecycle evidence may enter an official automatic point-in-time graph. Current `exchangeInfo`, current CCXT markets, current Gate markets, or the existence/absence of historical bars may not be used as a substitute for complete historical eligibility evidence.

Unknown historical eligibility remains fail-closed for official PIT claims and may be available only through explicitly labeled forensic/manual research where already permitted.

## 5. Explicit asset admission

QAP researches only economic assets the operator has explicitly approved as assets they are willing to own.

The current exchange directory is discovery input, **not** automatic QAP admission.

The Product Layer must therefore provide an operator-controlled Research Universe containing:

- canonical economic asset identity;
- venue/instrument availability;
- admission state;
- identity/lifecycle warnings when relevant;
- data readiness per supported timeframe;
- last refresh/safe research cutoff.

Asset-level religious/suitability judgment remains outside QAP's mechanical guarantees. QAP must not claim scholarly certification.

USDT remains a venue quote/execution coordinate under the existing contracts and is not automatically an economic target asset.

## 6. Asset identity is fail-closed

Ticker equality is not economic-asset identity.

The Product Layer must preserve QAP's existing concepts of:

- `canonical_asset_id`;
- asset identity version;
- venue symbol;
- rename/migration/lifecycle evidence;
- explicit continuity.

Known mappings may be automated.

Ambiguous ticker collisions, renames, migrations, contract changes, or uncertain cross-venue equivalence must be excluded from official automatic research until resolved or explicitly treated under an already-authorized forensic boundary.

Do not concatenate histories across a rename/migration without recorded continuity evidence.

## 7. Supported venue boundary

Product V1 remains bounded to the already-approved Binance and Gate public Spot surfaces.

The existing public adapters are the default implementation path.

A user-facing venue choice may exist only through an explicit versioned Product Layer/current-approved scope. Do not mutate Scanner-V1's frozen venue semantics merely to add a checkbox.

No cross-exchange inventory, arbitrage, synthetic history, or venue-splicing is introduced.

## 8. CCXT decision

CCXT remains an exchange-boundary candidate, not a Product-V1 requirement and never a truth source.

Frozen rule:

- V1 should reuse and extend QAP's existing Binance/Gate public adapters where they are sufficient;
- CCXT may be admitted when a third venue or demonstrated duplicated adapter work makes normalization materially cheaper;
- if admitted later, CCXT may normalize public transport/metadata primitives;
- QAP still owns canonical asset identity, source provenance, lifecycle evidence, historical-universe admission, Spot/action-space admissibility, dataset identity, and research claims.

Do not add CCXT merely because it is available.

## 9. Historical market-data acquisition

The Product Layer must be able to prepare the historical OHLCV needed by the selected approved universe without requiring a hand-authored scanner catalog.

Acquisition order:

1. official exchange-native bulk archives/checksums where they satisfy the exact QAP bar/provenance contract;
2. official public REST for missing intervals, bounded pages, gaps, and unpublished tail data;
3. derivation only where an explicit causal derivation contract exists and source lineage is retained.

Do not silently mix source families when their semantics disagree.

Binance daily official public data is preferred over blindly trusting monthly files when source reconciliation shows a discrepancy.

Gate bulk data may accelerate supported intervals, but a missing native interval such as a Product-required 15m series may be derived only through a documented deterministic aggregation contract from an admitted lower interval. The resulting dataset must retain exact source-generation lineage.

## 10. Market-data provenance

Automated acquisition requires more provenance than the original hand-built fixture workflow.

Every generated market-data artifact must be traceable to an immutable acquisition/derivation record containing at minimum:

```text
logical dataset identity
venue + venue symbol + canonical economic assets
interval
upstream provider/source family
exact archive/object/checksum or request boundary where available
retrieval/observation timestamp
acquisition implementation version
raw/source fingerprint(s)
derivation identity and parent generation(s), when derived
resulting QAP semantic fingerprint
```

The exact structure may remain a focused manifest rather than being embedded in every Parquet schema.

React does not need to display this by default; it belongs under Research & audit details.

## 11. Immutable logical datasets with physical generations

Logical dataset IDs must remain stable across later public-data refreshes, while physical source artifacts remain immutable.

Conceptually:

```text
BTC/USDT 1h
    generation A
    generation B
    generation C  <- current catalog pointer
```

Rules:

- never overwrite a completed physical research-data generation;
- publish a new generation only after complete download, validation, provenance binding, and semantic fingerprinting;
- update the logical current pointer atomically;
- old QAP/scanner manifests retain exact historical generation identity;
- do not garbage-collect generations referenced by research artifacts in Product V1.

## 12. Scan-refresh-freeze lineage correction

The Product Layer will refresh market data while users continue to inspect older scans. Therefore a refresh must not make a previously completed historical survivor impossible to freeze merely because the current catalog points to a newer physical source generation.

Frozen repair direction:

- historical freeze validation must resolve the original immutable historical replay sources sealed by the authoritative QAP run/scan lineage;
- it must not require the current catalog's whole-source fingerprint to equal the old scan generation merely because the logical dataset ID is the same;
- later prospective advancement may use a newer immutable generation under that logical dataset ID, provided the prospective checkpoint/replay contracts bind the exact later generation they consume;
- semantic candidate/freeze/checkpoint identities remain based on the already-frozen causal information states, not on future physical extent.

Do not weaken tamper detection or silently substitute source data.

## 13. Direct pair-market preparation

Relationship discovery can compare approved `ASSET/USDT` paths, but ordinary Slice-1 authoritative pair replay remains narrower: it requires a real direct same-venue spot instrument between the candidate economic assets plus admitted historical bars.

The Market Data Workspace should therefore discover and prepare relevant real direct markets between approved assets where they exist.

If no direct market exists, QAP may retain relationship/scout evidence but must continue to show the stricter economic replay as unavailable/unsupported rather than synthesizing a USDT cross.

## 14. Research readiness is backend-owned

The browser must not infer whether the workspace is ready to scan.

A backend Product Layer read model must compose at least:

- approved asset count;
- enabled supported venues/current market availability;
- identity/lifecycle exclusions;
- per-timeframe required interval readiness;
- direct-market readiness where relevant;
- latest safe completed-data cutoff;
- excluded/not-ready reasons;
- active market-data maintenance state.

The primary UI may say:

```text
24 approved assets
23 ready for Medium-term research
1 needs more history
Data ready through 2026-08-19 09:00 UTC
```

but those facts come from backend-owned state.

## 15. Default research input surface

The normal Research page asks for one research timeframe, not an expert matrix of protocol inputs.

Presentation labels are frozen as:

```text
Short-term
Medium-term
Longer-term
```

Backend identities remain:

```text
short
medium
swing
```

Multi-timeframe runs, forensic modes, manual pins, manual replay IDs, explicit historical cutoffs, and equivalent protocol controls remain Advanced Research functions.

Normal users do not supply `as_of`. The backend supplies the latest safe cutoff for the selected ready scope.

## 16. Research Idea as the longitudinal product object

The normal user should experience one Research Idea whose evidence evolves through distinct stages:

```text
Original historical research
    -> later forward evidence
    -> current market/liquidity evidence
    -> hypothetical-capital assessment
```

These evidence classes remain distinct in the backend and in advanced/audit presentation. The Product Layer may compose them into one page; it must not merge their authority or time semantics.

`Validate` therefore becomes part of the Research Idea lifecycle rather than a primary navigation concept.

## 17. Follow every historical survivor

Forward enrollment must preserve the existing anti-cherry-picking rule.

When a completed scan/horizon has multiple surviving automatic/manual selections, the normal action is conceptually:

> Start follow-up for all surviving ideas from this research generation.

The product may later let the user inspect one idea at a time, but it must not silently freeze only whichever survivor the user clicked after seeing the historical results.

Reselection/deduplication rules remain backend-owned.

## 18. Current public-evidence collector

A fresh workspace cannot satisfy the existing current-capacity contract with one button click.

QAP's qualification policy requires a 14-day window of sufficiently complete public L1/depth evidence plus metadata. The Product Layer therefore needs a persistent background collector for the instruments that actually need current qualification.

Frozen semantics:

- public, unauthenticated Spot data only;
- one scheduled L1 observation per nominal 60-second slot;
- one scheduled top-20 depth observation per nominal 5-minute slot;
- metadata observations as required by the existing qualification contract;
- actual observation timestamp preserved;
- missed invocation/slot remains missing evidence;
- no invented percentages/ETAs beyond measured slot/window readiness;
- collection can resume after process restart without fabricating missed evidence.

The collector is Product maintenance, not a scientific result.

## 19. No retroactive capacity certification

Historical exchange order-book archives must not silently backfill the existing prospective/current capture contract.

Even if a venue publishes historical depth files, using them for a different archive-backed capacity study would require a new explicit provenance/policy design.

The existing `research_only`, `small_capacity`, and `tradable_now` scientific meanings continue to rely on their current authorized evidence contract until deliberately versioned otherwise.

## 20. Collector slot uniqueness

The scheduled coverage denominator is defined by required cadence slots. The Product collector must not overweight one slot by persisting repeated successful observations from the same scheduled interval as independent required observations.

Operational persistence must enforce one admitted scheduled observation per:

```text
instrument x evidence kind x scheduled slot
```

while still preserving the real `observed_at` and source fingerprint of the accepted observation.

## 21. Operational persistence decision

The current file-per-stream append implementation reads and rewrites the entire Parquet stream on each append. That is appropriate for bounded fixture/manual capture but not for a persistent 14-day scheduled collector.

A focused **stdlib SQLite** store is frozen for Product operational state and current scheduled observation staging.

SQLite may own only:

- product maintenance task state;
- market-data preparation/refresh state;
- collector schedules/slot state;
- normalized current public observations needed for scheduled collection/recovery.

Immutable QAP research/economic artifacts remain Parquet/JSON and remain authoritative.

No Postgres, Redis, Celery, Kafka, cloud queue, microservice, or generic workflow engine is authorized.

## 22. Product maintenance versus research operations

Do not add continuous market-data acquisition to the existing seven-command scientific mutation vocabulary merely for convenience.

The existing research commands remain protected:

```text
run_scan
generate_asset_momentum
freeze_forward_cohort
advance_forward_cohort
capture_public_evidence
qualify_candidate
run_basket
```

Product maintenance may have a separate, small bounded vocabulary such as:

```text
prepare_market_data
refresh_market_data
```

and collector lifecycle state.

Do not introduce a generic arbitrary job endpoint.

## 23. Presentation state grammar

The Product Layer must preserve four conceptually separate outcomes:

```text
Task failed
    QAP could not complete the requested operation.

Evidence incomplete
    The operation may be valid, but the requested scientific claim is not ready.

Research rejected
    QAP completed valid research and the hypothesis did not pass its declared checks.

Research supported
    The hypothesis passed the declared research checks; this is not trade authorization.
```

These states must not be collapsed into generic red/green success UI.

## 24. Capital-assessment language

Backend enum values remain unchanged.

Primary presentation is frozen as:

```text
research_only  -> Research only
small_capacity -> Smaller amount supported
tradable_now   -> Current evidence supports this amount
```

The `tradable_now` presentation must remain adjacent to the explicit statement:

> Research assessment only - QAP does not place or authorize live trades.

The phrase `tradable now` is not novice-facing product copy.

Normal users provide a hypothetical capital amount after backend readiness is satisfied. They do not choose capture kinds, venue symbols, checkpoint IDs, or explicit `as_of` timestamps.

## 25. Sample versus real workspace

A clean product must make workspace mode explicit.

Frozen modes:

```text
sample
local_market
```

Sample mode:

- is an intentional onboarding/demo choice;
- carries a persistent visible Sample Workspace marker;
- must never be mistaken for the user's live local market-data workspace.

The local launcher/product status must distinguish:

- QAP already running for this workspace;
- another/sample QAP workspace using the expected ports;
- unrelated process occupying a required port;
- API/web partially running.

Do not treat port occupancy alone as proof the intended QAP workspace is running.

## 26. History and Activity

History is the primary completed-work archive for normal users. It may compose scans, forward evidence, basket research, experiments, and paper evidence while retaining links to their authoritative specialist views.

Activity remains available as a utility for running/completed/failed operational tasks.

An operational failure must never overwrite or reinterpret an existing scientific result.

## 27. Portfolio experience

Phase-16 portfolio authority boundaries remain frozen:

- pre-run UI may show admitted relationship availability/topology;
- the user explicitly selects a 3-6 asset basket and exact candidate edge where multiple rules exist;
- no browser-side resolver target/opinion preview before ordinary QAP replay;
- completed negative basket research is a valid result, not application failure;
- QAP policy/execution/accounting remains the sole financial authority.

The Product Layer may simplify labels and navigation but may not add automatic graph-to-basket discovery or optimizer-driven portfolios.

## 28. Performance/readiness boundary

A broad current market directory is not automatically a safe scan scope.

During this design investigation, the existing deterministic Scanner-V1 benchmark was run at 2,079 assets and 720 bars on the connected research machine:

```text
valid SSD pairs             2,160,081
retained edges                 11,869
fixed trials                  213,642
SSD time                       697.26 s
projected full scout time      199.74 s
peak RSS                       550,364 KiB
authoritative replay ceiling        30
```

This is sizing evidence, not a production SLA and not a current exchange-count contract.

Consequences:

- default Product research uses the explicitly approved universe rather than all venue tickers;
- backend readiness should expose scope size before launch;
- do not present an unbenchmarked all-market scan as a casual one-click default;
- if later latency requirements demand optimization, optimize the measured SSD/search bottleneck while preserving semantic distance/tie/digest rules rather than weakening the research scope after observing P&L.

## 29. Packaging boundary

Desktop packaging is **not** part of the initial Product Layer foundation.

M1-M8 must work as a reliable local product first.

A desktop shell may be evaluated in the packaging milestone only when it removes a demonstrated local-operability burden such as keeping long-lived processes/collector state alive. Tauri remains a candidate, not a frozen dependency.

Packaging may not introduce private exchange credentials or live-trading authority.

## 30. Human-comprehension acceptance

The Product Layer is not accepted merely because users can click through it.

Representative-user acceptance must check whether users can correctly explain, in plain language:

- which assets were included and why;
- which venues and data cutoff were used;
- what QAP actually compared;
- why an idea appeared;
- historical versus later versus current evidence;
- research rejection versus task failure;
- what a hypothetical amount assessment means;
- that QAP is **not** recommending or authorizing a live trade.

If representative users systematically misunderstand one of those protected concepts, that is evidence for a design review. It is not permission for the frontend to conceal or change the underlying research truth.

## 31. Explicit non-goals

Phase 17 does not authorize:

- live/private exchange APIs or order placement;
- leverage, margin, borrowing, derivatives, lending, yield, or interest-bearing mechanics;
- automatic asset-level religious certification;
- automatic admission of every exchange ticker;
- historical-universe inference from current metadata;
- a second accounting/backtest authority;
- changing HODL/control, cost/fill, timing, or final-OOS semantics;
- automatic portfolio discovery or an optimizer;
- cross-exchange inventory/arbitrage;
- generic strategy/plugin DSLs;
- arbitrary job/workflow APIs;
- cloud/distributed infrastructure;
- archived-depth retro-certification of current capacity;
- frontend capacity/coverage/economic math;
- a frontend framework or component-library rewrite;
- route migrations solely for prettier URLs.

## 32. Stop conditions

Return to design review before implementation crosses any of these boundaries:

- changing the protected economic objective or action space;
- changing benchmark, fill, cost, timing, inventory, or OOS semantics;
- changing the existing strict historical PIT admission rule rather than adding an explicit separately-versioned current-approved claim;
- automatically admitting assets without operator authority;
- treating uncertain asset identity as resolved;
- using historical order-book archives to satisfy the existing current-capture qualification policy;
- adding a generic job/queue architecture;
- adding a new external dependency when the existing adapters/stdlib are sufficient;
- moving scientific/economic authority into React;
- introducing live/private exchange or capital authority.

## 33. Frozen implementation order

Implementation proceeds in this order:

```text
M0  Product Layer design freeze                    COMPLETE
M1  Workspace identity + clean zero-state
M2  Market directory + explicit asset admission
M3  Historical market-data acquisition + generations/provenance
M4  Current-approved research claim + readiness + safe cutoff
M5  Self-explanatory Research experience + new primary IA
M6  Longitudinal Research Idea + all-survivor follow-up
M7  Persistent current-evidence collector
M8  Portfolio + History + utility Activity convergence
M9  Local packaging / process-lifecycle decision
M10 Representative-user comprehension closure
```

Do not skip directly to M5 React work. The UI cannot honestly simplify states that the backend Product Layer does not yet own.

## 34. Design-freeze summary

The Phase-17 Product Layer is a **local operational/read-composition layer around the existing research authority**.

It makes QAP usable from a clean workspace by explicitly owning:

```text
approved research universe
+ public market-data preparation/refresh
+ immutable generations/provenance
+ honest current-approved versus historical-PIT claims
+ backend readiness/safe cutoffs
+ longitudinal idea composition
+ persistent current public-evidence collection
+ understandable product navigation/state
```

while preserving:

```text
QAP/scanner scientific truth
+ exact immutable evidence
+ negative research
+ strict historical PIT semantics
+ anti-cherry-picking prospective enrollment
+ portfolio/accounting authority
+ live-capital NO-GO
```

This is the frozen baseline for Phase-17 implementation. Any later change to a protected item above requires an explicit design-review update rather than route-by-route improvisation.
