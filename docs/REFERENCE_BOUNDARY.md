# QAP Historical Reference Boundary

## Status

This document is constitutional for the clean QAP repository.

QAP v1 and QAP v2 live in the historical repository at `/home/hamza/repo/tradingview_ratio`. They are evidence sources for this project. They are not the foundation of this project's architecture.

## Rule

> **QAP v1 and QAP v2 are read-only reference corpora. They are not architecture templates, runtime dependencies, specifications, or automatic sources of authority for the clean QAP.**

The clean QAP must never import runtime code from the historical repository.

Historical code, docs, experiments, formulas, thresholds, and architecture must earn readmission one claim at a time.

## QAP v1 may be used for

- recovering original product intent;
- behavioral examples and UX ideas;
- historical algorithms and mathematical formulas;
- identifying implementation lessons that were actually correct;
- understanding concrete failure modes;
- behavioral parity checks when parity is intentionally desired.

QAP v1 does **not** automatically authorize:

- its CLI architecture;
- hidden environment-driven business state;
- split configuration ownership;
- trade-lifecycle-as-domain-model semantics;
- Student-t Copula as constitutional authority;
- BTC as a mandatory final accumulation target;
- accumulated gates, vetoes, thresholds, or feature machinery;
- any file, class, dependency, or abstraction merely because it existed before.

## QAP v2 may be used for

- falsification evidence;
- negative research results;
- data and temporal-correctness lessons;
- provenance and reproducibility lessons;
- discovery-object and promotion-object mismatch findings;
- lifecycle/expression findings from the R-series;
- evidence about concentration, controls, OOS behavior, and cost drag;
- warnings about research-process bloat.

QAP v2 does **not** automatically authorize:

- research governance as product architecture;
- its large documentation regime;
- candidate/promotion bureaucracy;
- a pair-only research object as the product's economic object;
- any model, feature, topology, or threshold that failed to earn robust authority;
- replay/runtime structure merely because it was carefully documented.

## Admission protocol

Every historical capability follows this protocol before entering clean QAP:

1. State the historical claim in plain language.
2. Identify the evidence supporting or contradicting it.
3. State the present clean-QAP requirement it would satisfy.
4. Identify the invariant it must preserve.
5. Choose one action:
   - `REIMPLEMENT` — the behavior is useful, but clean ownership is more important than code reuse;
   - `TRANSPLANT` — a small, isolated implementation is already correct and fits the new contract;
   - `WRAP_TEMPORARILY` — temporary migration aid only, with an explicit removal condition;
   - `REJECT` — not needed, not proven, or architecturally harmful.
6. Write a clean-QAP test or executable verification for the admitted behavior before relying on it.
7. Record provenance when the historical source materially informed the implementation.

## Forbidden coupling

The following are forbidden:

```python
from tradingview_ratio import ...
from old_qap import ...
```

Likewise forbidden are:

- symlinked runtime dependencies into the old repository;
- shelling out to old-QAP commands as part of normal runtime behavior;
- reading old-QAP configuration as hidden runtime state;
- sharing mutable data stores whose schema is owned by v1/v2;
- silently copying old constants or thresholds without provenance and justification.

## Reference workflow

Historical inspection is allowed during design, research, migration, and debugging. The old repository should remain untouched unless the user explicitly authorizes a separate historical-repo change.

The default question is not:

> What old code should we copy?

It is:

> What truth, invariant, behavior, or negative lesson has earned the right to exist in clean QAP?

## Why this boundary exists

QAP v1 accumulated mechanisms until experiments became architecture. QAP v2 accumulated governance until the proof process became the product. Clean QAP must keep enough discipline to prevent v1's ownership and feature accretion without recreating v2's procedural accretion.
