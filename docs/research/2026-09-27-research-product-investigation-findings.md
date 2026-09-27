# QAP Research Product — Investigation Findings

**Date:** 2026-09-27

**Status:** Investigation report answering the
[investigation plan](2026-09-27-research-product-investigation-plan.md). It
records evidence, causes, options and the decisions needed before a replacement
master plan. It authorizes no implementation, identity-policy change, eligibility
change or data repair.

**Source baseline:** `ee9100d` on `feat/research-study-workspace`, with the staged
planning documents preserved.

Update context — 2026-09-27
Trigger: the investigation plan's sections A–F and scenario matrix were executed.
The work started in a Codex session, which stopped when its credits ran out, and
finished in a Claude Code session using that session's recorded evidence.
Purpose: give the master plan evidenced causes, measured coverage and explicit
decisions instead of screen hypotheses.
Impact: confirms that the rejected experience comes from the identity/discovery
boundary and from where research orchestration lives, not from layout. Several
overhaul hypotheses are confirmed and several decisions need owner approval
(Section 10).
Evidence: this document's Sections 1–7, the saved probe scripts named in Section 1,
and the source files linked throughout.

## 0. Summary

The research product fails for five reasons. Each one predates the newest screens.

1. **No milestone ever owned automatic asset identity.** The
   [Product Layer design](../superpowers/specs/2026-08-19-qap-product-layer-design.md)
   (§6) says "Known mappings may be automated". The implementation automated none.
   The August 20 investigation left "independent identity evidence" open (§10.4).
   The September 24 plan explicitly limited identity to wording and placement (§8).
   Every later pass therefore redesigned a free-text form and could not remove it.
2. **QAP discards the metadata the exchanges already send.** Gate returns a full
   name for all 2,071 tradable USDT pairs and contract addresses for most currencies.
   QAP keeps only codes, symbols and status. Binance's public spot API has no names.
   That is why `Wormhole`, `Bitcoin` and `Ethereum` return nothing.
3. **An unvalidated manual mapping corrupted research inputs.** The free-text form
   saved Binance `W → BTC` as the first mapping of the M10-D walkthrough. Because
   mapped rows rank first, typing **`BTC`** now puts the Binance WUSDT row at the
   top. A "BTC" study, and the optional "BTC reference" lens, would use Wormhole
   prices. Two stored data generations carry `base_asset: BTC` for WUSDT. No saved
   result consumed them.
4. **The browser owns the research workflow, and Scan has no way to prepare data.**
   Pair research runs a ten-step orchestration inside one React mutation. Scan
   blocks on missing 15m history and links to a page that cannot prepare it.
   Readiness has no freshness bound, so "ready" can mean data five weeks old.
5. **Discovery offers assets outside the admissible action space.** The picker lists
   422 leveraged-token codes (`BTC3S`, `ETH5L`, …) and tokenized stocks (`AAPLB`,
   `NVDAX`) as research candidates.

Automatic coverage is feasible. Using only public sources and no per-coin work,
413 of 414 Binance crypto USDT bases (99.8%) and 1,459 of 1,488 Gate crypto USDT
bases (98.1%) resolve to exactly one registry coin. All 389 cross-venue tickers that
could be checked resolve to the same coin on both venues. Under 2% of listings
remain, mostly obscure codes and three token migrations (Section 4.2).

**Recommendation:** change the discovery/resolution boundary and move research
orchestration to the backend (Option B, Section 9). Another presentation pass
over the current contract cannot satisfy the requirements. Section 10 lists the
seven owner decisions this depends on.

## 1. Environment and evidence

| Item | Value |
| --- | --- |
| Commit | `ee9100d` plus staged docs; staged `PairResearchSetup.tsx` differs only by a two-space indentation change on one line (line 32), apparently accidental |
| Isolated workspace | `~/.local/state/qap/m10d-walkthrough-20260927` (copy of `runs/` state), API `127.0.0.1:18000`, web `127.0.0.1:5173` |
| Directory observation | Binance 2026-09-27T02:08:10Z, Gate 02:08:11Z; 5,907 markets stored |
| History cutoff | Medium horizon safe cutoff 2026-08-20T04:00Z; short and swing have none |
| Live sources | Binance `/api/v3/exchangeInfo`, Gate `/spot/currency_pairs` and `/spot/currencies`, CoinGecko `/coins/list?include_platform=true` and `/exchanges/{id}/tickers`, all fetched 2026-09-27 03:38–03:51 UTC |
| Browser | `agent-browser` session `qap-investigation-20260927` (Codex session) |
| Probe scripts | [2026-09-27-investigation-probes/](2026-09-27-investigation-probes/): `gate_match.py`, `cg_match.py`, `fetch_cg.sh`, `matrix.ts` (runs the real `researchAssetSearch.ts` against the live universe response). Raw snapshots (27 MB) are not committed; the folder README explains how to refetch them |

Labels used below: **observed** (seen in the running app or API), **source-verified**
(read in code), **measured** (computed from live responses), **inference**,
**unknown**. Live listings change; the counts are a 2026-09-27 snapshot.

The Codex session used Satori for code navigation. This session used direct source
reading. No subagents were used, no code index was created, and no workspace
mapping or evidence was modified.

## 2. Intent and friction ledger

### 2.1 How the burden survived each correction

| Date | Decision or change | Effect on the user's job |
| --- | --- | --- |
| 08-19 | Product design §5–6: explicit admission; fail-closed identity; "known mappings may be automated" | Automation was permitted but not assigned to anyone |
| 08-19 | Phase 17 plan: "add only the minimum mapping/persistence necessary"; unresolved identity is an exclusion reason | Minimum became a free-text operator form (`8e45c36`) |
| 08-20 06:52 | M10-D walkthrough: Binance `W` saved as `BTC`, version `1`; USDT mapped on both venues at 07:01 | Corrupt binding enters workspace state (observed in `research-universe.json`) |
| 08-20 | Cockpit investigation §10.2–10.4: identity should interrupt, not replace, research; evidence source "remains an open design decision" | Problem named, owner left open |
| 09-24 | Intuitive research plan §8: identity limited to wording and placement; a trusted identity service is "a separate design" | Explicitly scoped out |
| 09-24/25 | Console commits move the identity form inline into pair setup | Same burden, closer to the task |
| 09-27 | `ee9100d` shows mapping provenance and warns when codes differ | Makes the wrong mapping visible; still requires the user to judge it |

The pattern: every milestone preserved the fail-closed identity *contract* (correct)
and treated the manual *procedure* as part of it (not required by the spec). No plan
separated the two, so no plan could remove the procedure.

### 2.2 Friction ledger

| # | Reported friction | Reproduction | Root cause | Boundary |
| --- | --- | --- | --- | --- |
| R1 | `Wormhole` finds nothing | Observed; `matrix.ts` "Wormhole" → no match | Directory model has no name field; Gate `base_name` dropped in [gate_public.py](../../src/qap/market/adapters/gate_public.py) | Adapter → directory |
| R2 | `W` shows a BTC row | Observed; `W` → `W[W_USDT] \| BTC[WUSDT] \| …` | Stored mapping Binance `W → BTC`; picker labels the canonical ID | Workspace state |
| R3 | `BTC` leads to Wormhole data | Measured: `BTC` → first result `BTC[WUSDT]` | Mapped rows sort before unmapped rows ([researchAssetSearch.ts](../../web/src/features/discovery/researchAssetSearch.ts)); real `BTCUSDT` is unmapped | Picker ranking + state |
| R4 | Choosing DAI asks for a canonical ID and identity reference | Observed | [PairResearchSetup](../../web/src/features/discovery/PairResearchSetup.tsx) `IdentityConfirmation`; backend accepts any text ([set_identity_mapping](../../src/qap/product_universe.py)) | Identity contract |
| R5 | W/BTC pair fails with a generic error | API 409 "No supported venue has one unique current asset/USDT path" | W resolves only on Gate, "BTC" only on Binance, so no same-venue pair | Stored state + [pair study selection](../../src/qap/product_pair_study_data.py) |
| R6 | W/PIXEL "works" though no W/PIXEL market exists | API 200, venue Gate, data ready, direct unavailable, bridge needs authority | Relationship uses two same-venue USDT series; backtest needs two-leg USDT replay | Correct behavior, unexplained in the picker |
| R7 | Picker gives no hint that only USDT markets appear | Source-verified: projection and reviews include only `quote == USDT` | Scope rule is invisible | Presentation |
| R8 | Scan button disabled, link leads away | Observed: short horizon 0/3 ready, link to `/universe` | Scan page has no prepare action; `/universe` has none either; only Custom experiment calls `prepareProductMarketData` | Workflow ownership |
| R9 | Medium Scan "ready" on August 20 data | API: `ready_for_research: true`, cutoff 2026-08-20T04:00Z | No maximum-age rule in readiness ([product_current_approved.py](../../src/qap/product_current_approved.py)) | Freshness policy |
| R10 | Navigating to `/research` shows "Page not found" | Observed; nav "Research" points to `/scanner` | Route naming | Presentation |
| R11 | ETH, SOL, ADA searches list `3L/3S/5L` tokens | Measured | Gate leveraged tokens and stock tokens are ordinary directory rows | Eligibility |
| R12 | A saved study says "30 days", but the data may end weeks earlier | Source-verified | Pair readiness reuses the latest generation without topping it up | Freshness policy |

## 3. Discovery data flow

```text
Exchange response ─► adapter ─► CurrentSpotMarket ─► market-directory.json
   (names, chains,      (keeps code,    (venue, symbol,       5,907 rows
    buy_start, class)    symbol, status) base, quote, status)
        │
        ▼
research-universe.json (5 operator mappings) ─► ProductUniverse.projection
        │                                        3 assets + 2,825 unresolved codes
        ▼
/api/research-universe ─► researchAssetOptions ─► rank + top 16 ─► selection
        │
        ▼
resolved_scope (approved ∩ mapped ∩ trading) ─► same-venue USDT paths ─►
pair context / scan readiness ─► preparation (browser-triggered) ─► research
```

| Step | Owner | Dropped or filtered | Failure behavior |
| --- | --- | --- | --- |
| Binance adapter | [binance_public.py](../../src/qap/market/adapters/binance_public.py) | Nothing useful for identity; exchangeInfo has no names (measured, 3,713 symbols) | 429 raises; refresh aborts |
| Gate adapter | [gate_public.py](../../src/qap/market/adapters/gate_public.py) | `base_name`, `buy_start` (listing time), `type`, `st_tag`; `/spot/currencies` (name, chains, addresses, category, delisted) is never called | Raises; refresh aborts |
| Directory | [directory.py](../../src/qap/market/directory.py), [ProductUniverse.refresh_directory](../../src/qap/product_universe.py) | Publishes only when **both** venues succeed | One venue outage blocks both |
| Identity | `identity_mappings` keyed by (venue, code) → free-text canonical ID + free-text version | Every unmapped code, including each venue's USDT | Unmapped assets appear as "identity mapping needed" |
| Projection | `ProductUniverse.projection` | Non-USDT quotes; groups listings under whatever canonical ID was typed | Wrong mapping relabels the listing |
| API | [research_universe.py](../../src/qap/api/routes/research_universe.py) | No name, alias, class or listing time fields | — |
| Picker | [researchAssetSearch.ts](../../web/src/features/discovery/researchAssetSearch.ts) | Matches code, canonical ID, venue symbol only; `W/USDT` never matches; top 16 | "No current matching asset code" |
| Scope | `resolved_scope` | Unapproved, unmapped, non-trading, version conflicts | Plain string errors; cause type lost at the API boundary |
| Pair selection | `PairStudyDataReader.selection` | Needs both assets on one venue | One generic 409 for five distinct causes |
| Dataset identity | [product_market_data_prepare.py](../../src/qap/product_market_data_prepare.py) | Dataset ID embeds the typed identity versions (`binance-spot:WUSDT:1:1:4h`) | Changing identity changes dataset IDs |

Counts reconcile: Binance 3,681 stored markets and 484 trading USDT bases; Gate 2,226
stored markets and 2,079 trading USDT bases. After mapping: 3 canonical assets and
2,825 unresolved (venue, code) rows. History preparation is asset-agnostic once an
instrument resolves (source-verified), so identity is the gate on coverage. Data
acquisition is not.

Contamination from `W → BTC` (measured by searching all workspaces for the dataset
hashes): the mapping; generations `binance-spot:WUSDT:1:1:1h` and `:4h` in
`product-market-data/` and in the walkthrough copy, each with `base_asset: BTC`; one
walkthrough `catalog.json` entry. No run, scan, recipe or portfolio artifact
references them. The 4h generation is one of the two "ready" medium-scan paths, so
a medium scan today would treat Wormhole prices as BTC (inference from readiness
output).

## 4. Capability and coverage map

### 4.1 Sources

| Source | What it gives | Auth / limits | Measured coverage | Limits |
| --- | --- | --- | --- | --- |
| Binance `exchangeInfo` | Code, symbol, status | Public, weight 20 | 496 trading USDT bases; **no names** | No names, no class, no chain data |
| Binance `/sapi/v1/capital/config/getall` | Names, networks, contract addresses | Signed `USER_DATA`: needs an API key | Not measured (no key used) | Adds credential handling; policy decision |
| Binance undocumented `bapi` endpoints | Names | Public but undocumented | Not used | Not suitable as authority |
| Gate `/spot/currency_pairs` | `base_name`, `buy_start`, trade status | Public | Names for 2,071/2,071 tradable USDT pairs | Names are descriptive only |
| Gate `/spot/currencies` | Name, chains with contract addresses, `category`, `delisted` | Public | See 4.2 | 312 bases have no address (native coins or unknown) |
| CoinGecko `/coins/list?include_platform=true` | ID, name, symbol, contract address per chain | Keyless works for one call | 21,621 coins | 506 of Gate's bases share a symbol with another coin |
| CoinGecko `/exchanges/{id}/tickers` | Venue ticker → `coin_id` | Keyless: throttled to 429 after 3 fast pages; data cached 2 min; 100/page | See 4.2 | Needs a demo key or slow pacing; attribution terms apply |
| CCXT | Venue market lists | — | Not used | No economic identity; product spec §8 already rejects it as a truth source |

### 4.2 Measured resolution coverage (2026-09-27 snapshot)

Gate tradable USDT bases: 2,071 = 1,488 crypto + 420 leveraged tokens + 163 stock,
metal or forex tokens (Gate `category`).

For the 1,488 Gate crypto bases, matching Gate's contract addresses to CoinGecko
platform addresses gives:

| Outcome | Count | Share |
| --- | --- | --- |
| Address matches exactly one coin | 1,232 | 82.8% |
| Address matches several coins (bridged or wrapped variants, e.g. `USDC`, `WBTC`, `OP`) | 5 | 0.3% |
| Address has no registry match | 71 | 4.8% |
| No address; symbol unique in registry (weak evidence) | 106 | 7.1% |
| No address; symbol ambiguous (includes `ADA`, `AVAX`, `ALGO`) | 72 | 4.8% |
| No address; symbol unknown | 2 | 0.1% |

W: Gate `W` has one Solana address; exactly one registry coin (`wormhole`) shares it
(measured). CoinGecko's Wormhole tickers list Binance W/USDT, W/USDC, W/TRY and Gate
W/USDT.

The next table adds the registry's per-exchange ticker mappings
(`/exchanges/{id}/tickers`). Tickers in any quote currency count, because a venue
code means the same asset whatever it is quoted in. CoinGecko returned 1,359 Binance
and 1,681 Gate tickers, which is a subset of each venue's markets.

| Venue | Crypto USDT bases | One registry coin | Conflict | Unresolved |
| --- | --- | --- | --- | --- |
| Binance | 414 (496 minus 81 tokenized stocks and `EUR`) | 413 (99.8%) | 0 | 1 (`XNO`) |
| Gate, ticker mapping alone | 1,488 | 1,440 (96.8%) | 0 | 48 |
| Gate, address alone | 1,488 | 1,232 (82.8%) | 5 multi-match | 251 |
| Gate, address **or** ticker; conflict when they disagree | 1,488 | 1,459 (98.1%) | 8 (0.5%) | 21 (1.4%) |

Where both sources resolve, they agree on 1,197 codes and disagree on 8. The
disagreements show why one source is not enough:

- **Address evidence picks a wrapped or bridged token for five native coins:**
  `BTC → binance-bitcoin`, `ETH → binance-peg-weth`, `TLOS → wrapped-telos`,
  `NXPC → bridged-nxpc`, `XRD → e-radix`. Gate lists a BSC or other bridged contract
  address for these coins. The ticker mapping is correct in each case. A precedence
  rule resolves them: the registry's own mapping for that venue code wins over an
  address match to a wrapped or bridged representation of the same asset.
- **Three are migrations:** `DYDX` (`dydx` vs `dydx-chain`), `GAT`, `HOLDSTATION`
  (`holdstation` vs `holdstation-2`). These are the rename/migration cases the spec
  requires to fail closed. They should go to review with evidence attached.

Cross-venue: 393 tickers trade against USDT on both venues. 389 resolve to the same
coin on both, 4 cannot be determined, and **none** resolve to different coins in
this snapshot. `W`, `BTC` and `PIXEL` resolve to `wormhole`, `bitcoin` and `pixels`
on both venues. DAI has no registry ticker on either venue (Binance DAIUSDT is in
`BREAK`; Gate has no DAI/USDT pair).

Limits of this measurement: one snapshot; the registry flags 71 Binance and 78 Gate
matched codes as stale or anomalous on some ticker; keyless access hit rate limits
(Section 4.1). The quantified residue for ordinary use is 1 Binance and about 24 Gate
crypto codes (21 unresolved plus 3 migrations), under 2% of the combined crypto
listings.

### 4.3 Proposed identity ownership model

The requirement is not "an identity for everything". Different capabilities need
different identity:

| Capability | Identity actually needed |
| --- | --- |
| Find and display a listing | None beyond the venue's own code and symbol |
| Relationship study on one venue | Venue-local identity: this symbol's history is one continuous market |
| Group Binance and Gate listings as one asset | Cross-venue economic equivalence |
| Admission ("willing to own"), scans across venues, portfolios | Economic identity with a version |

The proposed contract, which needs owner approval (Section 10, D1):

1. **Listings are always discoverable** with name, venue, symbol, listing time and
   status. Discovery never waits on identity.
2. **A resolver owned by the Product layer** proposes bindings from evidence. It
   auto-accepts a binding when the evidence is strong and consistent: the registry's
   own ticker mapping for that venue code, or a venue-supplied contract address that
   matches exactly one registry coin, with no conflicting evidence. When the two
   disagree only because the address points at a wrapped or bridged form of the
   same asset, the ticker mapping wins (measured: BTC and ETH on Gate). Any other
   disagreement goes to review with both pieces of evidence attached.
3. **Cross-venue equivalence** is accepted only when both listings resolve to the same
   registry coin. Ticker equality alone never merges listings.
4. **The identity version is evidence-derived** (registry ID plus a fingerprint of the
   contract/chain set), not typed text. A contract migration or registry change
   produces a new version and never relabels old data.
5. **`ProductUniverse` stays the single authority** for accepted bindings and
   admission. The resolver writes proposals with evidence; `ProductUniverse`
   accepts them under the policy. There is no second registry of truth.
6. **Uncertain listings stay visible.** Only the capabilities that need the missing
   identity are unavailable, with the reason stated. Manual review is the exception
   path for conflicts, not the ordinary way to add an asset.
7. **USDT as the quote coordinate is seeded by policy** on both venues. The
   product spec already treats it as a protocol coordinate. Asking every workspace
   to type it is a chore.

### 4.4 Legacy reconciliation

A reconciliation preview runs the resolver against existing mappings before any
change:

- `binance:W → BTC` conflicts with evidence (Binance `W` resolves to `wormhole`).
  It is quarantined. It becomes `W` under a new evidence version; it is never
  edited in place.
- The two contaminated generations keep their dataset IDs and provenance and are
  marked with an integrity note ("recorded as BTC; evidence shows Wormhole"). They
  are excluded from new research and never relabeled as valid BTC or W history.
  Fresh W generations are acquired under the new binding.
- `gate:W → W`, `gate:PIXEL → PIXEL` and both USDT mappings agree with evidence and
  migrate to evidence versions. New dataset IDs follow the new versions; old IDs
  remain readable for saved results.
- Admission (`BTC`, `PIXEL`, `W` approved) carries over by canonical asset. The
  owner must re-confirm `BTC`, because that approval was made while BTC meant
  Wormhole's listing (Section 10, D6).

## 5. Responsibility and decision record

| Prompt or field today | Where | What it really is | Proposed owner |
| --- | --- | --- | --- |
| Canonical asset identifier (free text) | Pair setup, `/universe` | Identity binding | **Product automation** (resolver); review only on conflict |
| Identity version or reference (free text) | Pair setup, `/universe` | Evidence version | **Product automation** (derived) |
| USDT quote mapping | Pair setup "Finish price-data setup" | Protocol constant | **Product automation** (policy seed) |
| "Allow X in research" | Pair setup | Willingness to own; suitability is the user's judgment (spec §5) | **User choice**; ask once, in context, with name and venues shown |
| "Allow workspace bridge replay" | Backtest | Permission to hold transient USDT during two-leg replay | **User choice**; genuine and workspace-wide; ask once at the first backtest that needs it |
| Load/refresh available markets | Pair setup, `/universe` | Directory maintenance | **Product automation** (refresh on open when stale, per venue) |
| History preparation | Pair: automatic after Start; Scan: none; Custom: button | Data acquisition | **Product automation** inside the research request, with visible progress |
| Venue choice | Implicit (first available) | Real choice only when both venues qualify | **Optional inspection**, default chosen by backend |
| Period (30/90/180 days) | Pair setup | Research choice | **User choice** |
| Relationship vs Backtest | Pair setup | Research choice | **User choice** |
| Recipe parameters | Backtest settings | Research choice with defaults | **User choice**, optional |
| Final-OOS compilation SHA-256, research family ID, derived-from recipe SHA-256 | [ExperimentLab](../../web/src/features/discovery/ExperimentLab.tsx) | Lineage | **Product automation**: pick a previous experiment; backend derives hashes. Hashes remain visible as audit detail |
| Freeze UTC timestamp, candidate IDs | Legacy strict-scanner pages ([DiscoveryHome](../../web/src/features/discovery/DiscoveryHome.tsx), [CandidateDetail](../../web/src/features/discovery/CandidateDetail.tsx)) | Expert PIT controls | **Expert only**; keep under Advanced Research |
| Leveraged tokens, stock tokens in picker | Picker | Outside action space (leverage, synthetic exposure) | **Genuinely unsupported**: excluded by eligibility policy (Section 10, D4) |

Retry and interruption (source-verified in [PairResearch.tsx](../../web/src/features/discovery/PairResearch.tsx)):
the whole resolve → prepare → context → series → recipe → check → run chain runs in
one browser mutation. Reloading mid-preparation loses progress. The backend
preparation and operation owners already exist, so the chain can move server-side
without a new job ledger. Chart retry refetches the series only and cannot rerun
the experiment (source-verified). Backtest results are durable backend operations;
relationship reads are recomputed and are not saved results (console plan, §"saved
result" rules). A rerun therefore needs to show its new cutoff explicitly.

The optional "BTC reference" lens hardcodes the canonical ID `BTC`
(`analysisReference: 'BTC'` in PairResearch.tsx). In any workspace with the
`W → BTC` mapping, that lens reads Wormhole's Binance listing (source-verified,
inference for the effect). This is a second contamination path besides search.

## 6. Experience and test findings

- **Search**: exact-symbol matches are correct for mapped rows only. Name search is
  impossible. Mapped rows outrank everything, which turns one bad mapping into the top
  result for two different queries (R2, R3). The same asset appears twice when only one
  venue is mapped (`PIXEL` Gate mapped, `PIXEL@binance` unmapped).
- **Blocked states**: Scan's disabled primary button explains the cause but offers no
  in-place fix (R8). The pair error loses the specific cause (R5).
- **Freshness**: the UI says "trailing completed history", but nothing guarantees the
  trailing end is recent (R9, R12).
- **Tests protect the rejected contract**:
  [ResearchStudyWorkspace.test.tsx](../../web/src/features/discovery/ResearchStudyWorkspace.test.tsx)
  types `USDT` and `verified-record-v1` into the identity form and asserts that it
  saves. Fixtures start from pre-approved Gate-only assets with `${asset}-verified`
  versions. [ResearchAssetSelector.test.tsx](../../web/src/features/discovery/ResearchAssetSelector.test.tsx)
  asserts a warning for a BTC record backed by WUSDT, so it accepts the corrupt state
  as a valid display case. The four Playwright specs in `web/e2e/` cover pair anchor,
  portfolio and slice-4 flows. None starts from an empty workspace or covers the
  console's first use.
- **Protect what is right**: identity fail-closed behavior, dataset lineage, HODL and
  simple-rebalancing benchmarks, the bridge-authority scope and chart-retry isolation
  all have unit coverage that the redesign must keep.

## 7. Scenario matrix results

| Scenario | Result today | Cause |
| --- | --- | --- |
| `W`, `w` | Gate W first, then "BTC" (Binance WUSDT) | Stored mapping |
| `Wormhole`, `wormhole` | No match | No names |
| `WUSDT`, ` wusdt ` | "BTC" first | Stored mapping + symbol match |
| `W_USDT` | Gate W first | Symbol match |
| `W/USDT` | No match | No alias normalization |
| `BTC` | Mislabeled WUSDT first; real BTC rows unmapped; then `BTC3L`, `BTC3S` | Ranking + state + eligibility |
| `Bitcoin`, `Ethereum` | No match | No names |
| `DAI` | One unmapped Binance row, status `BREAK` (not trading); Gate has no DAI/USDT | Status not shown; identity form |
| Other assets (e.g. `SOL`, `ADA`) | Unmapped rows plus leveraged variants | No automation; eligibility |
| Venue-exclusive asset | Gate-only bases: 1,678 of 2,071 USDT bases have no Binance twin by ticker (measured) | Works only through manual mapping |
| Duplicate ticker, rename | Across venues, 389 of 393 shared tickers resolve to the same coin and 0 to different coins (4 undetermined). Registry-wide, 506 Gate codes share a symbol with another coin. 3 Gate codes show migration conflicts (`DYDX`, `GAT`, `HOLDSTATION`) | Ticker ≠ identity |
| Empty workspace | "Load available assets", then manual USDT mapping, then per-asset mapping and approval | Contract |
| Conflicting workspace | Reproduced (walkthrough copy) | Stored state |
| W/BTC | 409 generic error | No common venue under current mappings |
| W/ETH, BTC/DAI | 409 "Selected Product assets are not approved" | Admission and mapping |
| W/PIXEL | Relationship ready on Gate; backtest needs bridge authority | Correct, unexplained upfront |
| Scan, missing 15m history | Disabled; link to `/universe`, which cannot prepare | No owner |
| One exchange down | Directory refresh fails for both | All-or-nothing publish |
| Stale history | Medium scan runs on data ending 2026-08-20 | No freshness rule |

## 8. Target journeys and acceptance cases

Each case must pass in the rendered app, starting from an **empty workspace**, with no
developer help:

1. **First use.** Open Research. Markets load on their own. Type `Wormhole` and see
   "Wormhole (W) · Binance · Gate". Type `Bitcoin` and see BTC. Pick both, then 90 days,
   then Start. The only question asked is "Allow W and BTC in research?". The
   relationship result appears with its data cutoff and venue.
2. **Market alias.** `WUSDT`, `W_USDT`, `W/USDT` and `w/usdt` all lead to Wormhole
   and show which venue's market was typed. No query can surface W data under a BTC label.
3. **Deeper research.** From the result, choose "Backtest this pair". A one-time,
   workspace-wide bridge permission is shown if needed. The comparison runs against HODL
   and simple rebalancing. Changing a parameter keeps the pair and the previous result.
4. **Scan.** Choose Scan with 15m history missing. Start prepares the data with visible
   progress, then runs. Excluded assets are listed with reasons before results.
5. **Unfamiliar and venue-exclusive assets.** Pick a Gate-only asset that was never
   touched before (chosen at test time from the live directory) and complete a
   relationship study with no mapping step.
6. **Uncertain identity.** Pick an asset whose evidence conflicts or is missing. The
   picker shows it with "identity unconfirmed" and the reason. Relationship on its own
   venue is available if the policy in D2 allows it. Cross-venue features are off, with
   an explanation.
7. **Failure recovery.** With one exchange unreachable, the other venue's listings stay
   usable and the outage is named. An interrupted preparation resumes after reload
   without duplicating work.
8. **Return visit.** Reopen a saved study. It shows its original result and cutoff. A
   rerun shows the new cutoff and never overwrites the old result.
9. **Legacy workspace.** Open the walkthrough workspace. The reconciliation preview
   shows the `W → BTC` conflict. After acceptance, `BTC` search shows Bitcoin, and old
   generations carry the integrity note.

Tests to retire or rewrite: the manual USDT-mapping workspace test and the
"BTC backed by WUSDT" warning test. New coverage: resolver unit tests over recorded
source snapshots (W, BTC, DAI, a duplicate ticker, a migrated token, a leveraged
token), API contract tests for typed blocker causes, and Playwright journeys 1, 4, 7
and 9.

## 9. Architecture options

| | A. Focused repairs | **B. Evidence-backed resolution + backend research requests** | C. External market-data platform |
| --- | --- | --- | --- |
| What | Keep Gate names, fix ranking, quarantine W→BTC, add a Scan prepare button | Resolver + evidence bindings in `ProductUniverse`; typed availability; server-side request orchestration; freshness and eligibility policies | Replace adapters with a vendor or CCXT |
| Fixes R1–R12 | R1 (Gate only), R3, R8, R10 | All | Few; CCXT has no identity |
| Coverage without per-coin work | No; every asset still needs manual mapping | Yes, measured in Section 4 | Unknown; vendor-dependent |
| Risk | Low, but repeats the September pattern | Medium: policy amendment, migration | High: new truth source, cost, terms |
| Reuse | All current code | Adapters, directory, `ProductUniverse`, preparation, operations, recipes, execution, evaluation | Little |

**Recommended: B**, delivered in this order:

1. Owner decisions D1–D7.
2. Adapter and directory keep names, listing time, class and chain data. Per-venue
   directory publishing, so one outage does not block the other.
3. Resolver with recorded source snapshots, evidence versions and a reconciliation
   preview (read-only first). Registry client behind one interface, so the source can
   change.
4. Eligibility filter (D4) and USDT policy seed (D3).
5. Search API that returns names, aliases, venues, status and a typed availability per
   capability. The picker consumes it and derives no identity or readiness itself.
6. Backend research request: one submitted intent (assets, question, period) that the
   backend resolves, prepares, runs and resumes, using the existing preparation,
   recipe and operation owners. Single-flight, safe retry, typed blocker causes.
7. Scan and Custom experiment use the same request path. Lineage fields become
   "choose a previous experiment".
8. Screen redesign and prototype review on top of the real contract.
9. Acceptance journeys (Section 8) and human walkthrough.

The overhaul proposal's hypotheses hold up: a catalog/search API with no identity
authority, `ProductUniverse` as the single binding authority, typed resolution
outcomes and feature-specific orchestration without a new job ledger are all
supported. The investigation changes two things. Browser-initiated preparation is
not enough, because the chain must survive reloads. A bounded reviewed catalog is
unnecessary, because automatic evidence covers most assets.

## 10. Decisions

These touch identity, universe eligibility, freshness or source roles, so AGENTS.md
requires owner approval.

**Decided 2026-09-27:** Hamza delegated all seven to the recommendations below.
They are recorded, with their implementation consequences, in the
[Phase 18 decision log](../plans/18-research-experience-and-asset-resolution.md#2-decision-log).
D4 was decided as: exclude leveraged tokens and tokenized stocks, metals and
forex tokens.

| ID | Decision | Recommendation |
| --- | --- | --- |
| D1 | Amend product spec §6: evidence-backed automatic identity binding (Section 4.3) replaces operator authorship as the ordinary path | Approve |
| D2 | May a relationship study run on venue-local identity when cross-venue equivalence is unresolved? | Approve; economic replay, admission-dependent scans and portfolios still need full identity |
| D3 | Seed USDT quote identity by policy on both venues | Approve |
| D4 | Exclude leveraged tokens from discovery as outside the action space; decide on tokenized stocks, metals and forex tokens | Exclude leveraged tokens. Exclude tokenized stocks too, as synthetic exposure, unless you want them |
| D5 | Supplemental registry: CoinGecko (free demo key, attribution) as the first registry, behind an interface; whether to add a read-only Binance API key for Binance names and addresses | CoinGecko demo key now; defer the Binance key |
| D6 | Legacy reconciliation: quarantine `W → BTC`, integrity-mark the two generations, re-confirm BTC admission | Approve |
| D7 | Freshness: new research tops up history to the latest completed bar before running; readiness older than a threshold (e.g. two graph intervals) is "needs refresh" | Approve; a saved result keeps its original cutoff |

Admission itself (spec §5, "willing to own") stays a user decision. The recommendation
only changes when and how it is asked.

## 11. Unknowns and bounded next steps

| Unknown | Next step |
| --- | --- |
| Binance names and addresses without a key | Covered indirectly through registry tickers (Section 4.2); measure `capital/config/getall` if D5 adds a key |
| Registry demo-key limits and terms in practice | Register a demo key; confirm limits, attribution text and caching rules before implementation |
| Other registries (CoinPaprika, CoinMarketCap) | Measure only if the D5 source proves insufficient |
| Exact prior selection behind the original pair-error screenshot | Cannot be recovered. R5 reproduces the same message and cause |
| Timing and comprehension of the redesigned flow | Human walkthrough at step 9; no invented metrics |
| Renames and migrations over time | Record two source snapshots a week apart during resolver development; test version changes against them |
