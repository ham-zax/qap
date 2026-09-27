# QAP Research Product — Investigation Before Redesign

**Date:** 2026-09-27

**Status:** Investigation executed. Results are in the
[investigation findings](2026-09-27-research-product-investigation-findings.md).
Decisions and the resulting plan are in
[Phase 18](../plans/18-research-experience-and-asset-resolution.md).

**Source baseline:** `ee9100d` on `feat/research-study-workspace`, with existing
staged work preserved.

Update context — 2026-09-27 (investigation executed)
Trigger: sections A–F and the scenario matrix were carried out.
Purpose: link this plan to its results without rewriting the plan.
Impact: none on the plan's method. Preliminary findings F1–F9 below are confirmed
and extended in the findings report.
Evidence: [investigation findings](2026-09-27-research-product-investigation-findings.md).

Update context — 2026-09-27
Trigger: Hamza rejected the research experience and clarified that normal use must
not require manually adding coin support, authoring identity records, or checking
hashes/evidence. He requested investigation before a master redesign plan.
Purpose: establish how to discover the causes of the friction and the feasibility
of the desired experience before choosing screens or architecture.
Impact: the [overhaul proposal](../superpowers/plans/2026-09-27-research-experience-overhaul.md)
becomes provisional design hypotheses. Its catalog, navigation and orchestration
choices must be tested by this investigation; a manually maintained coin list is
not the accepted answer to asset coverage.
Evidence: supplied QAP/Uniswap screenshots, this conversation, the historical plans
and source linked below, and read-only inspection of local workspace mappings.

## 1. The experience we are investigating

Hamza wants a research application where he can find an asset, ask a question,
run it, understand the result, change assumptions, and continue into deeper work.
The app should handle the machinery that makes those actions possible.

Concrete requirements to carry into the investigation:

- Typing `W` or `Wormhole` should find the intended asset and its available Binance
  and Gate listings. Searching an observed market such as `WUSDT` should preserve
  that listing's identity and make the venue clear. A wrong saved mapping must not
  turn the result into Bitcoin.
- Coverage should follow supported exchange listings through a general ingestion
  and resolution process. The researcher should not configure every coin, and a
  developer should not need to add code or a hand-written allowlist entry for each
  ordinary new asset.
- QAP should obtain and validate the metadata and provenance its backend needs.
  Research must not depend on the user inventing canonical IDs, identity versions,
  finding contract evidence, copying hashes, or preparing files.
- Selection, necessary preparation, results, retry and further experimentation
  should retain the same research question. Routine failure must not send the
  researcher hunting through settings for an unexplained repair.
- Simple initial actions must lead into powerful research: relationship analysis,
  backtests, scans, supported custom methods, comparison and saved work. Expert
  controls must be discoverable when relevant and preserve the current context.
- Actual research choices belong to the user. Determine which existing permission
  prompts represent meaningful choices and which expose implementation chores.

The reference screenshots establish an interaction standard: recognizable assets,
clear primary actions, readable results and contextual complexity. They do not
specify a QAP theme, navigation structure, wallet flow or trading product.

Discovery, scientific support and permission to simulate ownership are distinct
questions. Discovering a listing must not require pretending every listed asset
has sufficient history or every requested method can run. Genuine limitations
need a specific explanation and an available next action.

## 2. What repository inspection already establishes

These are starting findings, not a claim that the investigation is finished.

| ID | Finding and evidence | Consequence for investigation |
| --- | --- | --- |
| F1 | The [August 20 investigation](2026-08-20-qap-research-cockpit-investigation.md) already records `W vs BTC/ETH`, poor exact-symbol search and identity administration interrupting research. The [September 24 plan, section 8](../superpowers/plans/2026-09-24-intuitive-research-experience.md) explicitly limits identity changes to wording/placement. | Explain why successive corrections preserved the same burden. Do not assume another presentation pass addresses it. |
| F2 | The current [directory model](../../src/qap/market/directory.py), [API DTOs](../../src/qap/api/product_schemas.py) and [search options](../../web/src/features/discovery/researchAssetSearch.ts) contain codes/market symbols, but no full asset name or alias metadata. | `Wormhole` cannot match through this contract. Establish where name metadata should come from; do not assume the existing exchange responses contain it. |
| F3 | [Binance](../../src/qap/market/adapters/binance_public.py) reads `/api/v3/exchangeInfo`; [Gate](../../src/qap/market/adapters/gate_public.py) reads `/spot/currency_pairs`. Both normalize venue codes, market symbols and trading status into directory observations. | Trace the data actually available and fields retained at every boundary, then investigate additional metadata only where needed. |
| F4 | Read-only inspection of both `runs/product/research-universe.json` and the isolated walkthrough copy found Binance `W → BTC`, Gate `W → W`, with identity version `1`. [ProductUniverse.projection](../../src/qap/product_universe.py) groups resolved listings under the recorded canonical ID; search labels that ID. | Separate wrong persisted state from absent listing data and ranking defects. Determine origin, affected datasets and reconciliation requirements without rewriting records during investigation. |
| F5 | [ProductUniverse](../../src/qap/product_universe.py) requires base and quote mappings to resolve a market. Admission requires a known canonical mapping. `refresh_directory` publishes only after both venue requests complete. | Investigate quote-identity dependencies, first-use initialization, refresh policy and single-venue outage behavior. A directory refresh alone does not supply economic identity. |
| F6 | [PairResearchSetup](../../web/src/features/discovery/PairResearchSetup.tsx) asks for independently checked canonical IDs and identity references. Its text says references are not independently validated. | Establish how the product can own identity resolution. Moving this form into a modal would retain the burden the user rejected. |
| F7 | [PairStudyDataReader.selection](../../src/qap/product_pair_study_data.py) emits a generic error when no venue has exactly one required path for each asset. [PairResearch](../../web/src/features/discovery/PairResearch.tsx) can prepare missing history after context resolution, but initial context failure happens before that preparation. | Trace missing mapping, quote, admission, listing and ambiguity separately. Identify where cause and recovery information are lost. The exact runtime cause of the final supplied pair-error screenshot remains unconfirmed. |
| F8 | [ProductResearch](../../web/src/features/discovery/ProductResearch.tsx) requires ready scan scope before launch and presents readiness separately. | Verify the complete scan journey from missing history through acquisition to execution; identify the owner of preparation and resumption. |
| F9 | [Selector tests](../../web/src/features/discovery/ResearchAssetSelector.test.tsx) check warning visibility for a BTC record backed by WUSDT. [Workspace tests](../../web/src/features/discovery/ResearchStudyWorkspace.test.tsx) explicitly require manually entering a USDT identity reference. | Existing green tests can protect the current contract while failing the desired product contract. Audit what the fixtures assume and what success actually proves. |

The stabilization commit `ee9100d` made mapping provenance more visible. It did not
introduce full-name discovery or automatically validate those mappings. These
problems predate the newest screen layout.

The preliminary investigation checked Satori availability; the latest status call
failed with a closed transport. Findings above were verified against local source.
No new index, subagent, external listing verification or fresh browser acceptance
is claimed. The screenshots remain user-supplied observations.

## 3. Investigation order and required evidence

### A. Recover the intended product and the decisions that shaped it

Read the [master implementation plan](../superpowers/plans/2026-08-17-qap-master-implementation-plan.md),
[Phase 17](../plans/17-product-layer-market-data-and-research-lifecycle.md),
[August 19 product investigation](2026-08-19-qap-product-layer-investigation.md),
August 20 investigation, September 24/25 plans, their implementation commits, and
the current proposal. Trace relevant changes through Git rather than relying on
completion labels.

Build a short timeline: user job → accepted requirement → scoped-out dependency →
implementation → verification → actual walkthrough outcome. Record where the
product promise depended on work no milestone owned. Distinguish constitutional
constraints, scientific contracts, temporary implementation choices and assumptions.

**Output:** an intent/decision ledger explaining repeated misses and the constraints
that a redesign must either preserve or explicitly amend.

### B. Reproduce the reported friction in controlled workspaces

Use a clean local workspace, a correctly populated workspace, and a copy containing
the observed conflicting mappings. Record commit, workspace, API origin, directory
observation time, history cutoff and browser state for each result. This prevents
stale data or a different backend from masquerading as a code defect.

For each journey record what the person tried, what was visible, the action taken,
the relevant API response, actual blocking condition, recovery, and retained/lost
context. Capture time spent waiting, unexplained disabled actions, admin detours,
required jargon and developer intervention. Screenshots and timing are observations,
not invented usability scores.

**Output:** reproducible cases linked to each supplied failure, including unknowns
when an exact prior selection cannot be recovered.

### C. Trace discovery from exchange response to research selection

Follow this chain for the same assets in each workspace:

```text
Exchange metadata → adapter → stored directory → identity/admission projection
                 → API response → picker matching/ranking → selected asset
                 → pair/scan availability → preparation → research inputs
```

At every step record the owner, input/output fields, dropped information, filters,
cache/freshness behavior, manual prerequisites and failure semantics. Reconcile
listing counts between steps. Check whether both venues remain distinguishable
after canonical grouping and whether exact market search retains its source.

Inspect refresh callers and defaults: initial load, cached load, retry, rate limits,
one source unavailable, stale snapshots and new listings. Determine whether directory
freshness and historical-data readiness are incorrectly conflated in presentation.

**Output:** a concrete data-flow map and a cause for every missing, misleading or
unselectable search result. Local observations do not prove current live listings.

### D. Establish scalable metadata and identity feasibility

Investigate official Binance/Gate metadata capabilities first. For any missing
names, aliases or identity information, evaluate appropriate supplemental sources.
Verify documentation and sample responses; record provenance and capture results
using the repository's research workflow. No competitor-site browsing is needed.

Compare options using the same questions:

- Can names, venue symbols and stable asset identity be connected programmatically?
  Which evidence is actually available for native coins and multichain tokens?
- Can the system handle both exchanges, newly listed assets and unfamiliar coins
  without a deployment or someone authoring each binding?
- What are measured coverage, uncertainty, freshness, authentication, cost, rate
  limits, redistribution terms, outage behavior and maintenance burden?
- How are duplicate tickers, aliases, renamed/migrated tokens, contract changes,
  wrapped representations and conflicting records handled?
- What needs a stable venue-local identity, and where is cross-venue economic
  equivalence genuinely required? Can uncertain listings remain discoverable while
  only the dependent capability is unavailable?
- How are source changes validated internally? How can legacy mapping conflicts
  be reconciled without relabeling old datasets or corrupting saved results?

Consider venue-owned metadata, supplemental registries and combinations on evidence.
Do not preselect a provider or replace the user's problem with a small curated coin
catalog. Similar tickers, names and logos alone do not establish equivalence. If
automatic coverage has a real limit, quantify it and describe the product behavior;
do not make manual identity authorship the ordinary fallback.

**Output:** source/coverage comparison, a proposed identity ownership model, migration
requirements and the explicit policy decisions needed before implementation.

### E. Audit every prerequisite and interruption across research

Walk relationship research, backtesting, scanning, custom experiments and saved
research. Inventory every field, confirmation, technical identifier and detour.
For each, ask:

1. What user decision does this represent, and what consumes the answer?
2. Is it needed for this task now, or only for a later capability?
3. Can QAP derive, fetch, validate or remember it under an explicit policy?
4. If a choice is genuinely required, can it be expressed where it matters using
   recognizable assets, dates, methods or previous research?
5. If it blocks progress, is the cause specific and can the task resume after repair?

Include base/quote mapping, research admission, transient USDT authority, venue
selection, history windows, preparation/refresh, recipe support, data bindings and
experiment lineage. Audit hash fields in advanced authoring as well as ordinary
screens: selecting a previous experiment may allow the backend to derive lineage.
Distinguish displayed audit detail from information users must supply or verify.

Follow existing preparation, operation and result owners before proposing new
orchestration. Check repeat clicks, retry, interruption, refresh/reopen, changed
inputs and source failure. Verify that fixing chart retrieval cannot rerun an
experiment, and changing settings cannot relabel an old result.

**Output:** a responsibility table: user choice / product automation / optional
inspection / genuine unsupported case, with evidence and any policy amendment.

### F. Evaluate the whole experience and its tests

Assess the initial screen, picker, waiting state, first useful result, settings,
failure/retry and return visit as one journey. Check the prominence of the primary
action, understandable defaults, responsive hierarchy, keyboard/focus behavior and
whether the user can explain the result and next action without coaching.

Inspect frontend fixtures, API contracts and integration/browser coverage. Identify
where tests start with preapproved identities, prepared data or mocked success;
where they assert a label instead of task completion; and where a technical test
enshrines a rejected interaction. Retain financial/provenance regression protection
while proposing new product acceptance coverage.

**Output:** observed experience failures and a verification strategy covering first
use and recovery. A prepared W/PIXEL demonstration cannot establish general coverage.

## 4. Mandatory scenario matrix

| Scenario | Question the investigation must answer |
| --- | --- |
| `W`, `w`, `Wormhole`, `wormhole` | Do these discover the intended asset, with Binance and Gate availability when observed? Is exact identity prominent among substring matches? |
| `WUSDT`, `W_USDT`, `W/USDT`, mixed case/whitespace | Can observed market aliases find the correct listing and related asset without unsafe string stripping or a BTC mislabel? |
| `BTC`, `Bitcoin`, `DAI` and full-name lookup | Does a familiar asset work without manually authoring identity/quote records? Is any actual data or method limitation stated accurately? |
| Assets selected from both venue directories beyond the existing demo set | Does the system generalize without adding per-coin code, prepared fixtures or mappings by hand? Include a venue-exclusive asset. |
| Duplicate ticker, rename, inactive/delisted market, newly observed listing | Can the user identify the intended asset while the backend avoids unsafe merges and explains unavailable history? |
| Empty, populated, stale and conflicting workspace state | Which failures are onboarding, cache, stored-state or contract problems? Can the product recover without hidden operator work? |
| `W/BTC`, `W/ETH`, existing `W/PIXEL` relationship → backtest | Where do descriptive analysis and economic execution acquire different prerequisites? Can the person progress and understand both? |
| No common venue, missing quote mapping, ambiguous market path | Does each distinct cause reach the user with a specific next action and retained selections? |
| Scan from empty scope or missing 15m history | How is scope chosen, data prepared and work resumed? Are exclusions and any scope changes visible before the research claim is made? |
| Exchange outage, stale directory/history, interrupted preparation | Is the failure isolated, freshness honest and retry bounded? Does one unavailable source unnecessarily hide the other? |
| Change method/period, inspect a negative result, retry, reopen history | Are settings discoverable, benchmark results understandable, original inputs retained and duplicate runs avoided? |

This is a bounded core matrix. Add cases only when evidence reveals another failure
mechanism. Live listing status and supported method/data coverage must be measured;
the named scenarios are investigation targets, not promises that every run succeeds.

## 5. Evidence discipline and working boundaries

- Work directly, without subagents. Use Satori for unfamiliar behavior when ready;
  use source inspection if unavailable. Use Codebase Memory only for a distinct
  structural question with its required coverage checks. Indexing is authorized
  if needed; indexed navigation does not replace checking relied-on source.
- Preserve current user changes and original workspace evidence. Perform writes
  needed for reproduction only in disposable workspaces. Do not repair mappings,
  grant ownership permission, or mutate historical evidence to make a demo pass.
- Label findings as **observed**, **source-verified**, **inference** or **unknown**.
  Record the environment and exact source/response supporting each causal claim.
  Use focused probes where necessary; do not run broad suites to prove a UX claim.
- Keep owned-spot action space, financial state ownership, benchmark/cost semantics,
  holdout rules and the live-capital NO-GO intact. Investigate identity, admission
  and freshness policies explicitly; do not silently promote every old UI step
  into a permanent invariant or silently change eligibility.

## 6. What must exist before the master plan

Keep findings together in a focused report with supporting artifacts as needed:

1. **Intent and friction ledger:** every supplied failure, the desired task, a
   reproduction or stated unknown, root cause and responsible boundary.
2. **Capability and coverage map:** what each exchange/source and existing QAP
   component actually supplies, automation feasibility and unresolved limits.
3. **Responsibility and decision record:** work QAP must own, real user choices,
   legacy migration needs and any proposed contract/policy amendments.
4. **Target journeys and acceptance cases:** first use, normal use, deeper research,
   failure recovery and return visits, including unfamiliar assets.
5. **Architecture options and recommendation:** compare focused repairs with
   changes to discovery/resolution and workflow boundaries. State why the proposed
   scope addresses the causes; identify reusable components and replacements.

Only then write the master plan. Every proposed feature or architectural change
must trace to a finding and acceptance case, with dependency order, migration,
failure behavior and verification. Validate interaction sketches against the real
data/capability constraints before committing to layout or component structure.

The investigation is ready to support that plan when each major friction has an
evidenced explanation, automatic asset coverage has a credible path or a quantified
limit, user responsibilities are explicit, and the required policy decisions are
visible. Remaining unknowns must have a bounded next step. Another polished
fixture-backed walkthrough is insufficient evidence of that readiness.
