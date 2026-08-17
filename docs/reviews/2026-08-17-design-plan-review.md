# QAP Design and Plan Engineering Review

**Date:** 2026-08-17

**Review target:** clean QAP design plus master/phase implementation plans

**Verdict:** **Ready for user review; not implementation-authorized**

## 1. Scope/process challenge

The package is intentionally documentation-only. The clean repository contains no runtime scaffold, source package, web application, tests, dependency files, exchange integration, or live-capital code yet.

The implementation plan is decomposed into bounded phases rather than one giant build. The sequence proves financial/accounting truth before statistical sophistication and proves paper semantics before any live-design consideration.

Deferred by design:

- live/private exchange execution;
- database/service decomposition;
- multi-exchange support;
- topology/network visualization;
- generalized plugin/model registries;
- optimizer frameworks;
- automated hyperparameter search;
- public deployment/auth;
- autonomous development tooling until the manual workflow is proven.

## 2. Architecture/data flow review

The reviewed dependency direction is:

```text
market observations
 -> relationship evidence
 -> policy
 -> target allocation / rebalance plan
 -> deterministic spot execution
 -> portfolio ledger/state
 -> evaluation / matched HODL / simple controls
 -> experiment artifacts
 -> thin API
 -> web inspection
```

Ownership is intentionally asymmetric:

- portfolio owns actual holdings;
- execution owns fill semantics, not a second wallet;
- policy owns target intent, not balances;
- relationship models own evidence, not allocation authority;
- evaluation derives economics, not mutations;
- API/web render authoritative results, not financial truth.

This direction is consistent across the design and phase plans.

## 3. Material findings found and corrected during review

### [high] Primary-objective contradiction

Some early design text still inherited an older inventory-primary framing after the user had selected portfolio wealth as primary.

**Resolution:** normalized the entire design to:

- primary objective: portfolio wealth growth relative to matched passive HODL after realistic costs;
- inventory: the actual economic state/object QAP reallocates;
- coin-unit accumulation: secondary outcome and attribution, never allowed to redefine wealth destruction as success.

### [high] Historical bar timing ambiguity

"completed bar t -> next bar open" was not explicit enough about candle-open timestamp semantics.

**Resolution:** every bar now has `close_time = open_time + interval`; decisions may consume exactly bars with `close_time <= decision_time`; the contiguous next bar open may be used as the execution reference without consuming any later value from that bar.

### [high] Dirty-code experiment identity collision

Using Git commit + dirty flag was insufficient because multiple distinct dirty source trees could share the same commit and flag.

**Resolution:** run identity now includes a deterministic code fingerprint over authoritative local source/config bytes. Commit/dirty status remains supplemental provenance.

### [high] Multi-asset routing ambiguity

An earlier plan did not define how independent overweight/underweight deltas map to executable conversions without a general matching optimizer.

**Resolution:** Phase 11 uses one explicitly declared transient settlement/bridge asset as the deterministic execution hub for multi-asset paper rebalances. It is execution infrastructure, not automatically analysis anchor or economic target.

### [high] Bridge residue accounting

Execution-only bridge dust could have been accidentally omitted from target-basket evaluation.

**Resolution:** any residual bridge balance remains real `PortfolioState` inventory and must be included in terminal valuation/accounting even when the bridge is outside the target allocation.

### [medium] Rebalance-notional double counting

Summing absolute target-current value deltas counts the same fully invested value once as a sell and once as a buy.

**Resolution:** the minimum-notional guard uses one-way rebalance notional: `0.5 * sum(abs(target_value_i - current_value_i))`.

### [medium] API contract inconsistency

The design listed `POST /api/experiments` while Phase 08 intentionally defined a read-oriented first API.

**Resolution:** removed the mutation endpoint. Experiments remain command/runner-driven until a real asynchronous/operator HTTP workflow earns a design.

### [medium] Student-t historical bias

The plan originally implied Student-t Copula would definitely be reimplemented because it was historically important.

**Resolution:** Phase 10 now contains an admission gate. Student-t can end as `REJECT` without code if no current falsifiable question survives the historical/v2 evidence review.

### [medium] Source/document God-object risk

The main design document exceeded the user's new maintainability rule.

**Resolution:** split design into two focused companion specs. No current hand-written repository file exceeds 500 lines. Future source/test files warn for decomposition at 500 lines and hard-fail beyond 700 unless narrowly generated/exempt.

### [medium] Current runtime choice

The initial plan used the previous Python feature line even though Python 3.14 is now the current stable feature line and the required scientific packages publish CPython 3.14 wheels.

**Resolution:** baseline moved to Python 3.14 with `<3.15` until the next stable feature line is deliberately adopted.

## 4. Contract decisions now settled

- Matched-HODL-relative wealth is the primary scalar success metric.
- Coin accumulation is secondary per-asset attribution.
- Pair `X/Y` means Y units per one X unit.
- `X/Y` and `Y/X` are orientations of one canonical relationship.
- BTC/another asset may be an analysis anchor but has no constitutional trading authority.
- Policy produces target allocation; execution produces fills; portfolio owns balances.
- Default bar timing is completed-bar evidence -> contiguous next-bar-open paper execution.
- Actual spot ownership only; no leverage, borrowing, derivatives, shorting unowned inventory, or interest-based financing.
- v1/v2 are read-only evidence/reference repositories and never runtime dependencies.
- Web/API layers do not own financial truth.
- No live-capital authority exists before a separate readiness review and later live-execution design.

## 5. Verification strategy review

The plan uses focused tests around real failure modes rather than coverage ceremony:

| Risk | Planned evidence |
|---|---|
| phantom/negative inventory | hand-calculated wallet/ledger scenarios |
| duplicate cost/fill application | idempotent fill + explicit cost scenario |
| lookahead | point-in-time history and last-bar/no-next-fill tests |
| orientation error | reciprocal/log-sign pair tests |
| anchor math error | direct vs anchor-decomposition identity tests |
| benchmark mismatch | same-start HODL invariant |
| run unreproducibility | manifest/data/code fingerprints + repeated isolated runs |
| API drift | focused OpenAPI/contract tests |
| frontend financial duplication | API-owned DTOs + component tests around presentation only |
| multi-leg loss of value | hand-calculated bridge route + independent reconciliation |
| autonomous scope drift | plan parser, Git guard, verification and escalation tests |

Property-based testing is deliberately deferred until focused examples expose an invariant where generated-domain coverage is materially stronger than examples.

## 6. Isolation/worktree verdict

No worktree is justified for the current documentation-only clean repository. It is a new repository with no unrelated local changes. Future implementation should continue in the current checkout unless concurrent workers, conflicting dirt, material risk, or explicit repository policy provides a real isolation reason.

## 7. Current-stack verification

The stack decision was refreshed against current official/project sources before review completion:

- Python 3.14 stable line;
- React 19.2 latest patched line;
- Vite 8.1 line;
- TanStack Router Vite plugin for file-based typed routes;
- TradingView Lightweight Charts 5.2 line.

Exact package patch versions are intentionally resolved and reverified at phase execution time rather than frozen in prose today.

## 8. Remaining intentional uncertainties

These are not missing plan details; they are hypotheses or later operator decisions:

- which exact real asset basket should be admitted;
- whether BTC should be the preferred analysis anchor for a given experiment;
- realistic fee/slippage values for each venue/account context;
- whether Student-t Copula deserves reimplementation after the Phase-10 admission review;
- which relationship model, if any, adds incremental OOS wealth over simple cost-aware rebalancing;
- whether a bridge asset is needed for the chosen basket/venue;
- eventual live capital/risk limits;
- whether QAP ever earns live execution authority.

## 9. Readiness conclusion

The design/planning package is coherent enough for user review. The next correct action is **not implementation**; it is user review of the two companion design specs, historical-reference boundary, master plan, and phase plans. Requested changes should be applied to the documentation before Phase 00 begins.
