# Phase 18 — Research Experience and Automatic Asset Resolution

**Status:** M1 committed (`438b3d9`); M2 committed (`62dd8e0`). The experience direction
of M4–M7 is superseded by [Phase 19](19-pair-rotation-lab-mvp.md) (approved 2026-09-30). Decisions D1–D7 are recorded below. The milestone tracker
(Section 5) records Phase 18 progress.

Update context — 2026-09-30 (direction change)
Trigger: design interview; Hamza rejected the research console experience and chose a
two-coin dashboard with verified real edge ([decision record](../product/decisions-2026-09-30.md)).
Purpose: point Phase 18's remaining work to its successor without erasing its history.
Impact: M1 and M2 stand. From M3, only the `W → BTC` repair continues; M4 search moves
to Phase 19 M2; M5 and M6 are replaced by Phase 19. D1–D7 remain in force except that
Phase 19 (Q9, approved) allows researching any eligible coin without admission.
Evidence: [vision](../product/vision.md), [MVP design](../superpowers/specs/2026-09-30-pair-rotation-lab-mvp-design.md).

Update context — 2026-09-30 (cleanup and wrap-up)
Trigger: Hamza authorized committing M1 and continuing to the M6 boundary, then
requested removal of legacy/stale code, data and documents and finally wrap-up.
Purpose: record the executable checkpoint, partial-work recovery and remaining work.
Impact: D6 cleanup direction now includes verified retirement rather than indefinite
quarantine; v1 compatibility and stored-data cleanup remain unimplemented. M6 is
not authorized to begin in this handoff. No financial semantics changed.
Evidence: M1 commit `438b3d9`; interrupted drafts and verification below.

Update context — 2026-09-30
Trigger: resumed the Claude handoff at `be22d2f` and implemented M1.
Purpose: record the implementation and distinguish focused verification from the
still-open requirement for green repository-wide checks.
Impact: none to D1–D7 or the remaining milestones; M1 implementation is committed
with the verification limitations recorded below (historical M1 check results).
Evidence: directory/API regression tests, recorded Gate fixtures, live read-only
adapter checks and baseline reproductions described in Section 5.

**Investigation evidence:** [research product investigation findings](../research/2026-09-27-research-product-investigation-findings.md)
(causes R1–R12, measured coverage, target journeys, options).

**Investigation method:** [investigation plan](../research/2026-09-27-research-product-investigation-plan.md)

**Retired proposals:** the September 27 research experience overhaul and the
September 25 research console plan were removed on 2026-09-30 at Hamza's request.
Their historical content remains in Git; this phase is the current contract.

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
| D6 | **Legacy cleanup (amended 2026-09-30):** retire the contradicted `binance:W → BTC` binding and verified contaminated/stale data after a preview and dependency check; re-confirm BTC admission. The original decision was quarantine/preservation; Hamza now requests removal of legacy/stale records and compatibility. | Reconciliation preview and dependency inventory first; no in-place relabeling. Stored-data deletion and compatibility retirement need completion; do not claim them done. | §3, §4.4 |
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
- Reconciliation preview and apply for legacy state (D6): verified retirement,
  dependency checks, integrity protection during cleanup, BTC admission re-confirmation.
- Dataset IDs for new generations use evidence versions. Remove obsolete v1
  compatibility after retiring or explicitly converting the affected workspace state.

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
| M0 Decisions and contract amendments | Done | `be22d2f` | D1–D7 recorded; Product design §5/§6 amended; index, findings, investigation plan, overhaul and console plans point here |
| M1 Exchange metadata, per-venue publishing | Implemented; repository-wide verification gate open | `438b3d9` | Names and currency evidence preserved; v2 directory, stable v1 hashes, independent publication and typed outage outcomes; verification below |
| M2 Registry, resolver, eligibility | Implemented and tested; uncommitted at time of writing | — | Registry client, resolver and eligibility with recorded fixtures; Phase 00 checks green (below); Binance tokenized-stock residue and bridged-variant policy open |
| M3 Automatic bindings, reconciliation | Draft only; incomplete | — | Interrupted untested draft; no actual workspace cleanup performed |
| M4 Search and availability API | Not started | — | |
| M5 Backend research requests | Not started | — | Investigation only before interruption |
| M6 UI regeneration | Not started | — | |
| M7 Acceptance | Not started | — | |

### M1 implementation and verification — 2026-09-30

Gate directory acquisition now includes `/spot/currencies`. Listings retain names,
`buy_start` as UTC, pair type, trade status, category, delisting/trade-disabled
flags and chain/address evidence. Addresses preserve case; these fields establish
no canonical identity. Binance retains spot permission flags and permission sets;
names and listing times it does not provide remain unknown.

The directory writes schema v2 and reads v1 without changing its historical hash.
Each venue is published before the next attempt. Failures retain the failed
venue's exact last-good source and markets, with separate attempted-at/status/error
records. An empty workspace can publish one successful venue. Total outage keeps
saved data stale, or returns a typed 502 if no observation exists. Corrupt saved
state is rejected before refresh. The Research Universe API exposes these outcomes;
its OpenAPI and generated frontend types have been updated.

Directory models and parsing helpers were separated to reduce the touched owners'
size. `product_universe.py` remains 632 lines and `binance_public.py` 610 lines:
both retain their existing owner responsibilities; new directory models/parsing
live in separate files. No touched file exceeds 700 lines. Extracted Binance
validation helpers match their original ASTs after symbol renaming.

| Check | Outcome |
| --- | --- |
| `uv sync`, `uv run python -V` | Passed; Python 3.14.4 |
| Focused directory/API/public-adapter tests | 51 passed, 1 opt-in live-network test skipped |
| Focused web tests for updated DTO fixtures | 26 passed |
| Ruff lint/format, import-linter, source-size, `git diff --check` | Passed; source-size reports 39 review warnings |
| Pyright on changed source and new tests | Passed |
| Frontend typecheck and production build | Passed |
| Read-only live adapter smoke | Gate: 2,202 markets, all named; Binance: 3,720 markets; no workspace publication |
| Full Python suite | 698 passed, 3 failed, 1 skipped |
| Full web suite | 110 passed, 6 failed |
| Repository-wide Pyright | 15 errors in the existing scanner qualification test |

Every full-suite failure was reproduced from an isolated archive of `be22d2f`.
Python failures: outdated exact OpenAPI operation-ID set in
`tests/contract/api/test_openapi.py`, an outdated expected message in
`tests/unit/experiment/test_model_policies.py`, and the obsolete `_capture_state`
call in `tests/unit/scanner/test_qualification_run.py` (also all 15 Pyright errors).
Web failures: two route-error tests plus BasketDetail, ExperimentList,
OperationList and PortfolioOverview. Those files' failing assertions and production
behavior were left outside the M1 change. The requirement for fully green Phase 00
checks remains open; implementation is not recorded as full milestone acceptance.

Raw Gate fixture subsets and provenance are in
[`tests/fixtures/gate/`](../../tests/fixtures/gate/README.md). Open Web Search
discovery failed; official Gate/Binance documentation was checked through the web
fallback. Khiip capture was unavailable, so no upstream Markdown archive is claimed.

### M2 implementation and verification — 2026-09-30

Update context — 2026-09-30 (M2 completion)
Trigger: Hamza asked to continue from the wrap-up handoff to the M6 boundary.
Purpose: record what M2 delivered and what its recorded evidence does and does not show.
Impact: none to D1–D7 or financial semantics; M3 drafts in the stash are untouched.
Evidence: tests in `tests/unit/asset_registry/`; fixtures and provenance in
[`tests/fixtures/registry/`](../../tests/fixtures/registry/README.md).

Delivered: `src/qap/asset_registry.py` (evidence contracts, `AssetRegistry`),
`asset_registry_coingecko.py` (paced, budgeted, injectable-transport client with
provenance per request, disk snapshot, last-good fallback returning typed
`stale`/`unavailable` results, `cached` reuse within `min_age`, optional
`COINGECKO_DEMO_API_KEY`), `asset_resolver.py` (evidence-only proposals) and
`asset_eligibility.py` (D4 classifier with typed reasons). No registry state is
mutable or authoritative; `ProductUniverse` is unchanged.

Behaviour: the venue ticker mapping outranks an address that only matches a reviewed
wrapped or bridged representation (`binance-bitcoin`, `binance-peg-weth`, and the
other allowlisted forms, including bridged USDC and DAI); any other disagreement
(DYDX, HOLDSTATION) is a `review` proposal with both candidate sets and no identity.
A unique address match resolves when no ticker exists, as does an address set whose
other members are reviewed representations of one asset (Gate DAI). Stale and anomalous tickers are
not evidence. Fixtures are real recordings from 2026-09-30, not synthetic.

Measured on the recorded snapshot (tradable USDT bases): Binance 415 resolved of
503 with 88 excluded and 0 unresolved (study 413 of 414; tolerance +-10), Gate 1,421
of 1,461 non-excluded (97.3%; study 98.1%; tolerance +-1.5 points), 5 reviews (0.3%),
393 cross-venue bases with 386 resolved on both and none disagreeing.

Hamza's decisions (2026-09-30): tokenized stocks are not needed, so Binance's
stock permission group `TRD_GRP_261` excludes every `...B` stock token, including
those the registry does not name; bridged USDC and DAI need no manual review and
are on the reviewed representation list. Gate `forex`, `metals`, `commodities` and
`indices` tags are venue metadata, with the forex tag overridden by registry crypto
evidence (USDC).

| Check | Outcome |
| --- | --- |
| `uv run pytest -q` | `761 passed, 1 skipped in 297.01s (0:04:57)` |
| `uv run ruff check .` | `All checks passed!` |
| `uv run ruff format --check .` | `473 files already formatted` |
| `uv run pyright src tests scripts` | `0 errors, 0 warnings, 0 informations` |
| `uv run python scripts/check_source_size.py` | `source-size: ok (39 review warning(s))` |
| `uv run lint-imports` | `Contracts: 8 kept, 0 broken.` |

The web suite was not run for M2.

### Wrap-up handoff — 2026-09-30

M1 is committed as `438b3d9`. The continued lanes were interrupted with
`Fatal error: application network permission was revoked`. Hamza then requested
wrap-up; M2–M5 and cleanup are not reported as completed. No UI generation began.

Untested M2/M3 drafts are preserved outside the executable working tree in Git
stash **`85278dcc93a02268a4fd7a7fa41968cf3169bc6e`**
(`wip: interrupted Phase 18 M2-M3 backend drafts before wrap-up`). This includes
registry/resolver/eligibility modules, integrity/reconciliation drafts, and an
unintegrated v2 universe-model extraction. It contains no acceptance tests or
recorded coverage fixture and must be reviewed before reuse. Inspect with
`git stash show --include-untracked --stat 85278dcc93a02268a4fd7a7fa41968cf3169bc6e`.
Do not apply it blindly to newer owner changes.

Wrap-up cleanup corrects three proven stale Python tests: the OpenAPI check now
protects required core/product operation IDs and uniqueness while allowing new
endpoints; qualification passes the authoritative instrument; model-policy
rejection checks the current error while preserving the rejection assertion.
Two explicitly superseded proposals were removed, with references redirected here.

Latest wrap-up checks: 36 focused Python tests passed, including all three repaired
baseline failures and the directory/API regressions. Repository-wide Pyright,
Ruff lint/format, import-linter, source-size and diff checks passed. The full Python
and web suites were not rerun during wrap-up; the earlier full-run evidence above
remains historical, and the six web failures remain unresolved.

Remaining work, in dependency order:

1. Finish M2 with recorded evidence, resolver fixture cases and measured coverage.
2. Finish M3 automatic policy bindings/USDT seed and evidence versions. Inventory
   actual workspaces and dependencies, retire verified corruption/stale records,
   remove obsolete compatibility/manual setup paths, and re-confirm BTC admission.
3. Implement M4 search and typed availability, then M5 durable research intents,
   freshness, scan preparation and authoritative custom-run lineage.
4. Resolve the six pre-existing web failures (route-error mocks, BasketDetail,
   ExperimentList, OperationList, PortfolioOverview) without weakening their
   evidence and economic assertions; run complete repository acceptance again.
5. **Stop before M6 and hand off.** UI generation and human acceptance stay pending.

No stored workspace data was deleted, no v1 compatibility was removed, and no
legacy reference corpus was changed in this checkpoint. Those authorized cleanup
items remain pending.

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
| Retirement breaks saved references | Dependency inventory and reconciliation preview before authorized retirement; no in-place relabeling |
| UI rewrite regresses expert flows | Existing specialist routes stay reachable; M6 wires modes incrementally behind the new surface |
| Scope creep | Every change traces to a finding and a journey; anything else goes to a later phase |
