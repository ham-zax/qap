# Agent 2 — M5 Research Experience / Truthful Funnel Reconnaissance

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** read-only
**Workspace:** `/home/hamza/repo/qap` read-only
**Can start:** immediately from the Wave-5 coordination base
**Depends on:** M3 complete; treat Agent 1's M4 mission as the expected backend truth contract, not implemented reality yet
**Execution lifetime:** `persistent-agent-loop` for continuity; do not manufacture waits

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-1-m4-current-approved-readiness.md`
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`
- `docs/research/2026-08-19-qap-human-centered-workbench-ux-investigation.md`
- `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`

## Mission

Produce the bounded repository-grounded reconnaissance needed to implement M5 immediately after M4 is integrated.

Investigate how the current Phase-16 specialist shell and Scanner/Product read models should converge into the frozen primary Product flow:

`Home | Research | Portfolios | History`

Focus on a non-expert Research experience that explains what QAP is researching, what data/timeframe it is using, how far discovery progressed, what each stage can/cannot conclude, and what valid action comes next.

This mission is read-only. Do not implement M5.

## Ownership

Investigate:

- current React route/shell composition and existing Phase-16 navigation;
- current Home/Discover/Validate/Results specialist views and their reusable components;
- existing scanner list/detail/candidate read models and real stage counts available today;
- M2 Product universe and M3 market-data APIs already integrated;
- the expected M4 readiness/safe-cutoff API contract from Agent 1's mission brief/reconnaissance;
- which backend states can truthfully drive a discovery funnel and next actions;
- the smallest M5 frontend/backend read-composition changes needed without moving scientific logic into React;
- what existing routes should remain stable behind the new primary IA;
- accessibility/progressive-disclosure implications for nontechnical and lower-digital-skill users.

## Legacy-salvage lens

Reuse concepts, not legacy runtime architecture.

Specifically investigate how current QAP can support truthful counts such as:

- approved assets;
- possible relationships actually enumerated by the current scanner;
- retained graph relationships;
- valid/deeper historical trials;
- promoted/replayed candidates;
- resulting Research Ideas.

Do not invent labels/counts that current artifacts cannot support. Do not use old TradingView/cointegration terminology merely because the legacy system used it.

For each major Research state, identify how the UI can answer:

1. What is happening?
2. What can this stage conclude?
3. What can it not conclude?
4. What valid action comes next?

Next actions must be authorized by backend state/contracts. React may translate enums into plain language but must not infer research/economic verdicts from raw metrics.

## Frozen UX boundaries

Normal Product flow must not require primary exposure of:

- scan IDs;
- candidate IDs;
- protocol IDs;
- manual replay IDs;
- checkpoint IDs;
- venue symbols;
- raw UTC `as_of`;
- model-family/template controls.

Audit/protocol/lineage details remain available under progressive disclosure.

Keep presentation states distinct:

- task failed;
- evidence incomplete;
- research rejected;
- research supported.

Do not collapse `direct_market_unavailable`, `history_missing`, or other readiness limitations into asset invalidity or research rejection.

## Questions to answer

1. Which current routes/components can be reused versus relabeled/recomposed for `Home | Research | Portfolios | History`?
2. What exact primary Research page information architecture should M5 implement after M4?
3. Which current scanner artifact/read fields can produce truthful funnel counts, and which desired counts need a small backend read-composition extension?
4. How should one selected timeframe drive Research without exposing backend `as_of` or raw protocol controls?
5. How should M4 readiness/exclusions appear before launch in plain language without losing structured detail?
6. What are the backend-authorized next actions for zero-state, needs-data, ready-to-research, running, completed-negative, completed-supported, and failure states?
7. Which specialist routes should remain as advanced/detail destinations rather than being deleted?
8. What minimum frontend/API boundary would let M5 stay presentation-only for science/economics/readiness?
9. What existing charts/tables/components are useful and what current primary surfaces are misleading for non-experts?
10. What M5 acceptance evidence should be used for representative nontechnical comprehension before M6 begins?

## Success conditions

- exact current route/component/read-model map;
- concrete proposed primary Research information architecture;
- truthful funnel/count source map grounded in existing artifacts;
- next-action state machine owned by backend truth, not UI inference;
- progressive-disclosure map for specialist IDs/protocol/lineage;
- explicit reuse/deletion/defer recommendations for current Phase-16 surfaces;
- bounded list of any M5-required backend read additions;
- no repository mutation.

## Verification intent

Read-only inspection only: focused source search/reads and Git status before/after. Do not run tests, builds, generators, downloads, captures, or mutating API calls.

## Out of scope

- M5 code/UI changes;
- changing M4 policy/readiness;
- M6 longitudinal Research Idea implementation;
- new scientific metrics/rules;
- deleting specialist routes before executable M5 composition proves they are unnecessary;
- importing legacy presenter/state-machine architecture.

## Finish report

Return:

1. status and read-only Git state before/after;
2. current route/component/read-model map;
3. proposed M5 primary IA and state flow;
4. truthful funnel/count source map;
5. backend-authorized next-action map;
6. smallest required API/read additions, if any;
7. reuse/defer/remove recommendations;
8. risks/stop conditions and M6 handoff implications.
