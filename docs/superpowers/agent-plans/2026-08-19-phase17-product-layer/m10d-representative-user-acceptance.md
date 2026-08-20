# Phase 17 M10-D — Representative-User Comprehension / Authority Closure

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** human-led acceptance / qualitative evidence
**Baseline:** integrated Product through M10-C at `3e07878`
**Can start:** now
**Depends on:** M10-A `12ed08a`, M10-B `f39b4b4`, M10-C proof `3e07878`
**Execution owner:** human moderator + actual/likely representative users

## Purpose

Close Phase 17 only after the corrected Product can be used and explained by the intended audience without developer coaching.

This is not a coding-agent simulation and not another technical proof. Do not fabricate participant reactions, completion rates, timings, or usability scores.

## Representative-user profile

Use actual or likely QAP users/stakeholders. Prefer people with limited developer knowledge and limited professional-trading expertise where practical, because the Product is explicitly intended to make the research machinery usable without requiring backend vocabulary.

Developer self-review alone does not satisfy this gate.

## Moderator rules

- Give the participant the task and goal, not the click path.
- Do not explain canonical identity, fingerprints, protocol IDs, recipe hashes, scanner internals, or research-family semantics before the participant encounters them.
- Normal clarification of the task is allowed; coaching on how QAP works is not.
- If the participant asks what a Product term means, first ask what they think it means from the interface. Record that interpretation before explaining anything after the task.
- Do not change scientific/economic meaning in order to obtain a pass.
- Record qualitative evidence in the participant's own words where useful; do not invent quantitative metrics.

## Required task journey

The participant should attempt these realistic tasks against the integrated Product:

1. **Find exact W**
   - Locate the asset whose code is exactly `W` rather than a substring match such as `WAL`, `WAN`, `AAVEDOWN`, or `BTCDOWN`.
   - Select it without the result list obscuring the next action on a small/mobile screen when such a device is available.

2. **Start W / BTC Pair Research**
   - Select `W` and `BTC`.
   - Choose one Product timeframe.
   - Understand what QAP will check before it can run.
   - If identity, approval, or market-data setup is required, complete the prompted task and return to the same unfinished pair research without re-entering the pair/timeframe.

3. **Interpret Pair Research support**
   - Explain whether the recipe can run now and why.
   - Distinguish a setup/data blocker from a method-capability blocker.
   - If runnable, launch it and find the resulting sibling experiment runs / Activity status.

4. **Scan My Universe**
   - Find and start the normal Universal Scan path.
   - Explain at a high level what is being scanned and what the stage/funnel counts mean.
   - Understand that rejected/unavailable/negative results remain valid research evidence rather than application failure.

5. **Check a named method in Experiment Lab**
   - Inspect a currently executable method and a known-unimplemented method such as Student-t Copula.
   - Explain the difference between `method unsupported/unimplemented` and `the selected pair is incompatible`.
   - Confirm that a non-runnable support result cannot be launched.

6. **Interpret simultaneous blockers**
   - Use the curated paper-replication example or another prepared declaration that produces more than one support reason.
   - Explain that capability, authority, readiness, fidelity, and structural truth can coexist rather than one status replacing the others.
   - Identify when QAP is blocked by its constitution (for example a required short position) versus merely missing an implementation.

7. **Exact replication versus adaptation**
   - Inspect the declared research components: relationship/evidence, decision rule, allocation/rebalance, risk, parameter selection, execution/costs, benchmark/evaluation, and OOS/data role.
   - Explain why a QAP adaptation is not the same claim as faithfully reproducing the cited external method.

8. **Evidence layers and History**
   - Open a completed manual recipe experiment and its advanced provenance.
   - Distinguish model/relationship evidence, economic replay, later/current evidence, and operational Activity.
   - Understand that manual experiments do not automatically become scanner-discovered Research Ideas.

9. **Approved versus ready / Product versus strict PIT**
   - Explain the difference between an approved asset and an asset that is ready for research data-wise.
   - Explain that normal Product research uses the current-approved retrospective claim while strict historical point-in-time discovery remains a separate Advanced Research claim.

10. **Hypothetical capital and live authority**
    - Explain what a hypothetical-capital/current-evidence assessment means.
    - State correctly that QAP does not recommend trades, authorize live capital, or place live orders.

## Evidence record per participant

Record only what was actually observed:

```text
Participant profile (non-identifying):
Device / viewport:
Workspace mode:

Task 1 exact W:
  completed / blocked / misunderstood
  observation:

Task 2 W/BTC Pair Research:
  completed / blocked / misunderstood
  observation:

Task 3 support/setup distinction:
  completed / blocked / misunderstood
  participant explanation:

Task 4 Universal Scan:
  completed / blocked / misunderstood
  participant explanation:

Task 5 method support:
  completed / blocked / misunderstood
  participant explanation:

Task 6 simultaneous blockers / constitution:
  completed / blocked / misunderstood
  participant explanation:

Task 7 replication vs adaptation:
  completed / blocked / misunderstood
  participant explanation:

Task 8 evidence layers / History:
  completed / blocked / misunderstood
  participant explanation:

Task 9 approved-ready / Product-PIT:
  completed / blocked / misunderstood
  participant explanation:

Task 10 hypothetical capital / live authority:
  completed / blocked / misunderstood
  participant explanation:

Unexpected confusion or friction:
What the participant expected instead:
Moderator coaching required, if any:
```

Do not record secrets, credentials, or unnecessary personally identifying information.

## Decision rules

### ACCEPT M10-D

Accept only when representative-user evidence shows the corrected primary jobs are operable without developer coaching and the protected meanings above are understood well enough that the user does not cross a scientific/economic authority boundary.

### UX REMEDIATION

Use this when the backend/scientific meaning is correct but the participant cannot discover or operate the intended task because of presentation, hierarchy, wording, mobile interaction, or recoverability friction.

A remediation should remain small and must preserve backend-owned scientific truth. Re-run the affected acceptance task afterward.

### DESIGN REVIEW

Return to design review when the participant's misunderstanding exposes a protected semantic problem rather than a presentation problem, including confusion that would require changing:

- scientific/economic authority;
- current-approved versus strict-PIT claim meaning;
- asset identity/admission authority;
- recipe/support/fidelity semantics;
- final-OOS/family discipline;
- hypothetical versus live-capital authority.

Do not "fix" such a failure by making React invent a more convenient scientific meaning.

## M10-D deliverable

When representative-user sessions are complete, create one qualitative closure report under `docs/research/` that records:

- integrated baseline used;
- non-identifying participant profiles relevant to representativeness;
- observed task outcomes and participant explanations;
- concrete UX issues/remediations, if any;
- protected-concept misunderstandings, if any;
- final verdict: `APPROVE M10-D`, `UX REMEDIATION REQUIRED`, or `DESIGN REVIEW REQUIRED`.

Phase 17 closes only on `APPROVE M10-D`.
