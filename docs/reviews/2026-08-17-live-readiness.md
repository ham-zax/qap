# QAP Phase-12 Live-Readiness Review

**Review date:** 2026-08-17

**Decision: `NO-GO`**

QAP has **not** earned the right to begin a live-execution design. The paper/research system is materially stronger and its current accounting/execution boundaries are verified, but the Phase-12 economic evidence gate fails before any live-capital question is reached: the predeclared real-data Phase-10 family produced zero development survivors, therefore no candidate consumed the reserved final-OOS window, and no genuinely prospective post-freeze candidate evaluation exists.

`NO-GO` means continue paper/research work with the blockers below. It does **not** authorize a live-execution design, private API credentials, authenticated exchange code, order placement/cancel code, a live scheduler, or automated capital deployment.

Detailed IDs, fingerprints, commands and current-source references are recorded in `docs/reviews/2026-08-17-live-readiness-evidence.md`.

## Candidate/run evidence

The designated real-data simple-first family is:

- research family: `phase10-btcusdt-daily-momentum-2023-v1`;
- development window: BTCUSDT daily 2023, 365 bars;
- development semantic fingerprint: `0cff5a7068c2d3e7957b481f826ce8ca80956191873671035a08353cfdb4d5fc`;
- predeclared attempts: `9`;
- development survivors: `0`.

All six core family members are negative versus strict inventory HODL after the declared costs. Some beat the periodic-30 simple control, including under symmetric adverse costs, but that cannot satisfy the declared survivor rule when HODL-relative wealth is negative.

The reserved BTCUSDT daily 2024 dataset remains unconsumed:

- 366 bars;
- semantic fingerprint `b3069c70fb61f1e7fb6a8b1d338194817ba8896dfd2618b96091c8c46686f2a5`;
- candidate final-OOS commitment count `0`.

Its Phase-02 Parquet container is now research-role-neutral; final-OOS meaning belongs to the experiment manifest/commitment protocol rather than market-data storage metadata.

There is also no genuinely prospective candidate paper period. Current paper-operation artifacts are deliberately classified as `operational_dry_run` with `prospective_candidate_evidence=false`, and the operator input cannot self-declare a prospective/candidate-freeze role.

### Economic gate conclusion

Phase 12 requires at least one justified candidate with both:

1. a committed/consumed historical `final_oos` result; and
2. a genuinely prospective post-freeze `forward_paper` evaluation.

Neither exists, because the preceding development family produced no survivor. Consuming the reserved 2024 holdout or relabeling an operational dry run now would spend/reclassify evidence without a candidate justified for promotion.

**Economic gate: FAIL / automatic `NO-GO`.**

## Economic result versus HODL and primary control

The development evidence does not support live-design exploration:

- every core momentum member is negative versus strict HODL;
- several members are positive versus the periodic-30 primary control, but this is secondary to the declared HODL wealth objective;
- no nearby-parameter or one-bar-delay diagnostic establishes a robust HODL-beating region;
- high fill counts and modeled costs remain economically material.

This is a valid negative research result, not a protocol failure. The correct action is to leave final OOS untouched and require a new independently motivated, predeclared research generation before any candidate promotion can occur.

## Reconciliation and deterministic paper result

The current deterministic four-asset paper smoke remains internally reconciled:

- operation ID: `forward-paper-three-asset-20260817`;
- input fingerprint: `0bdf50061654218460fde07def6230db142cba2defd6768ed62e5cd233d79d7e`;
- independent reconciliation: `true`;
- fill count: `3`;
- evidence class: `operational_dry_run`;
- prospective candidate evidence: `false`.

The review-hardening batch also closes the material execution/research integrity findings that were raised before this gate:

- final-OOS execution permits are bound to the authoritative atomic holdout registry entry rather than caller-selected JSON;
- multi-asset execution performs a complete immutable shadow pass so route/precision/cost/no-fill outcomes are known before the accepted execution pass;
- held non-bridge assets must be explicit members of the economic target, with explicit zero meaning liquidation;
- Binance-style MARKET notional validation receives an explicit venue filter-reference price separate from modeled slippage-adjusted execution price;
- the reserved market-data artifact no longer falsely labels itself `development` at the storage layer;
- Phase-11 larger-window evidence captures its own commit, dirty state and code fingerprint;
- Playwright Chromium provisioning is part of the documented E2E command.

A clean clone of committed `9936387541412c1a0d05027ce6b253824ee31bed` passed the backend/static completion gate with `399 passed, 1 skipped`, Ruff/format clean, strict Pyright clean, five import contracts kept, and no source-size hard-cap failure. OpenAPI regeneration was byte-identical, generated TypeScript did not drift, frontend typechecks passed, `42/42` Vitest tests passed, and the production build passed.

The browser acceptance gate is not fully green on that committed UI state: the pair/anchor flow passes, but the portfolio flow is stale against the evolving Phase-14 UI and the current Portfolio page still does not provide the Phase-11.9 Portfolio -> Pair Workbench navigation. That UI integration is a separate unresolved operational blocker; it does not alter the already-failed economic gate.

**Determinism/accounting gate: paper core PASS; browser operational acceptance INCOMPLETE.**

## Current venue semantic mapping

Current official Binance Spot documentation was checked rather than inferring live behavior from the public market-data adapter.

The later live design would need to map at least these real venue semantics:

| Paper assumption / need | Current live semantic | Readiness state |
|---|---|---|
| explicit spot instrument and filters | symbol/filter metadata including price, lot, MARKET lot and notional filters | paper normalization exists; authenticated/account-specific filters still need live design |
| deterministic MARKET notional admission | venue reference/average price semantics governed by `avgPriceMins` | paper contract now separates filter-reference price; live acquisition/reconciliation is not designed |
| one intended economic action | signed order submit plus durable client identity | no authenticated intent/idempotency layer exists |
| immediate modeled fill | venue may acknowledge, partially fill, fully fill, reject, cancel or expire | no live state machine exists |
| HTTP response determines truth | some timeouts/5xx can leave execution status unknown | no unknown-state recovery/query barrier exists |
| quote-denominated modeled fee | venue reports actual commissions and commission asset | no live commission/fee-asset reconciliation exists |
| local balances after fill | venue account/order state is authoritative | no restart reconciliation/recovery design exists |
| bounded request flow | venue rate limits, 429 handling and potential bans | no live backoff/rate-limit controller exists |

Every live paper assumption therefore either has a known venue analogue or an explicit design gap; none of these gaps is silently treated as solved.

**Venue semantic review: MAPPED ENOUGH FOR A NO-GO REPORT; NOT IMPLEMENTATION-READY.**

## Required future live order lifecycle

Any future live design would need an explicit fail-closed lifecycle:

```text
intent
 -> persist idempotent client identity
 -> submit signed spot order
 -> venue acknowledgement OR unknown submission state
 -> zero/partial/full fill events
 -> cancel/reject/expire handling
 -> query/user-stream reconciliation from venue truth
 -> balance reconciliation
 -> restart recovery
```

Required properties include:

- a retry cannot silently duplicate the intended economic action;
- partial fills immediately become real owned inventory;
- an unknown order state blocks dependent trading until reconciled;
- local optimistic balances are never authoritative before venue confirmation;
- restart recovery reconciles outstanding intents/orders before new trading;
- actual commission amount/asset is folded into balances/accounting;
- account-specific filters and permissions are checked rather than inferred from public metadata;
- rate-limit/backoff state is operationally enforced.

These are design requirements only. No Phase-12 live implementation is created.

## Capital and failure controls

The current architecture keeps route length at one or two real spot legs and fails closed on missing/ambiguous paper inputs. A future live design would additionally require explicit user-approved values/mechanics for:

- maximum total portfolio notional exposed to automation;
- maximum notional per rebalance/event;
- stale-data timeout;
- maximum tolerated price deviation/slippage;
- any daily/period anomaly or loss stop consistent with the inventory objective;
- kill-switch behavior independent of a healthy strategy loop;
- explicit admission of any execution-only bridge asset.

These are user risk decisions. Phase 12 does not guess them, and their absence independently blocks live implementation.

## Secret and access boundary

The current tracked repository secret-pattern scan found no common API-secret/private-key patterns. The existing public market-data/paper stack requires no Binance trading credential, and production code contains no authenticated order-placement path.

A future live design would still need to require:

- minimum necessary API permissions;
- withdrawal permission disabled where venue permission separation allows it;
- secrets outside Git, run artifacts, logs and agent prompts;
- test/sandbox and production credentials separated where supported;
- authentication material redacted from logs/errors.

**Secret boundary today: clean paper/public-data boundary. Live secret design: NOT YET PRESENT.**

## Action-space confirmation

QAP's implemented action space remains actual spot ownership/conversion only. The current production paths contain no margin, auto-borrow, leverage, futures, perpetual, option or CFD execution mechanism. Execution-only bridge ownership is explicit, and bridge residue remains real portfolio inventory.

Asset-level religious/suitability admission remains an operator/scholarly decision outside the engine's mechanical guarantees.

A future live design must preserve these account/order settings mechanically. Any venue requirement that forced borrowing, margin or derivative exposure would be an automatic `NO-GO` under the declared QAP boundary.

**Mechanical action-space today: PASS for paper architecture. Live account configuration: UNVERIFIED.**

## Current jurisdiction/venue blockers

The repository does not establish the user's legal residence, tax residence, account entity or exact venue-account jurisdiction. India was checked provisionally because it is a plausible operational context, but this report does not assume it is the user's legally controlling jurisdiction.

Current official Indian sources show active AML/CFT guidance and registration/compliance processes for VDA service providers, and current Income Tax material retains transaction-level VDA reporting and special VDA tax/TDS mechanics. The review also located an FIU-IND Binance compliance order dated 19 June 2024, but did **not** find an authoritative current source sufficient to prove that the exact Binance service/entity/account available to this user is presently eligible for the proposed workflow.

Before any future live design, the user must confirm the actual account/jurisdiction context and obtain appropriate legal/tax guidance for venue eligibility, transaction reporting, tax/TDS responsibility and any entity/account-specific requirements. QAP's internal controls are not legal or tax advice.

**Jurisdiction/venue eligibility: UNRESOLVED / blocker.**

## Required user decisions before any future live implementation

These decisions are deliberately left unset:

1. actual legal/tax residence and the Binance entity/service/account intended for use;
2. maximum automated portfolio notional;
3. maximum notional per rebalance/event;
4. stale-data timeout;
5. maximum tolerated price deviation/slippage;
6. anomaly/loss-stop policy, if any;
7. kill-switch operational ownership;
8. explicitly admitted execution-only bridge assets;
9. future API-key permission model and credential storage/operator procedure.

Even if these were answered today, the economic final-OOS/prospective-evidence blockers would remain.

## Decision matrix

| Gate | Result | Blocking? |
|---|---|---|
| Development candidate survives HODL + primary-control rule | **FAIL — 0 survivors** | **yes** |
| Historical candidate `final_oos` consumed | **FAIL — none eligible/consumed** | **yes** |
| Genuine post-freeze prospective candidate evidence | **FAIL — none** | **yes** |
| Paper accounting/reconciliation | pass on designated smoke and larger-window exercise | no |
| Final-OOS reservation authority | repaired and focused regression verified | no |
| Multi-asset precision/route preflight | repaired and focused regression verified | no |
| MARKET filter-reference semantics | explicit in paper contract; live source acquisition not designed | yes for live implementation |
| Current venue order lifecycle mapped | requirements identified, implementation absent | yes for live implementation |
| Secrets absent from current paper repo | pass on tracked scan | no |
| User capital/risk limits | unset | yes for live implementation |
| Spot-only mechanical boundary | pass in current production code | no |
| Current legal/account/venue eligibility | unresolved | yes |
| Critical browser operational flow | incomplete in evolving UI | yes for Phase-11 operational acceptance |

## Recommendation

**Remain in paper/research mode. Do not begin a live-execution design and do not introduce private exchange credentials.**

The next economically legitimate path is a new independently motivated research generation with its own predeclared family. Only if a candidate survives the development gate should QAP consume a reserved final-OOS window. Only a surviving, consumed historical candidate may then begin a genuinely prospective post-freeze paper period. If that full evidence chain later passes, Phase 12 should be rerun with fresh venue/jurisdiction sources and explicit user risk decisions.

A future `GO TO LIVE-DESIGN` would authorize only a separate design/specification cycle. It would still not itself authorize live orders or capital deployment.
