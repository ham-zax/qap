# QAP

QAP is a spot-only crypto wealth-compounding system built around explicit inventory ownership and relative rebalancing. It manages a curated set of assets the operator is willing to own, measures their relative relationships, and uses economically justified reallocations to improve the portfolio.

The primary product objective is **portfolio wealth growth relative to matched passive HODL after realistic costs**. Coin-unit accumulation remains a secondary outcome and attribution lens. A fiat/crypto numeraire is used to value heterogeneous holdings consistently; it is a measurement coordinate, not a directional market-prediction objective.

## Current repository state

This repository is intentionally documentation-only while the final pre-build review/research handoff completes. The independent oracle review has been integrated into the plans. No trading engine, API, web application, or execution integration is implemented yet.

Start here:

- `docs/superpowers/specs/2026-08-17-qap-system-design.md` — economic/domain/system design.
- `docs/superpowers/specs/2026-08-17-qap-web-operations-design.md` — web, API, verification, maintainability, operational boundaries, and phase map.
- `docs/REFERENCE_BOUNDARY.md` — rules for using QAP v1/v2 as historical evidence.
- `docs/plans/README.md` — plan map and phase order.
- `docs/superpowers/plans/2026-08-17-qap-master-implementation-plan.md` — master implementation plan.
- `docs/reviews/2026-08-17-design-plan-review.md` — engineering/reflection review and remaining intentional uncertainties.

The next implementation step is Phase 00 after the user's current review/research handoff. One targeted statistical research pass may refine later Phase 07/10 rules, but it does not block Phase 00 unless it reveals a critical contradiction in the agreed economic/accounting/research constitution.

## Review and OSS Baselines

The design has passed the final targeted pre-build quantitative admission review with **Phase-00 GO / no critical pre-build blockers**. Phase-specific statistical claim gates remain in Phases 07/10 rather than blocking the economic kernel.

Open-source reuse is governed by [`docs/OSS_REUSE_BOUNDARY.md`](docs/OSS_REUSE_BOUNDARY.md): reuse mature commodity tooling where it saves code, but never delegate QAP's inventory/accounting/replay/research semantics to a generic trading framework.
