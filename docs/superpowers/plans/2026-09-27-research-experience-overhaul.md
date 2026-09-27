# QAP Research Experience Overhaul

**Status:** Provisional product and architecture hypotheses. The
[investigation plan](../../research/2026-09-27-research-product-investigation-plan.md)
is the current prerequisite. A replacement master plan is deferred until its
findings establish the required changes. No product implementation or revised
identity policy is approved by this document.

Update context — 2026-09-27 (superseded by Phase 18)
Trigger: investigation decisions D1–D7 were approved and Phase 18 was planned.
Purpose: point readers to the current plan.
Impact: superseded. [Phase 18](../../plans/18-research-experience-and-asset-resolution.md) is the current plan and tracker; this
document remains a historical record.
Evidence: Phase 18 decision log.

Update context — 2026-09-27 (investigation findings)
Trigger: the investigation this proposal depended on is complete.
Purpose: show which hypotheses survived.
Impact: confirmed: catalog/search without identity authority, `ProductUniverse`
as the single binding authority, typed resolution outcomes, and orchestration
without a new job ledger. Changed: preparation and resumption must be backend-owned,
because browser-initiated preparation does not survive reloads. A reviewed catalog
is unnecessary as a default, because automatic evidence covers most assets. See
[findings §9–10](../../research/2026-09-27-research-product-investigation-findings.md).
Evidence: the findings report.

Update context — 2026-09-27 (investigation-first correction)
Trigger: Hamza clarified that asset discovery must work across Binance/Gate by
code and name without per-coin support work, manual identity evidence or hashes,
and requested a documented investigation before the master plan.
Purpose: prevent tentative screen and catalog choices from becoming the solution
before the causes, coverage and automation options have been established.
Impact: navigation, layout, catalog and orchestration below are hypotheses. The
initial bounded reviewed-catalog recommendation is superseded as a default;
general ingestion/resolution feasibility must be investigated first.
Evidence: [investigation scope and preliminary source findings](../../research/2026-09-27-research-product-investigation-plan.md).

Update context — 2026-09-27
Trigger: Hamza's walkthrough rejected the current Research Console and scanner
experience; supplied QAP failure screenshots and Uniswap reference screenshots.
Purpose: define a coherent research product whose ordinary workflows absorb setup
complexity while retaining access to advanced research.
Impact: proposes replacing the September 25 interaction contract and revising the
asset discovery/setup boundary. Financial and scientific owners remain authoritative.
Evidence: supplied screenshots; current source at `ee9100d`; the
[console plan](2026-09-25-research-console-semantic-layer.md) and
[Phase 17 plan](../../plans/17-product-layer-market-data-and-research-lifecycle.md).

## 1. Intended experience

A person should be able to ask “compare Wormhole with Bitcoin,” find the intended
assets, start research, understand what happened, and deepen or change the experiment
without learning QAP's internal data machinery.

The supplied reference screens demonstrate a compact primary task, recognizable
entities, stable controls across modes, contextual detail, and complex capabilities
available when relevant. Those interaction properties are the reference. QAP's
research jobs and existing scientific constraints determine its actual controls.

Product responsibilities:

- Recognize assets by name, ticker, and exact supported market symbol.
- Resolve supported identities and venue compatibility from maintained evidence.
- Prepare the required history and retain the user's question through interruptions.
- Explain outcomes and offer a concrete next action when progress is blocked.
- Keep advanced controls connected to the question and result they affect.

User decisions:

- Which assets and question to research, and which supported period to use.
- Explicit permission to include an asset in research where admission is required.
- Optional methodology and parameter changes, with exact defaults inspectable.
- Any genuinely required research ownership permission, such as transient USDT.

Ordinary asset selection must not ask users to invent canonical identifiers, type
identity-version strings or verify provenance themselves. Coverage must be examined
beyond a prepared demonstration set; routinely adding a newly listed asset should
not require per-coin code or a hand-authored binding.

## 2. What the walkthrough established

| Observed failure | Verified cause or limitation | Required correction |
| --- | --- | --- |
| A tall initial form beside an empty canvas | `PairResearch` renders a stage strip and empty result panel before a task starts; controls and explanations dominate the initial view | Compact composition before a run; allocate the result workspace when there is something to inspect |
| `WUSDT` appears as BTC | Copied workspace contains Binance `W → BTC`; `researchAssetSearch` searches market symbols under the mapped canonical label | Validate and reconcile asset bindings; retain the observed listing identity in search; never silently present a conflicting mapping as Bitcoin |
| “Wormhole” returns no match | Search inputs contain symbols, canonical keys, and market strings; no full-name or alias metadata exists | Add sourced asset names and aliases to the discovery contract |
| “Needs identity mapping” on DAI | Ordinary selection exposes unresolved records; the setup UI asks for manually authored identity fields | Investigate general automated identity resolution and honest coverage limits; manual authoring cannot remain the ordinary fallback |
| BTC comparison ends in a technical path error | Pair selection raises one generic error when it finds no unique common venue path; the client appends “resolve setup above” | Backend supplies the actual cause and permitted recovery before a launchable action is offered |
| Scanner shows missing 15m history and a disabled button | Normal scan readiness is rendered without an integrated prepare-and-resume action | Scan intent owns preparation, scope confirmation, execution, and results as one journey |

Additional preparation findings: the copied Gate W/PIXEL history was reported ready
with a cutoff of August 20, 2026. Readiness alone does not establish current data.
The exact assets behind the final error screenshot are not established, so the
generic-error path is verified but its particular runtime cause remains unconfirmed.

This is product-owner rejection of the present experience. It does not fabricate
formal representative-user session results or close the M10-D gate.

## 3. Proposed navigation and screen behavior

Retain `Home / Research / Portfolios / History` as primary destinations. Home offers
resume and start actions. Asset administration and workspace diagnostics live in a
utility menu and remain reachable through contextual links when necessary.

Research has three visible task modes: **Compare / Backtest / Scan**. Compare and
Backtest share the selected pair and period. Advanced method authoring is available
from Backtest settings, including an explicit link to the existing custom experiment
editor. Historical point-in-time scanning has a separate advanced destination.

### Initial Compare screen

```text
QAP      Home   Research   Portfolios   History               Workspace

                      Compare   Backtest   Scan

                 Compare two assets
                 [ Select asset             v ]
                 [ Compare with             v ]

                 Period  [30d] [90d] [180d]
                 [       Compare assets       ]

                 Recent research, when it exists
```

This is a behavior sketch, not the final visual specification. The actual default
period labels must preserve the existing horizon/window contract and disclose the
date range used. Selecting two assets does not silently launch scientific work.

- Keep the main action visible from the beginning, with a clear prerequisite state.
- Do not allocate a blank chart column or display an idle process diagram.
- Do not create a visible “Untitled study” history entry from an untouched form.
- Use recognizable asset names, symbols, and sourced icons with neutral fallbacks.
- Prefer concise labels; put methodological explanations at the relevant decision.

### Asset picker

A roomy modal on desktop and a full-height sheet on mobile use the same searchable
catalog. Search supports `W`, `Wormhole`, `WUSDT`, and observed separator variants
such as `W/USDT`. Exact asset and exact market matches precede prefixes and substrings.
Market parsing uses known listings, not blindly removing `USDT` from arbitrary text.

Rows show name, ticker, and meaningful availability. For an exact market query,
show the matching venue market explicitly. Multiple venue listings can share one
asset row only when identity evidence supports that relationship. Ambiguous names
remain separate, recognizable choices. Names and logos never establish identity.

Choosing the second asset shows compatibility with the first. Incompatible assets
may remain discoverable, but show why and which recovery is available. Searching
for Bitcoin must not accept a Wormhole price series because a legacy record says BTC.

### Comparison and backtest results

After Start, expand into a chart-led workspace: pair and period remain editable in
a compact control area; the main area shows the result. On mobile, controls condense
above the result. Changing settings marks the old result as belonging to its old
inputs until another run completes.

Compare leads with the observed relationship and its chart. Backtest leads with
recorded outcomes versus holding and the declared simple-rebalancing control, then
the relative-wealth chart. Method details, assumptions, fills, costs, and provenance
remain accessible beside the result. No automatic winner selection is introduced.

Loading, partial results, and retry states occupy the same workspace. A chart retry
must not rerun a backtest. Reopening history preserves the exact recorded result and
does not attach new measurements as if they belonged to that run.

### Scan

The initial Scan view contains an explicitly approved scope, period, and one action.
An empty scope offers inline asset selection. Starting a scan prepares missing
history using existing acquisition owners, evaluates readiness, and displays the
actual eligible scope before execution. A reduced scope must follow the approved
scanner rules and be visible; it must not silently drop failed assets or substitute
a different research claim.

Progress reflects real work. Results lead with what was evaluated and learned,
including rejected and negative outcomes. Detailed exclusion reasons remain
available per asset. Advanced historical scanner configuration is a separate task,
not another full form below the normal scan.

### Expert use and History

An expert can inspect and edit supported methods, parameters, costs, allocation,
and evaluation settings without abandoning the current research context. Changes
still produce exact recipe identities and go through existing support validation.
Unsupported methods explain the limitation before launch.

History lists recognizable questions, dates, status, and outcomes. Browser drafts,
backend operations, and immutable results keep their distinct persistence meanings.
Portfolios continue to render authoritative holdings and economics; visual
consistency must not imply live holdings or trading capabilities that do not exist.

## 4. Architecture hypotheses to investigate

Build within the Python modular monolith and existing React application.

| Responsibility | Proposed owner / change | Boundary |
| --- | --- | --- |
| Names, symbols, aliases, icons, source attribution | Focused asset catalog and read API | Descriptive metadata cannot grant identity, approval, or readiness |
| Asset-to-market binding | Evolve existing Product universe resolution with admitted, versioned evidence records | `ProductUniverse` remains the single workspace authority for accepted bindings and admission; no competing mutable registry |
| Pair availability and blockers | Extend Pair Study preparation/context with structured resolution outcomes | Same-venue, exact-input and execution constraints remain backend-owned |
| Prepare and resume a research request | Feature-specific application orchestration using existing data preparation, recipe support, and operation owners | One submitted intent, single-flight execution, safe retries; no second job ledger or generic workflow framework |
| User interface state | Focused React task controllers and shared asset picker | Draft intent and presentation only; no client-derived scientific readiness or verdict |
| Replay and economic results | Existing recipe, execution, portfolio and evaluation modules | No new backtester, accounting implementation, or financial state owner |

### Asset resolution policy is an explicit design amendment

The existing contract puts identity authorship on the operator. Removing that
burden for ordinary assets requires maintained source evidence and an admission
policy for automated resolution. Hiding the current form does not achieve this.

Earlier proposal, now superseded as the default: start with a bounded catalog of
reviewed, versioned venue bindings. The rationale was conservative identity evidence,
but this can preserve manual per-coin support and fail Hamza's coverage requirement.

Investigate programmatic exchange discovery, sourced names/aliases and scalable
identity resolution before selecting a catalog strategy. Measure coverage and gaps,
including newly listed assets and assets outside the existing test fixtures.
Determine which identities can be resolved automatically, what evidence is needed,
and how genuine uncertainty affects only the relevant capabilities. Do not claim
universal runnable coverage without evidence or make manual mapping the normal path.

Before implementation, specify source precedence, update/freshness behavior,
renames and migrations, ambiguous symbols, conflicting evidence, source outages,
and which changes require review. No ticker-only merge, arbitrary version default,
or third-party logo/name lookup may become economic identity proof.

Legacy mappings require a previewable reconciliation report. Conflicts such as
`W → BTC` must be reviewed/quarantined under the approved policy. Correcting a
binding creates a new current version; old datasets and run manifests keep their
original lineage. Affected historical evidence gets an integrity explanation and
cannot silently be relabeled into valid Bitcoin research.

### Resolution and preparation contract

Return distinct causes: missing listing, unsupported identity, conflicting binding,
missing quote identity, no common venue, ambiguous path, missing history, stale
directory, and unavailable data source. Include the affected asset/source and
allowed actions. Render a concise explanation and relevant action in context.

The browser may initiate automatic supported preparation after explicit Start.
The backend remains responsible for eligibility, exact sources, dates and runnable
status. New research displays the actual data cutoff. Any missing policy for
refresh thresholds must be decided before promising “latest” data. Saved results
never refresh in place. Final-OOS rules remain in the advanced research contract.

## 5. Recovery examples to design before implementation

| Situation | Expected experience |
| --- | --- |
| Known W selected | Wormhole/W remains identifiable; accepted venue bindings are resolved internally |
| New supported DAI selected | Recognizable asset details and any required “Allow DAI in research” decision; no free-text identity-version request |
| Unknown or conflicting asset | Explain the specific unresolved identity in the picker; offer supported alternatives or contextual review without losing the question |
| Missing 15m history for Scan | Start initiates preparation; show real progress and retry failed source work in the same flow |
| No compatible venue for a pair | Explain which source is missing or incompatible; retain the pair and offer backend-supported alternatives or change selection |
| Temporary USDT ownership needed | One concise, explicit permission step inside Backtest with its workspace scope and consequences; resume after consent |
| Unsupported method | Keep the declared method visible, explain the unsupported capability and any honestly supported alternative; never silently adapt |
| Negative result | Display a completed result and both benchmarks; technical failure styling is reserved for failures |

## 6. Delivery order and review gates

**Prerequisite:** complete the linked investigation and derive a master plan from
its findings. The sequence below records the earlier delivery hypothesis; it does
not authorize implementation or settle architecture, layout or identity policy.

1. **Resolve the product contract.** Review this proposal, the identity policy
   amendment, and the recovery examples. Specify freshness and migration behavior.
   Approval of visual styling alone cannot approve identity-policy changes.
2. **Create a clickable experience prototype.** Show the initial screen, asset
   picker, contextual admission, preparation, incompatible-pair recovery, comparison,
   backtest, scan and expert settings on desktop and mobile. Label sample data.
   Review the whole journey and visual hierarchy before integrating product code.
3. **Implement asset discovery and resolution.** Deliver the catalog/search API,
   validated bindings, reconciliation preview and typed availability states.
   Verify W/Wormhole/market aliases, BTC, DAI, ambiguity and source failures.
4. **Deliver one complete Compare/Backtest slice.** Integrate picker, preparation,
   consent, existing execution and results. Prove the previously failing scenarios
   through the rendered application before expanding scope.
5. **Apply the same interaction contract to Scan and expert research.** Connect
   preparation and recovery, remove stacked task forms, and preserve exact scope,
   method and holdout semantics. Bring History and Portfolio navigation into line.
6. **Run experience acceptance and technical regression checks.** Record actual
   task outcomes and comprehension. Fix observed failures and rerun their journeys.
   Release completion requires both technical verification and human acceptance.

Use small reviewable changes within each step. Replace feature boundaries as
needed; preserve existing deep links and persisted drafts through explicit migration.
Do not expand this into a financial-engine rewrite or a new platform framework.

## 7. Acceptance contract

- `W`, `Wormhole` and a supported exact W market lead to the intended identity;
  conflicting legacy mappings cannot impersonate BTC.
- Known supported BTC and DAI require no operator-authored identifier/version text.
- A user can start the ordinary supported task from one compact screen; its primary
  action remains discoverable on desktop and mobile.
- No blocked primary action relies on “resolve setup above” without a matching,
  specific recovery action. Missing data can be prepared in context.
- Expert settings are reachable from the relevant task and preserve the selected
  pair, method intent and earlier result when opened or changed.
- Keyboard selection, focus return, screen-reader states and narrow-screen input
  are exercised in the asset picker and interruption flows.
- The chart and outcome dominate results; audit detail remains available.
- Tests protect identity, eligibility, benchmark, consent, retry and lineage
  behavior. Rendered checks cover real layout and complete interactions.
- Human walkthroughs demonstrate understanding and completion without developer
  coaching. No invented timing metrics or blanket click-count target substitutes
  for successful tasks and necessary decisions.

## 8. Evidence and limits

Source inspected: `researchAssetSearch.ts`, `ResearchAssetSelector.tsx`,
`PairResearchSetup.tsx`, `PairResearch.tsx`, `ResearchHome.tsx`, `ProductResearch.tsx`,
`product_universe.py`, `market/directory.py`, and `product_pair_study_data.py`.
The local source was used because Satori was not ready. No index was required to
establish these findings. No subagents were used.

External interaction references are the screenshots supplied by Hamza. Earlier
attempts at live search did not return usable results, the supplied Binance URL
did not yield readable content, and the local Khiip API timed out. No external
capture or live listing verification is claimed; further reference browsing was
stopped at the user's direction.

Phase 12 remains NO-GO. Spot ownership, explicit admission, HODL/control comparisons,
realistic execution costs, same-venue source contracts and final-OOS discipline
remain constraints on the proposed experience. Identity automation, changed
eligibility or freshness semantics require explicit design approval before code.
