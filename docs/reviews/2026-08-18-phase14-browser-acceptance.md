# Phase 14 Browser Acceptance — 2026-08-18

**Verdict:** GREEN after two serious rendered regressions were found and fixed during this acceptance pass.

**Scope:** Current React/Vite analytical workbench, inspected with the installed `agent-browser` CLI against the local read-only QAP API. This review covers the rendered contract in `docs/plans/14/acceptance-and-regression.md`; it does not authorize live trading or scanner execution.

## Test fixture and environment

The browser exercised immutable local evidence generated from repository fixtures:

- development run: `run-e8a00240d5c5ff869ec54457`;
- consumed final-OOS boundary fixture: `run-13976c2e06e3e32dbfa0c9b8`;
- reconciled full-fill paper operation: `forward-paper-three-asset-20260817`;
- reconciled no-fill paper operation: `forward-paper-precision-no-fill-20260817`;
- one QA-only deliberately invalid run-directory copy to exercise the corrupt-artifact list state.

The final browser runtime sweep used the current workbench with Vite at `http://127.0.0.1:54902` and the read-only API behind Vite's `/api` proxy. Browser sessions were isolated by name. Temporary screenshots and axe/network evidence were captured under `/tmp/qap-phase14-browser-acceptance/`; they are verification evidence, not screenshot-test baselines.

## Rendered matrix

The following states were exercised at both desktop `1440x1000` and mobile `390x844` where applicable:

| State | Desktop | Mobile | Axe | Page errors | Document overflow |
|---|---|---|---|---|---|
| Research Runs | pass | pass | 0 violations / 0 incomplete | 0 | none |
| Experiment Detail — negative development | pass | pass | 0 / 0 | 0 | none |
| Experiment Detail — consumed final OOS | pass | pass | 0 / 0 | 0 | none |
| Research Runs — invalid artifact visible beside valid runs | pass | pass | 0 / 0 | 0 | none |
| Portfolio Economics | pass | pass | 0 / 0 | 0 | none |
| Pair — ratio | pass | pass | 0 / 0 | 0 | none |
| Pair — log ratio | pass | pass | 0 / 0 | 0 | none |
| Pair — normalized paths | pass | pass | 0 / 0 | 0 | none |
| Pair — anchor lens | pass | pass | 0 / 0 | 0 | none |
| Pair — reciprocal orientation | pass | pass | 0 / 0 | 0 | none |
| Paper Operations index | pass | pass | 0 / 0 | 0 | none |
| Paper Operation — reconciled full fill | pass | pass | 0 / 0 | 0 | none |
| Paper Operation — reconciled no-fill | pass | pass | 0 / 0 | 0 | none |
| Not-found shell | pass | pass | 0 / 0 | 0 | none |

At mobile width every checked route satisfied:

```text
document.documentElement.scrollWidth === window.innerWidth === 390
```

A separate `720px` viewport pass was used as a 200%-equivalent desktop reflow check. Research Runs, Experiment Detail, Portfolio, Pair Anchor, Paper index/detail, and not-found shell all satisfied:

```text
document.documentElement.scrollWidth === window.innerWidth === 720
```

with zero page errors.

## Economic and research-boundary presentation

The negative development run renders the authoritative result as negative evidence rather than success-colored arithmetic:

- `Negative evidence`;
- `Underperformed Periodic-2 by 1.79%`;
- `vs strict inventory HODL −1.79%`;
- the predeclared success threshold remains visible;
- Portfolio and Pair evidence links are visible without exposing raw hashes as primary content.

The consumed final-OOS state renders `Final OOS · consumed` and explicitly states that the inspected window has been consumed and must not later be treated as a fresh holdout.

The deliberately invalid run remains visible as `Invalid artifact` with `Run artifacts are invalid.`; it does not hide valid runs or acquire a success presentation.

Paper states retain explicit non-candidate boundaries. The no-fill fixture renders `Reconciled with 2 fills; 1 leg did not fill` and `No fill · SOL · Below Minimum Notional` while remaining `Forward paper · operational dry run` and ineligible for parameter selection/model promotion/deployment evidence.

## Chart and pair behavior

Portfolio renders relative wealth as primary time-series evidence, followed by benchmark comparison, composition, allocation history, HODL attribution, execution context, flows, and one selected rebalance decision at a time.

Pair behavior was exercised through all four chart modes and reciprocal orientation:

- ratio -> `view=ratio`;
- log ratio -> `view=log`;
- normalized paths -> `view=normalized`;
- anchor lens -> `view=anchor`;
- reciprocal action -> canonical path remains `/BTC/USDT` while URL-owned `orientation=USDT/BTC` changes the displayed orientation to `USDT / BTC`.

Rendered chart copy states units/orientation and gives a textual latest-value summary. TradingView attribution remains visible. Anchor decomposition reports zero identity error in the deterministic fixture.

## Keyboard and focus

Keyboard checks passed:

- first `Tab` on Research Runs focuses the `Skip to content` link;
- the skip link has a visible `3px solid` focus outline and Enter navigates to `#main-content`;
- Pair reciprocal orientation can be focused and activated with Enter, has the same visible focus treatment, and updates URL-owned orientation;
- Portfolio Decision 2 can be focused and activated with Enter, updates the `decision=` URL search state, and changes the panel to `Rebalance 2 of 12`.

Wide audit regions are internally scrollable and keyboard reachable. At `390px`, the no-fill paper detail exposes focusable `overflow-x: auto` regions for execution routes, realized fills, holdings, venue precision, reference prices, and MARKET notional-filter reference prices. Their scroll widths exceed their contained client widths without expanding the document.

## Disclosure and provenance defaults

Audit/provenance content remains available but closed by default:

- Experiment Detail: exact-value disclosures and `Technical provenance` are closed;
- Portfolio: exact values, benchmark-role comparison, exact holdings/HODL attribution, flow audit, exact decision evidence, and advanced compounding view are closed;
- Paper Detail: `Execution audit`, `Technical execution details`, and nested valuation/reference-price disclosure are closed.

This keeps raw IDs, fingerprints, exact decimals, route details, and venue metadata out of the normal reading flow while preserving auditability on demand.

## Reduced motion

With browser emulation set to `prefers-reduced-motion: reduce`:

- the media query matched;
- maximum animation duration was `0s`;
- maximum transition duration was `0.00001s`;
- no element had animation/transition duration greater than `1ms`.

Nonessential motion is therefore effectively suppressed.

## Runtime and network gate

After the rendered fixes below, a fresh multi-route browser sweep across Research, Experiment, Portfolio, every Pair view/orientation, Paper index/detail, and not-found state reported:

```text
failed application Fetch/XHR requests: 0
console warnings/errors:              0
page errors:                          0
not-found <main> landmarks:           1
not-found primary navigations:        1
```

The final not-found state also passes axe with zero violations and zero incomplete findings.

## Serious regressions found and fixed

### 1. Duplicate application shell on the not-found route

**Observed:** `/not-a-route` rendered two complete shells: duplicate skip links, primary navigation, main landmarks, footer/attribution. Axe reported `landmark-main-is-top-level`, `landmark-no-duplicate-main`, and `landmark-unique` violations.

**Root cause:** the root layout already wrapped its outlet in `AppShell`, while the root `notFoundComponent` also wrapped itself in `AppShell`.

**Regression:** `web/src/app.test.tsx` now asserts an unknown route has exactly one `main` and one primary navigation. The test was observed RED before the fix.

**Fix:** `db3b8c9 fix: avoid duplicate not found shell` removes the redundant not-found shell while preserving the loader-error shell behavior.

**Rendered recheck:** one main, one primary navigation, axe `0 violations / 0 incomplete`.

### 2. Duplicate React keys in reduced anchor-log charts

**Observed:** the anchor view emitted two React console errors for duplicate key `BTC/USDT`.

**Root cause:** reduced anchor decomposition can legitimately contain two semantically distinct series with the same orientation display name but different units (`log anchor ratio` and `pair log ratio`). `TimeSeriesChart` keyed legend/cursor rows by display name alone.

**Regression:** `TimeSeriesChart.accessibility.test.tsx` now renders same-name/different-unit series and asserts no duplicate-key console error. The test was observed RED before the fix.

**Fix:** `a80facb fix: stabilize chart series keys` keys rendered series rows by `name + unit`.

**Rendered recheck:** anchor view has zero console warnings/errors, zero page errors, and axe `0 violations / 0 incomplete`.

## Standard frontend gate

Fresh after both rendered fixes:

```text
pnpm typecheck        PASS
pnpm typecheck:e2e    PASS
pnpm test             PASS — 20 files / 47 tests
pnpm build            PASS
python run_playwright_e2e.py PASS — 2/2 critical flows
```

The critical Playwright flows still prove:

1. Experiment -> Portfolio -> Pair Workbench through visible UI navigation;
2. Pair reciprocal orientation + anchor state remain URL-owned.

## Acceptance conclusion

The Phase-14 rendered acceptance contract is green for the tested current workbench states. Negative, invalid, final-OOS-consumed, reconciled, and no-fill semantics remain explicit in text; desktop/mobile/reflow widths are contained; audit surfaces are accessible on demand; keyboard focus and URL-owned analytical state behave correctly; reduced motion is honored; and the final browser runtime is free of failed application requests, console errors, page errors, axe violations, and axe incomplete findings.
