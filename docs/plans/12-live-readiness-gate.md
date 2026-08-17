# Phase 12 — Live-Readiness Gate Plan

**Goal:** Decide deliberately whether QAP has earned the right to begin a separate live-execution design; Phase 12 itself does not place live orders or create broker/exchange write capability.

**Architecture:** This is an evidence, semantics, security, compliance/action-space, and operational review over the completed paper system. A `GO` authorizes writing a new live-execution design spec only. A `NO-GO` records the exact blockers and leaves the paper product intact.

**Tech Stack:** Existing QAP paper stack, current official venue/API documentation, current applicable legal/regulatory source checks where relevant, security review tools already available in the development environment.

## Global Constraints

- Earlier phases never imply live-capital authority.
- User approval is mandatory after the readiness report.
- No private API key is required to conduct the readiness review.
- The spot-only/no-leverage/no-borrowing/no-derivatives/no-interest action boundary remains unchanged.
- Asset admission remains operator-controlled; QAP does not make religious certification claims.
- Any live implementation requires a new design spec and implementation plan after this gate.

## File Map

**Create during Phase 12:**
- `docs/reviews/YYYY-MM-DD-live-readiness.md` — evidence-based readiness report and `GO`/`NO-GO` recommendation.
- `docs/reviews/YYYY-MM-DD-live-readiness-evidence.md` — concise links/IDs to the exact runs, reconciliations, current venue contracts, and unresolved issues supporting the decision.

**Create only after explicit user approval of a `GO`:**
- `docs/superpowers/specs/YYYY-MM-DD-live-execution-design.md` — separate brainstorming/design artifact; not part of this phase's automatic work.

**Do not create in Phase 12:**
- authenticated exchange adapter;
- order placement/cancel code;
- secret files;
- live scheduler/daemon.

## Section 12.1 — Economic Evidence Gate

**Required evidence:**
- At least one frozen OOS experiment and one later non-overlapping OOS or forward-paper evaluation for the candidate policy/model family being considered for live design.
- Both use the same authoritative cost/timing/accounting contract as paper operation.
- Candidate is compared against matched HODL and the simple admissible rebalance control.
- HODL-relative portfolio wealth growth is positive in the declared readiness evidence, or any exception is explicitly justified and cannot be a relabeling of the objective.
- Cost, turnover, per-asset contribution, and concentration are reported.
- A result dominated by one pair/asset/window is labeled concentrated and is not presented as broad evidence.

**Steps:**
- [ ] Select/freeze exact run IDs before reviewing their outcome narrative.
- [ ] Re-run or independently verify data/config/code fingerprints.
- [ ] Reconcile terminal holdings/results with Phase-11 independent reconciliation.
- [ ] Record whether evidence supports continued research only, constrained live-design exploration, or no-go.

**Automatic NO-GO conditions:**
- unresolved accounting mismatch;
- negative/unstable primary result presented only through favorable secondary metrics;
- evidence depends on lookahead or changed OOS labels;
- candidate cannot beat matched HODL/simple control after declared realistic costs on the readiness windows.

## Section 12.2 — Determinism and Reconciliation Gate

**Required checks:**
- Repeat designated readiness runs from frozen manifests and compare authoritative artifacts.
- Recompute ending holdings from fill ledger independently.
- Confirm every cost is applied once.
- Confirm no negative balance, unsupported route, or silent data fallback occurred.
- Confirm bridge residues/dust are visible.

**Acceptance criteria:**
- Zero unresolved reconciliation discrepancies across designated readiness runs.
- Any nondeterminism is explained by explicitly modeled external input, not hidden state.

## Section 12.3 — Current Venue Contract Review

**Steps:**
- [ ] Use the then-current official venue documentation to verify spot order types, quantity/price filters, fee behavior, order IDs/idempotency capabilities, partial fills, cancel/reject semantics, rate limits, and account permissions.
- [ ] Verify the intended instruments are true spot instruments and do not require margin/borrowing/derivative mechanics.
- [ ] Record contract fields QAP would need and any paper-model mismatch.
- [ ] Do not infer live semantics from Phase-11 public-market-data endpoints.

**Acceptance criteria:**
- Every paper execution assumption has a mapped live venue semantic or a documented design gap.

## Section 12.4 — Live Order Lifecycle Requirements

Before `GO`, the readiness report must define requirements for a later design covering:

```text
intent
 -> submit with idempotent client identity
 -> venue acknowledgement
 -> zero/partial/full fill(s)
 -> cancel/reject/expire handling
 -> balance reconciliation
 -> restart recovery
```

**Required properties:**
- repeated submission cannot duplicate intended economic action silently;
- partial fills are first-class;
- local state is reconciled from venue truth after restart;
- unknown order state stops further dependent trading until reconciled;
- no local optimistic balance is treated as authoritative before venue confirmation.

These are requirements only; Phase 12 does not implement them.

## Section 12.5 — Capital and Failure Controls

The future live design must have explicit, user-approved values/mechanics for:

- maximum portfolio notional exposed to automated execution;
- maximum notional per rebalance/event;
- maximum route legs (still one or two under current architecture);
- stale-data timeout;
- maximum tolerated price deviation/slippage;
- daily/period loss or anomaly stop if the user chooses one consistent with the inventory objective;
- kill switch that prevents new orders without requiring a healthy strategy loop;
- fail-closed behavior on missing balances, metadata, timestamps, or ambiguous order state.

**Steps:**
- [ ] Identify which limits can be derived from venue/instrument constraints versus which require an explicit user risk decision.
- [ ] Mark unresolved user risk decisions as blockers to live implementation, not values to guess autonomously.

## Section 12.6 — Secret and Access Boundary

**Required future design properties:**
- trading API key has minimum necessary permissions;
- withdrawal permission disabled where venue supports permission separation;
- secrets stored outside Git/run artifacts/logs;
- no secret transmitted to agent prompts or documentation;
- test/sandbox credentials separated from production where venue supports them;
- logs redact authentication material.

**Steps:**
- [ ] Review current repository for accidental secret patterns before any key is introduced.
- [ ] Confirm paper code paths do not require secret configuration.

## Section 12.7 — Shariah/Action-Space Confirmation

**Steps:**
- [ ] Confirm live-design scope remains actual spot ownership and immediate spot conversion.
- [ ] Confirm no margin, auto-borrow, futures, perpetuals, options, CFDs, or interest-bearing mechanics are enabled by account/order configuration.
- [ ] Confirm any execution-only bridge asset is explicitly admitted by the operator.
- [ ] Record that asset-level suitability remains an operator/scholarly decision outside the engine's mechanical guarantees.

**Automatic NO-GO:** any required venue mechanism violates the declared action-space boundary.

## Section 12.8 — Current Legal/Operational Check

Because exchange access, venue rules, and applicable regulations can change, perform a fresh check using current authoritative sources at Phase-12 execution time for the user's actual jurisdiction and chosen venue.

**Steps:**
- [ ] Record only operationally relevant constraints that materially affect the planned live integration.
- [ ] Do not treat QAP's internal design as legal advice.
- [ ] Escalate unresolved legal/venue eligibility questions rather than guessing.

## Section 12.9 — Readiness Report Decision

**Report structure:**

```text
Decision: GO TO LIVE-DESIGN | NO-GO
Candidate/run evidence
Economic result vs HODL/control
Reconciliation result
Venue semantic mapping
Action-space confirmation
Security/secrets readiness
Operational failure gaps
Current jurisdiction/venue blockers
Required user decisions
Recommendation
```

**GO means only:** begin a fresh Superpowers brainstorming/design cycle for live execution.

**NO-GO means:** continue paper/research work with named blockers; do not create live-order code.

## Verification

Run the exact current completion suite for paper QAP before signing the report, plus designated readiness manifests and reconciliation commands. The report must cite concrete run IDs/commit hashes/commands rather than saying "tests passed" without evidence.

## Phase Exit Criteria

- [ ] Readiness report and evidence file are complete.
- [ ] Paper economic/accounting evidence is freshly reverified.
- [ ] Current venue semantics and jurisdiction-relevant constraints were checked from authoritative sources.
- [ ] Action-space/security/failure-recovery requirements are explicit.
- [ ] Decision is `NO-GO` or `GO TO LIVE-DESIGN`; there is no implicit live implementation.
- [ ] User reviews the decision before any live design begins.

## Stop Conditions

Immediately stop the phase and recommend `NO-GO` on unresolved accounting/reconciliation, lookahead, hidden state affecting decisions, action-space violation, ambiguous venue order truth, or a need to invent user capital-risk limits without user input.
