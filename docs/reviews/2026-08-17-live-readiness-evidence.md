# QAP Live-Readiness Evidence Ledger

**Review date:** 2026-08-17

**Decision supported:** `NO-GO`

This file records the concrete local artifacts, commands, current official venue sources, and unresolved operational/legal questions used by the Phase-12 readiness review. It does not authorize private API access or live order placement.

## 1. Economic/research evidence

### Predeclared development family

- Research family: `phase10-btcusdt-daily-momentum-2023-v1`
- Precommit: `docs/research/2026-08-17-phase10-momentum-family-precommit.json`
- Result note: `docs/research/2026-08-17-phase10-momentum-family-results.md`
- Development data: `tests/fixtures/market/BTCUSDT_1d_2023.parquet`
- Development semantic fingerprint: `0cff5a7068c2d3e7957b481f826ce8ca80956191873671035a08353cfdb4d5fc`
- Development attempts: `9`
- Development survivors: `0`
- Core result: every core member is negative versus strict HODL after the declared modeled costs.

Durable local run IDs in the frozen family:

1. `run-226112400b25ce2fb57fdc23`
2. `run-318a83af16b67f160024efc2`
3. `run-aca063dfd2bbb6900dc095ca`
4. `run-eb02105fb8a9d24c9917b8b7`
5. `run-7106cd158a8a4edd7bf65084`
6. `run-bd698e79e981bbb708b17134`
7. `run-9a13ebf22a6fb42ec88734f5`
8. `run-20574b31b3d0c65dfc4acfb4`
9. `run-f047103cecf378d53190c7b6`

The nine run artifacts report clean execution provenance from commit `7cef139a0feaaeefcc3eed50aba32b3fe087576c` with `git_dirty=false`, as recorded in the Phase-10 result note.

### Reserved final-OOS data

- Reserved file: `tests/fixtures/market/BTCUSDT_1d_2024.parquet`
- Window: `[2024-01-01T00:00:00Z, 2025-01-01T00:00:00Z)`
- Bars: `366`
- Semantic fingerprint: `b3069c70fb61f1e7fb6a8b1d338194817ba8896dfd2618b96091c8c46686f2a5`
- Candidate final-OOS commitment count: `0`
- Candidate final-OOS consumption status: **unconsumed**
- Storage metadata after `4e85044`: `qap_evidence_role=role_neutral_market_data`; the experiment manifest/commitment protocol, not Phase-02 storage, owns research-role semantics.

Because the predeclared development survivor count is zero, there is no candidate eligible to consume the reserved final-OOS window.

### Prospective evidence

There is no genuinely prospective candidate evaluation. Current paper-operation artifacts are mechanically derived as:

- `evidence_class=operational_dry_run`
- `prospective_candidate_evidence=false`

The operator boundary also rejects any paper spec that attempts to self-declare prospective evidence or candidate-freeze metadata.

Therefore the Phase-12 economic requirement of both a committed/consumed historical `final_oos` candidate result and a genuinely prospective post-freeze `forward_paper` evaluation is not satisfied.

## 2. Paper execution/reconciliation evidence

Current deterministic paper-operation smoke input:

- Spec: `tests/fixtures/paper/four_asset_forward_paper.json`
- Operation ID: `forward-paper-three-asset-20260817`
- Input fingerprint: `0bdf50061654218460fde07def6230db142cba2defd6768ed62e5cd233d79d7e`
- Reconciliation: `true`
- Fill count: `3`
- Ending holdings: `BTC=0.002501263970304367`, `ETH=0.021054338498337197`, `SOL=1.056261213720316622`, `USDT=120.3297984136`
- Explicit MARKET notional-reference prices: `BTCUSDT=63643.03000000`, `ETHUSDT=1906.42000000`, `SOLUSDT=75.80000000`

The filter-reference prices are explicit paper inputs and are intentionally separate from modeled slippage-adjusted execution prices. The fixture does not claim to reconstruct Binance's historical `avgPriceMins` series.

Key review-hardening commits:

- `0a9df528b3f289c8c19481240655e39d8b606d11` — authoritative final-OOS registry binding and full immutable shadow execution preflight.
- `9569213f12c0c9dcf820d55bd05f8782d682667c` — explicit held-asset target semantics and separate MARKET notional-reference contract.
- `4e8504465a8e01a362883bfb654ffea632b69b89` — role-neutral market-storage provenance and reserved 2024 fixture repair.
- `67d24bd56c62ca384a54ce802a802914d78a8fc9` — Playwright Chromium provisioning and self-captured larger-window provenance.
- `9936387541412c1a0d05027ce6b253824ee31bed` — refreshed Phase-11 clean measured evidence.

Larger-window evidence:

- `docs/research/2026-08-17-phase11-larger-window-exercise.json`
- `docs/research/2026-08-17-phase11-larger-window-exercise.md`
- Clean measured commit: `67d24bd56c62ca384a54ce802a802914d78a8fc9`
- Self-captured code fingerprint: `f57d7465d33f9e6490edd59a9cebcfe6aff0856f83f0410195402e52f654e444`
- Self-captured dirty flag: `false`
- 365 carried-state paper operations, 1,095 market rows, 391 fills, 704 explicit no-fill outcomes, all operation artifacts reconciled.

## 3. Clean committed verification gate

A separate clean clone of committed `9936387541412c1a0d05027ce6b253824ee31bed` was used so concurrent uncommitted Phase-14 work could not influence the gate.

Backend/static commands and results:

```text
uv run pytest -q
-> 399 passed, 1 skipped

uv run ruff check .
-> clean

uv run ruff format --check .
-> 199 files already formatted

uv run pyright src tests scripts
-> 0 errors, 0 warnings, 0 informations

uv run lint-imports
-> 5 contracts kept, 0 broken

uv run python scripts/check_source_size.py
-> hard cap clean; 8 review warnings in the 500-700 line band

git diff --check
-> clean
```

Frontend/OpenAPI commands and results in the same clean clone:

```text
uv run python scripts/export_openapi.py /tmp/qap-phase12-openapi.json
cmp -s web/openapi.json /tmp/qap-phase12-openapi.json
-> byte-identical

pnpm install --frozen-lockfile
pnpm generate:api -- /tmp/qap-phase12-openapi.json
git diff --exit-code -- src/api/schema.d.ts
-> generated schema unchanged

pnpm typecheck
pnpm typecheck:e2e
-> clean

pnpm test
-> 20 files passed, 42 tests passed

pnpm build
-> production build passed
```

Browser acceptance is **not fully green** on committed `9936387`:

```text
pnpm e2e
-> Chromium provisioning ran successfully
-> pair/anchor flow passed
-> portfolio flow failed before entering Portfolio because the committed Phase-14 experiment-detail UI renamed the accessible link from "Open portfolio economics" to "Portfolio economics"
```

Source inspection also confirms the current committed Portfolio page does not expose the Phase-11.9-required Portfolio -> Pair Workbench navigation; the older E2E test jumps back to Experiment Detail before entering Pair Workbench. This UI integration is owned by the concurrently active Phase-14 workstream and is recorded here as an unresolved operational acceptance blocker rather than modified by this review stream.

## 4. Repository secret/access boundary

Tracked-source secret-pattern scan on the current repository found no matches for common private-key/API-secret patterns. Production `src/qap`/`scripts` paths also contain no authenticated Binance trading adapter, private order-placement path, margin/borrow/futures/perpetual execution code, or live scheduler.

Current paper/public-data paths therefore require no Binance secret configuration.

## 5. Current Binance Spot venue semantics checked

Authoritative sources accessed 2026-08-17:

- Binance Spot REST API: https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md
- Spot filters: https://github.com/binance/binance-spot-api-docs/blob/master/filters.md
- Spot enums/order statuses: https://github.com/binance/binance-spot-api-docs/blob/master/enums.md
- MARKET order behavior FAQ: https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_orders_faq.md

Relevant live-design facts from those sources:

- private trading requests are signed; `TRADE` permission covers placing/canceling orders and `USER_DATA` covers account/order status;
- `newClientOrderId` exists, but a live design still needs durable local intent identity/retry/recovery semantics rather than assuming one HTTP submission equals one economic action;
- order state includes `NEW`, `PARTIALLY_FILLED`, `FILLED`, `CANCELED`, `REJECTED`, `EXPIRED`, and `EXPIRED_IN_MATCH`;
- MARKET orders can partially fill and then expire, so partial fills must be first-class inventory/accounting events;
- order/query responses expose real executed quantity, cumulative quote quantity, commissions and commission asset; current paper quote-fee assumptions are not a sufficient live commission model;
- request timeout/5xx can leave execution status unknown even if the Matching Engine may have accepted the order; venue status must be queried/reconciled before dependent trading continues;
- 429 indicates rate-limit violation and repeated violations can lead to 418 bans; live design needs explicit backoff/rate-limit handling;
- `exchangeInfo`/filters include symbol-level price/lot/notional constraints, while account-specific relevant filters can require authenticated `USER_DATA` access;
- MARKET `MIN_NOTIONAL`/`NOTIONAL` uses a venue reference/average previous-trade price governed by `avgPriceMins`, not the modeled fill price. QAP paper execution now requires that filter-reference price explicitly but does not yet acquire the live venue reference itself.

## 6. Live order-lifecycle requirements not yet implemented

Any later live design must treat this sequence as authoritative:

```text
intent
 -> persist durable idempotent client identity
 -> submit signed spot order
 -> venue acknowledgement or unknown submission state
 -> zero/partial/full fill events
 -> cancel/reject/expire handling
 -> query/user-stream reconciliation from venue truth
 -> balance reconciliation
 -> restart recovery
```

Required fail-closed properties:

- retry must not silently duplicate the economic action;
- unknown order state blocks dependent orders;
- partial fills immediately become real owned inventory;
- venue balance/order truth supersedes local optimistic state;
- restart recovers outstanding intents/orders before new trading;
- fee asset and actual commission are reconciled from venue data;
- account-specific filters/permissions are checked, not inferred from public market metadata;
- rate-limit/backoff state is operationally enforced.

No current QAP module implements this authenticated lifecycle, which is intentional before a GO decision.

## 7. Action-space and capital-control evidence

Current QAP design and production code remain spot-only and contain no margin, borrowing, leverage, futures, perpetual, option or CFD execution path. Execution-only bridge ownership is explicit and residual bridge inventory remains in the real portfolio state.

A later live design would still need user-approved values for:

- maximum total automated portfolio notional;
- maximum notional per rebalance/event;
- stale-data timeout;
- maximum price deviation/slippage;
- any daily/period anomaly or loss stop compatible with the inventory objective;
- kill-switch semantics;
- explicitly admitted execution-only bridge assets.

These values are not safe to invent autonomously and remain blockers to live implementation.

## 8. Provisional India legal/operational source check

The repository does not establish the user's legal residence, tax residence, account entity, or venue account jurisdiction. For this gate, India was checked as a provisional context only; actual jurisdiction must be confirmed by the user before any live design.

Authoritative sources accessed 2026-08-17:

- FIU-IND downloads/guidance: https://fiuindia.gov.in/files/downloads/downloads.html
- FIU-IND compliance orders: https://fiuindia.gov.in/files/Compliance_Orders/orders.html
- Income Tax Section 115BBH: https://www.incometaxindia.gov.in/w/section-115bbh-5
- Income Tax Schedule VDA: https://www.incometaxindia.gov.in/w/schedule_vda
- Income Tax VDA TDS guidance: https://www.incometaxindia.gov.in/w/tds-on-payment-for-the-transfer-of-virtual-digital-assets-vdas-

Relevant observations:

- FIU-IND publishes AML/CFT guidance for VDA service providers updated 8 January 2026 and a third revised VDA-service-provider registration circular dated 15 September 2025.
- FIU-IND's compliance-order page records a Binance order dated 19 June 2024. This review did not locate an authoritative current FIU registry page that is sufficient by itself to prove the exact Binance service/entity/account available to this user is presently eligible for the proposed live workflow.
- Current official Income Tax material requires transaction-wise Schedule VDA reporting, maintains special taxation of VDA transfer income, and retains VDA TDS mechanics. Exact applicability, deduction responsibility, account/entity treatment and any 2026 transition rules require user-specific tax/legal confirmation.

These observations are operational blockers/questions, not legal or tax advice.

## 9. Current blocker summary

Automatic/primary blockers:

1. zero Phase-10 development survivors;
2. no eligible candidate has consumed the reserved final-OOS window;
3. no genuinely prospective post-freeze candidate evaluation exists.

Additional live-design blockers:

4. no authenticated order lifecycle or unknown-state/restart recovery design;
5. no live commission/fee-asset and account-filter reconciliation contract;
6. user capital/risk limits are unset;
7. actual legal/tax/account jurisdiction and venue eligibility are not confirmed;
8. Phase-11.9 Portfolio -> Pair Workbench browser acceptance remains incomplete in the current committed UI stream.

These blockers are sufficient for `NO-GO`. No private API key or live-order implementation is warranted by the current evidence.
