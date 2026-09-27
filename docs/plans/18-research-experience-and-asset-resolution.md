# Phase 18 — Research Experience and Automatic Asset Resolution

**Status:** Approved; M0 done, M1 next. Decisions D1–D7 are recorded below. The
milestone tracker (Section 5) is the single place to record progress.

**Investigation evidence:** [research product investigation findings](../research/2026-09-27-research-product-investigation-findings.md)
(causes R1–R12, measured coverage, target journeys, options).

**Investigation method:** [investigation plan](../research/2026-09-27-research-product-investigation-plan.md)

**Superseded proposals:** the [research experience overhaul](../superpowers/plans/2026-09-27-research-experience-overhaul.md)
(provisional hypotheses, now resolved here) and the
[research console plan](../superpowers/plans/2026-09-25-research-console-semantic-layer.md)
(historical implementation contract).

Update context — 2026-09-27
Trigger: the investigation found that the rejected experience comes from manual
asset identity, discarded exchange metadata, a corrupt `W → BTC` mapping,
browser-owned research orchestration, missing freshness rules and ineligible
assets in discovery. Hamza delegated decisions D1–D7 ("decide for me") and asked
for a simple, intuitive experience that does not hide complexity where it is
needed, plus a UI regeneration suitable for him and his stakeholders.
Purpose: turn the findings into approved decisions, ordered milestones and a
tracker for decisions and implementation.
Impact: amends Product Layer design §6 (identity) and §5 (discovery eligibility)
as recorded in D1–D4. Replaces the September 25 console interaction contract.
Economic objective, benchmarks, cost/fill semantics, holdout roles, owned-spot
action space and the live-capital NO-GO are unchanged.
Evidence: findings §0–§11.

## 1. Goal

A person opens Research, types an asset by name, ticker or market symbol, asks a
question, and gets an understandable answer. QAP finds, identifies, prepares and
refreshes everything that answer needs. Deeper research (backtests, scans,
parameters, custom experiments, audit detail) opens from the answer and keeps
its context. Genuine choices stay with the user and are asked once, in context,
in plain words.

The result must look and read well enough to show stakeholders: charts and
outcomes first, clear typography, consistent components, and exact audit truth
one step away.

## 2. Decision log

Decided 2026-09-27 by Hamza, who delegated the choice to the investigation's
recommendations. Each decision traces to the findings.

| ID | Decision | Consequence for implementation | Findings |
| --- | --- | --- | --- |
| D1 | **Automatic identity.** Evidence-backed resolution replaces operator-authored canonical IDs and identity versions as the ordinary path. Amends Product design §6: "known mappings may be automated" becomes "evidence-backed mappings are automated". | Resolver proposes bindings; `ProductUniverse` accepts them under policy; identity versions are evidence-derived; free-text identity forms are removed from ordinary flows. Manual review remains only for conflicts. | §4.3, R1–R4 |
| D2 | **Venue-local relationship research is allowed** before cross-venue equivalence is resolved. | A relationship study on one venue needs only that venue's listing identity. Economic replay, admission-dependent scans and portfolios still need full economic identity. | §4.3 |
| D3 | **USDT quote identity is seeded by policy** on Binance and Gate. | No workspace asks the user to map USDT. USDT stays a protocol coordinate, never an automatic economic target. | §5 |
| D4 | **Discovery eligibility:** leveraged tokens and tokenized stocks, metals and forex tokens are excluded from research discovery as outside the owned-spot action space (leverage, synthetic exposure). Fiat codes are excluded. | Eligibility classifier from venue metadata (Gate `category`, leveraged naming, registry classification). Excluded listings never appear as research candidates. | R11, §4.2 |
| D5 | **CoinGecko is the first supplemental registry**, behind a replaceable interface. An optional demo key is read from configuration; keyless access is paced and cached. A Binance API key is deferred. | Registry snapshots are recorded with provenance and reused; outages fall back to the last good snapshot and never block discovery. Attribution shown where registry data appears. | §4.1, §4.2 |
| D6 | **Legacy reconciliation:** quarantine `binance:W → BTC`, mark the two affected generations with an integrity note, re-confirm BTC admission. | Reconciliation preview first; no in-place relabeling; old dataset IDs remain readable; saved results keep their lineage. | §3, §4.4 |
| D7 | **Freshness:** new research tops up history to the latest completed bar before running. Readiness older than two graph intervals reports "needs refresh". | Research requests include a refresh step. Every result shows its data cutoff. Saved results keep their original cutoff. | R9, R12 |

Unchanged user decisions: admission ("willing to own", Product design §5) and the
workspace-wide transient USDT bridge permission. Both are asked once, in context,
with the asset's name and venues or the permission's scope shown.

## 3. Experience principles

1. **Ask, answer, deepen, audit.** Four layers on one surface: a question bar;
   the answer canvas (chart and outcome first); inline controls to deepen
   (backtest, parameters, scan, custom method); an evidence drawer with exact
   lineage. Nothing forces a user into a deeper layer to finish a simpler task.
2. **Recognizable assets.** Name, ticker, venues, listing status and a clear state
   ("ready", "preparing", "identity unconfirmed: reason") in the picker.
3. **One primary action per state.** A blocked action always names the cause and
   offers the fix in place. No "resolve setup above".
4. **Progress you can see.** Preparation and runs show real stages and survive
   reloads.
5. **Complexity where it belongs.** Expert settings, lineage selection and PIT
   controls are reachable from the task they affect and keep the question and
   previous result.
6. **Presentable.** Consistent design tokens and components, dark and light themes,
   desktop and mobile layouts, and a clean result view suitable for sharing.

## 4. Milestones

Dependency order. Each milestone lands as small reviewable commits with the
Phase 00 verification commands green.

### M0 — Decisions and contract amendments

Record D1–D7 in the Product design spec (§5, §6) with update-context notes. Mark
the overhaul proposal and console plan as superseded by this phase.

**Exit:** spec, plan index and dependent docs agree; no code change.

### M1 — Keep exchange metadata; publish each venue on its own

- Gate adapter keeps `base_name`, `buy_start`, trade status and pair type; add
  `/spot/currencies` (name, chains, contract addresses, category, delisted).
- Binance adapter keeps what `exchangeInfo` offers.
- Directory schema v2 stores names, listing time, class and chain evidence per
  listing; v1 files remain readable.
- Refresh publishes each venue independently with its own observation time; one
  outage leaves the other venue usable and names the stale source.

**Exit:** R1 fixed at the data layer for Gate listings; single-venue outage test.

### M2 — Registry client, resolver and eligibility

- `AssetRegistry` interface with a CoinGecko implementation: coin list with
  platforms, per-exchange tickers, optional demo key, pacing, snapshot recording
  with provenance, last-good fallback.
- `AssetResolver`: evidence from venue ticker mappings and contract addresses;
  precedence rule (ticker mapping beats a wrapped/bridged address match); conflicts
  and migrations go to review with evidence; evidence-derived identity versions.
- Eligibility classifier for D4.
- Recorded source snapshots as test fixtures: W, BTC, ETH (wrapped conflict), DAI,
  DYDX (migration), a leveraged token, a tokenized stock, a Gate-only asset.

**Exit:** resolver reproduces the measured coverage within tolerance on a recorded
snapshot; all fixture cases behave as specified.

### M3 — Automatic bindings in ProductUniverse; reconciliation

- Universe state v2: evidence bindings (source, evidence fingerprint, version,
  accepted_by `policy` or `review`), USDT policy seed, admission unchanged.
- Resolution runs after each directory refresh; accepted bindings apply
  automatically; conflicts are listed for review.
- Reconciliation preview and apply for legacy state (D6): quarantine records,
  generation integrity notes, BTC admission re-confirmation.
- Dataset IDs for new generations use evidence versions; old IDs stay readable.

**Exit:** a clean workspace resolves W, BTC and PIXEL with no manual step; the
walkthrough workspace shows and repairs the `W → BTC` conflict without relabeling
old data.

### M4 — Asset search and availability API

- Search endpoint: names, aliases (`W`, `Wormhole`, `WUSDT`, `W_USDT`, `W/USDT`),
  venues, status, listing time, eligibility and per-capability availability
  (relationship, backtest, scan) with typed reasons.
- Pair availability endpoint replaces the generic 409 with typed causes: missing
  listing, identity unconfirmed, conflict, no common venue, missing history, stale,
  source unavailable, not admitted.
- The web picker consumes these and derives no identity or readiness itself.

**Exit:** scenario matrix (findings §7) search rows pass as API contract tests.

### M5 — Backend research requests

- One submitted intent (assets, question, period, optional method) creates a
  research request owned by the backend. The backend resolves, refreshes (D7),
  prepares, runs and records stages using the existing preparation, recipe and
  operation owners. Single-flight per intent; safe retry; resumable after reload.
- Typed blockers with allowed actions (admit asset, grant bridge permission,
  choose another venue or asset).
- Scan uses the same path, including 15m preparation (R8).
- Custom experiment lineage becomes "choose a previous experiment"; the backend
  derives hashes.

**Exit:** journeys 1, 3, 4 and 7 pass against the API with a mocked network
boundary; reload during preparation resumes without duplicate work.

### M6 — UI regeneration

- Design system: tokens (color, type scale, spacing, radius, elevation), dark and
  light themes, core components (button, input, combobox, card, tabs, drawer,
  stage indicator, stat, empty and error states), chart theme.
- App shell and navigation: Research, Portfolios, History; `/research` route with
  redirects from existing deep links.
- Research surface: question bar with asset picker, answer canvas, deepen panel,
  evidence drawer; Compare/Backtest, Scan and Custom as modes of one surface.
- Stakeholder-ready result view: headline outcome versus HODL and simple
  rebalancing, chart, cutoff and venue, plain-language summary, exact audit behind
  one click.
- Accessibility: keyboard combobox, focus return, screen-reader states,
  narrow-screen layout.
- Prototype review with real data before wiring the remaining modes.

**Exit:** rendered desktop and mobile screenshots reviewed by Hamza; the primary
journeys work end to end in the browser.

### M7 — Acceptance

- Playwright journeys 1, 4, 7 and 9 from an empty workspace; journeys 2, 3, 5, 6
  and 8 as integration or rendered checks.
- Retire tests that enshrine the rejected contract (manual USDT mapping, "BTC
  backed by WUSDT" warning); keep identity, lineage, benchmark, consent and
  chart-retry protections.
- Human walkthrough by Hamza, recorded as observed outcomes.

**Exit:** all journeys pass; Hamza accepts the experience. This also closes the
open Phase 17 M10-D representative-user gate.

## 5. Tracker

Update this table in the same commit as the work it records.

| Milestone | Status | Commits | Notes |
| --- | --- | --- | --- |
| M0 Decisions and contract amendments | Done | `docs(plans): record Phase 18` | D1–D7 recorded; Product design §5/§6 amended; index, findings, investigation plan, overhaul and console plans point here |
| M1 Exchange metadata, per-venue publishing | Not started | — | |
| M2 Registry, resolver, eligibility | Not started | — | |
| M3 Automatic bindings, reconciliation | Not started | — | |
| M4 Search and availability API | Not started | — | |
| M5 Backend research requests | Not started | — | |
| M6 UI regeneration | Not started | — | |
| M7 Acceptance | Not started | — | |

## 6. Constraints

- `ProductUniverse` remains the single authority for accepted bindings and
  admission. No second mutable registry.
- Registry data is evidence, never economic truth on its own; ticker equality never
  merges listings.
- No new backtester, accounting, job ledger or workflow framework. Research requests
  compose existing owners.
- Saved results never refresh or relabel in place.
- Source files stay under 500 lines where possible (fail above 700); import-linter
  layers hold; financial core never depends on Product modules.
- No live order placement; the Phase 12 NO-GO stands.

## 7. Risks

| Risk | Mitigation |
| --- | --- |
| Registry rate limits or outage | Snapshot cache, last-good fallback, optional demo key, discovery never waits on the registry |
| Registry misclassification | Two-source agreement, precedence rule, review queue, recorded evidence per binding |
| Migration breaks saved results | Old dataset IDs readable, reconciliation preview before apply, no in-place edits |
| UI rewrite regresses expert flows | Existing specialist routes stay reachable; M6 wires modes incrementally behind the new surface |
| Scope creep | Every change traces to a finding and a journey; anything else goes to a later phase |
