# QAP Phase 16 — M4 Boundary Stop and Implementation Handoff

Update context — 2026-08-19
Trigger: Phase 16 M2 and M3 were implemented, then the explicit M4 current-evidence capture boundary failed during owner tracing.
Purpose: Preserve the completed presentation work and give the next agent one exact continuation point without encouraging a frontend capture oracle.
Impact: M2 and M3 are complete. M4 is stopped before mutation pending one bounded backend read-composition decision. No scientific/economic rule or mutation command changed.
Evidence: `eb40327`, `b1cce7a`, `ForwardCohortDetailDto`, `ProspectiveDetail.tsx`, `qualification_run.py::_capture_state`, and the Phase-16 M4 stop condition.

## 1. Repository state at stop

```text
Repository: /home/hamza/repo/qap
Branch:     main
HEAD:       b1cce7a feat: simplify discovery research flow
Tree:       clean before this handoff document
```

Recent implementation commits:

```text
b1cce7a feat: simplify discovery research flow
eb40327 feat: add phase16 home and shell
b9d4a65 docs: add phase16 implementation handoff
```

## 2. Completed — M2 Home + shell

Commit: `eb40327`

Implemented:

- `/` now composes the existing `experiments()`, `operations()`, and `forwardCohorts()` reads;
- first viewport presents Find research ideas / Continue validation / Analyze a portfolio / Review prior results;
- Home shows at most one running task, up to three resumable validations, and three recent research results;
- primary navigation is `Home / Discover / Validate / Portfolios / Results / Activity`;
- stable routes remain unchanged;
- Paper Operations left primary navigation but its routes remain intact.

No backend, new route path, dependency, shared style, or test change was made.

## 3. Completed — M3 Discover + Research Idea

Commit: `b1cce7a`

Implemented:

- Discover leads with analysis date/time and research timeframe;
- manual pins, forensic mode, replay IDs, and scanner protocol details are under native advanced disclosure;
- primary action is `Find research ideas`;
- Scan Detail groups only persisted statuses into:
  - passed historical checks;
  - evaluated but rejected;
  - valid rules not replayed;
  - invalid/unavailable evidence;
- survivor ideas appear before the complete ledger;
- the full denominator remains under `All evaluated rules`;
- Research Idea detail leads with a plain historical verdict and benchmark context;
- Candidate IDs, model/template/orientation, promotion, lineage, and exact links remain under advanced/exact evidence;
- the eligible next action is `Start forward validation`;
- no frontend score or scientific calculation was added.

No backend, API, route, schema, shared style, dependency, or test change was made.

## 4. Verification actually performed

After each milestone:

```text
cd web && pnpm build
```

Both passes completed successfully. This command ran TypeScript checking and the Vite production build.

Tests were not run or modified. `web/src/app.test.tsx` still contains pre-M2 primary-navigation text expectations and will need deliberate synchronization when testing is explicitly in scope or required at closure.

## 5. M4 stop condition — fired

No M4 source file was changed.

The current `ForwardCohortDetailDto` exposes only:

```text
summary
freezes
checkpoints
qualifications
```

It does not expose:

```text
current capture inventory
capture-contract readiness for an explicit as_of
missing capture kinds
the authoritative direct-market venue symbol
the authoritative capture base/quote identity
```

The current frontend therefore cannot determine the correct finite `capture_public_evidence` action without guessing. In particular:

- `CandidateFreezeDto` has venue and pair/orientation but no direct-market venue symbol;
- `ProspectiveDetail.tsx` currently guesses `USDT` as quote and leaves venue symbol for manual entry;
- capture readiness is a multi-observation contract evaluated relative to explicit `as_of` by backend-owned `evaluate_capture_contract`;
- a published qualification exposes the evidence it consumed only after assessment and cannot serve as pre-assessment readiness.

This is exactly the Phase-16 M4 backend stop condition. Do not work around it in React.

## 6. Smallest proposed continuation

This is a proposal, not an implemented or frozen contract.

Add one bounded read composition for a selected forward checkpoint and explicit `as_of`. It should:

1. resolve the authoritative direct-market instrument from existing QAP/forward lineage;
2. read the existing public-capture artifacts;
3. call the existing backend capture-contract evaluator;
4. return the exact venue / venue symbol / base / quote target;
5. return L1 and depth captured/expected coverage, metadata availability, overall readiness, and missing finite capture kinds.

A route shaped like the following is reasonable, but the next agent must confirm the existing API conventions before freezing it:

```text
GET /api/forward/cohorts/{cohort_id}/capture-readiness
    ?checkpoint_id=...
    &as_of=...
```

Keep all seven mutation commands unchanged. The frontend should still invoke the existing finite `capture_public_evidence` command one kind at a time using backend-returned identity. Do not add a generic capture/job endpoint and do not make the browser evaluate coverage.

Before implementing this API change:

- record the decision in the Phase-16 plan;
- update the OpenAPI/interface plan;
- preserve the existing authority and no-live-trading boundaries.

## 7. M4 presentation work after the boundary is resolved

Then complete M4 in this order:

```text
Forward Validation summary + visible freeze boundary
→ Update forward evidence
→ Check/update current market evidence
→ Amount to evaluate
→ Current capital assessment result
```

Primary wording must use:

```text
Forward validation
Update forward evidence
Update current market evidence
Current capital assessment
Amount to evaluate
```

`tradable_now` must render as `Current evidence supports this amount` and always include:

> Research assessment only — QAP does not place or authorize live trades.

Exact checkpoint/capture/q-safe/gate/snapshot values remain under advanced/exact evidence.

## 8. Fresh-agent mission

> Work in `/home/hamza/repo/qap` on `main`. Confirm HEAD and dirty state, then read `docs/research/2026-08-19-qap-phase16-m4-boundary-stop-handoff.md`, the Phase-16 implementation handoff, UX investigation, and Phase-16 plan. M2 is complete at `eb40327`; M3 is complete at `b1cce7a`. Do not redo them. M4 source work has not started because the documented current-evidence capture stop condition fired: the existing forward detail read model cannot supply authoritative capture identity or readiness for an explicit checkpoint/as-of. Before source mutation apply Causal Coding, Ponytail, and MCP Harness Router. Confirm the smallest bounded backend read composition, record the plan/OpenAPI decision, implement it without changing the seven mutation commands, then finish the M4 staged presentation. Do not build a frontend capture oracle or generic capture/job API. Checkpoint M4 before proceeding to M5.
