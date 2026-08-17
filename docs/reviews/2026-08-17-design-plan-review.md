# QAP Design and Plan Engineering Review

**Date:** 2026-08-17

**Review target:** clean QAP design plus master/phase implementation plans

**Verdict:** **Ready after independent-review changes; one final targeted research check may refine Phase 10 but is not a prerequisite to begin Phase 00 unless it reveals a critical contradiction**

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

"completed bar t -> next bar open" was not explicit enough about source timestamp semantics or the distinction between an observable reference price and a guaranteed executable fill.

**Resolution:** internally each bar now has `bar_end_exclusive = open_time + interval` while source-native close timestamps are preserved separately. Decisions may consume only bars whose internal completion boundary is no later than the decision time. The contiguous next-bar open is a causal **execution reference**; modeled execution price is derived from declared slippage/fee/quantization and is never described as a guaranteed market fill.

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

### [high] Potential portfolio/evaluation dependency cycle

The oracle integration added an executable dependency-direction guard, which exposed a plan-level cycle: Phase 05 originally placed rebalance planning in `qap.portfolio` while consuming an evaluation-owned valuation snapshot. That could force portfolio -> evaluation while evaluation already depends on portfolio.

**Resolution:** observed mark prices now live in a small Phase-02 `qap.market.PriceSnapshot`; pure rebalance planning moved to `qap.policy.rebalance`; `qap.portfolio` stays the inner holdings/allocation owner; independent fill/result reconciliation moved to `qap.experiment`, which is explicitly allowed to orchestrate execution and evaluation. Phase 00 now plans a standard-library import-boundary checker to prevent this dependency direction from regressing.

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
- Default bar timing is completed-bar evidence -> contiguous next-bar-open execution reference -> explicit modeled fill.
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

## 8. Independent oracle review integration

An external oracle review returned **READY WITH CHANGES**, explicitly finding no architectural-redesign requirement and concentrating its objections on research validity, historical-universe semantics, execution realism, and model-orientation semantics.

The review was treated as external feedback rather than authority. Each material item was checked against the actual plans and, where the claim depended on external facts, against primary literature/current official documentation.

### Disposition matrix

| Oracle finding | Disposition | Plan/design action |
|---|---|---|
| Point-in-time universe/survivorship semantics | **ACCEPT** | Added `declared_fixed_basket` vs `point_in_time_investable`; fixed-basket backtests cannot claim historical discoverability. Added stable `AssetId` vs venue-symbol mapping. |
| Minimum research-integrity rules appear too late | **PARTIAL ACCEPT** | Moved only durable rules into Phase 00/02 (`final_oos` consumption, fixed-vs-point-in-time claims, escalation boundaries). Full manifest/runner/tooling remains Phase 07 to avoid recreating v2. |
| First real public Spot data should appear before Phase 10 | **ACCEPT** | Moved one bounded unauthenticated Binance Spot public-data adapter to Phase 02. Phase 11 now reuses/hardens it rather than creating a second path. |
| Reciprocal pair identity does not imply reciprocal fitted-model behavior | **ACCEPT** | Added `OrientationBehavior = exact_transform | directional_transform | refit_required`; every fitted model declares it. |
| Next-bar open is causal but not guaranteed execution | **ACCEPT** | Renamed it execution reference and made modeled price/slippage/fee/quantization explicit. |
| Pair x model x horizon search needs family/trial accounting | **ACCEPT** | Added `research_family_id`, parent lineage, retained failed siblings, frozen family before final OOS, and final-holdout commitment/consumption. |
| Formal multiple-testing protection | **PARTIAL ACCEPT** | No permanent SPA/Reality-Check/PBO framework. Family-level multiplicity analysis is required only when an actual broad search supports a formal superiority claim. |
| Common crypto factors can masquerade as pair alpha | **ACCEPT WITH YAGNI BOUNDARY** | Phase 10 now includes one simple cross-sectional/common-mode control. Rich market/size/momentum attribution becomes required before calling a surviving return pair-specific alpha, but its data/tooling is admitted only if a candidate survives simpler controls. |
| Decimal/quantized ledger semantics | **ALREADY COVERED; STRENGTHENED** | `Decimal` was already authoritative for quantities/fees/accounting; source vs execution prices and later venue quantization are now even more explicit. |
| UI can leak final OOS | **ACCEPT** | API/web read persisted run artifacts only; no arbitrary raw-holdout browser. Final-OOS commitment/consumption and research-family context are visible. |
| Bridge/fee assets need explicit admission | **ALREADY COVERED; STRENGTHENED** | Bridge residue was already inventory. The constitution now explicitly applies the same admission/accounting rule to third-party fee assets. |
| Terminal wealth alone hides risk/path differences | **ACCEPT** | Phase 03 now includes relative-wealth path and drawdown diagnostics; web Portfolio prioritizes them with turnover/cost/concentration. |
| 500/700 line rule can cause artificial splitting | **ACCEPT AS EXISTING INTENT** | Numeric thresholds remain tripwires; one-reason-to-change, dependency direction, and God-object review remain stronger. Phase 00 now plans a lightweight import-boundary checker. |

### External claim verification

Primary-source checks performed during integration:

- Halbert White, *A Reality Check for Data Snooping*, Econometrica 68(5), 2000, DOI `10.1111/1468-0262.00152`: repeated use of one dataset for model/specification selection can produce chance winners and motivates benchmark-aware family-level inference.
- Peter R. Hansen, *A Test for Superior Predictive Ability*, Journal of Business & Economic Statistics 23(4), 2005, DOI `10.1198/073500105000000063`: supplies a many-alternative benchmark-comparison tool that improves on limitations of the original Reality Check.
- Liu, Tsyvinski & Wu, *Common Risk Factors in Cryptocurrency*, Journal of Finance 77(2), 2022, DOI `10.1111/jofi.13119`: market, size, and momentum factors account for substantial cross-sectional crypto-return structure, supporting common-factor attribution before declaring pair-specific alpha.
- Current official Binance Spot API documentation: public market-data requests are available through a market-data-only endpoint without signed/private trading authority; Spot symbol filters explicitly expose price ticks, quantity steps, and minimum/notional constraints. This supports moving a bounded read-only data adapter earlier while keeping precision/execution hardening separate.

### Review-loop stopping rule

This integration is the **last broad pre-build architecture/research review gate**. A further research pass may refine unresolved Phase-10 statistical choices, but Phase 00 is no longer blocked by requests for another general review. Reopen the architecture before building only if new evidence shows a critical contradiction in the primary objective, long-only action space, benchmark/control logic, accounting ownership, causal timing, or reproducibility model.

## 9. Remaining intentional uncertainties

These are not missing plan details; they are hypotheses or later operator decisions:

- which exact real asset basket should be admitted;
- whether BTC should be the preferred analysis anchor for a given experiment;
- realistic fee/slippage values for each venue/account context;
- whether Student-t Copula deserves reimplementation after the Phase-10 admission review;
- which relationship model, if any, adds incremental OOS wealth over simple cost-aware rebalancing;
- whether a bridge asset is needed for the chosen basket/venue;
- eventual live capital/risk limits;
- whether QAP ever earns live execution authority.

## 10. Readiness conclusion

The independent review was strong and materially improved the scientific contract, but it did not reveal a reason to redesign the architecture. The design/planning package is now **ready to begin Phase 00 after the user's current review/research handoff**.

One narrow research question remains useful before Phase 10 is eventually executed: what is the minimum statistically defensible protocol for separating pair-specific incremental value from simple rebalancing/common-mode effects under many pair/model/horizon trials? That answer may refine Phase 07/10, but it should not delay repository foundation, domain, data, accounting, or deterministic replay work unless it uncovers a critical contradiction.

## Final Targeted Quantitative Review Reconciliation

**External verdict:** `GO`; no critical Phase-00 blocker.
**Internal reconciliation:** accepted with bounded clarifications; architecture remains frozen for build.

| Finding | Decision | QAP correction |
|---|---|---|
| Benchmark ladder is counterfactual, not unique additive causal decomposition | ACCEPT | Phase 07 now limits claims to incremental value relative to declared controls. |
| Terminal wealth ratio alone is insufficient for statistical uncertainty | ACCEPT | Phase 03 emits aligned incremental net log-relative performance series while retaining terminal wealth as the economic headline. |
| Common-mode control should be executable/pair-blind | ACCEPT | Phase 10 requires a real pair-blind allocation policy through identical mechanics/costs. |
| Two-asset internal common-mode control is degenerate | ACCEPT | Two-asset studies cannot claim common-mode-independent pair alpha without an external proxy/additional assets. |
| Reciprocal semantics need joint-fit vs directional-evidence distinction | ACCEPT AND STRENGTHEN | Phase 04 separates `fit_reciprocity` from `evidence_reciprocity`; refit orientation selection stays inside one correlated research family. |
| Formal multiplicity methods should be claim-triggered | ACCEPT | SPA preferred for searched-family superiority on reused evaluation data; PBO/DSR only for the questions they actually answer. |
| Student-t remains early candidate; Gaussian required only for a tail-specific claim | ACCEPT | Phase 10 first Copula experiment remains deliberately narrow. |

### Independent verification

The log-relative reconciliation is exact for strictly positive aligned wealth paths. The two-asset common-mode warning is exact: with `m=(r_X+r_Y)/2`, `r_X-m=(r_X-r_Y)/2` and `r_Y-m=-(r_X-r_Y)/2`.

Primary literature independently supports the governance corrections: White's Reality Check addresses best-model claims after specification search; Hansen's SPA improves robustness/power when poor alternatives contaminate the family; Phillips-Ouliaris developed residual-based cointegration tests including a normalization-invariant variant, supporting caution around conventional normalized residual fits; Demarta-McNeil establishes the t-Copula as a serious tail-dependence model while also motivating richer variants. The maintained `arch` library already implements block-bootstrap SPA/RealityCheck/StepM, so QAP should not recreate these procedures.

### Review-loop stop rule

This closes the broad pre-build research review loop. New evidence does not reopen architecture unless it exposes a critical contradiction in primary objective, long-only Spot action space, accounting ownership, causal timing, benchmark logic, or reproducibility. Remaining questions are Phase-07/10 admission questions and must not delay Phase 00.

### OSS consequence

The parallel OSS audit does not change architecture; it changes implementation tactics. Use maintained commodity libraries where they save code, but retain QAP-owned economic truth. See `docs/OSS_REUSE_BOUNDARY.md`.
