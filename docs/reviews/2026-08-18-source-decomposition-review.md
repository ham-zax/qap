# QAP Source Decomposition Review — 2026-08-18

**Trigger:** `uv run python scripts/check_source_size.py` reports eight hand-written source/test files in the 500–700-line review zone. The hard cap remains green.

**Decision rule:** 500 lines is a decomposition-review trigger, not a mandatory split. Split only when a file has multiple independent reasons to change or a stable ownership boundary can be named. Do not create thin indirection modules merely to silence the warning.

## Current warning set

| File | Lines | Current ownership | Decision |
|---|---:|---|---|
| `src/qap/experiment/controls.py` | 658 | Mechanical/control policy implementations plus shared allocation/drift helpers used by those controls | **KEEP for now.** The policies form one benchmark-control family and share exact allocation helpers. Next new unrelated control family must first evaluate a split into `control_math.py` + specific control modules; do not add model policy composition here. |
| `src/qap/experiment/artifacts.py` | 621 | Immutable experiment artifact lifecycle: reserve/write/read/validate/family discovery/final-OOS commitment | **KEEP for now, no new responsibility.** The file is cohesive around one artifact aggregate, but it is near the cap. A new artifact class (scan/candidate/paper/etc.) must live in its own module; do not add Phase-15 scanner persistence here. If experiment run reading/writing independently expands, split writer/reader behind the existing public artifact API. |
| `src/qap/market/adapters/binance_public.py` | 616 | Single Phase-02 public Binance Spot adapter, normalization and public kline/metadata semantics | **KEEP for now.** One external adapter is intentionally the authority boundary. If a second public endpoint family adds materially different parsing/state (archives, trade history, point-in-time eligibility), split by Binance public endpoint responsibility while keeping one adapter facade; do not introduce a generic multi-venue framework. |
| `src/qap/experiment/manifest.py` | 581 | Current-schema immutable experiment manifest/spec models and validation | **KEEP for now.** The size comes from related schema types rather than multiple runtime responsibilities. Phase-15 scan schemas must not be appended here; they get a scanner-domain schema module. Split only if experiment manifest submodels gain independent lifecycle/versioning. |
| `tests/integration/market/test_binance_public_adapter.py` | 541 | Integration contract for the single public Binance adapter, including metadata/filter/kline/live-smoke cases | **KEEP for now.** Test grouping mirrors one production boundary. If the production adapter splits by endpoint family, split this test file along the same boundary; do not split tests solely by arbitrary line count. |
| `tests/unit/experiment/test_artifacts.py` | 536 | Unit/contract tests for the experiment run artifact aggregate and final-OOS commitment lifecycle | **KEEP for now.** Scenarios share fixtures and one artifact aggregate. If `artifacts.py` is split into writer/reader contracts, split this test file in lockstep. Phase-15 scan artifact tests go in a new scanner test module instead. |
| `src/qap/experiment/model_policies.py` | 519 | Composition of admitted model evidence into replay policies for momentum, rolling-log-ratio, and cross-sectional models | **REVIEW BEFORE NEXT MODEL.** Current content is cohesive enough, but a fourth materially different model family should trigger extraction into model-family composer modules with a small dispatcher. No speculative registry/base-class framework now. |
| `src/qap/experiment/paper_operation.py` | 508 | Forward-paper spec loading, public-input normalization, policy-owned rebalance planning, execution/reconciliation serialization, immutable artifact I/O | **KEEP at current responsibility ceiling.** The recent fix removed duplicate target planning rather than adding new authority. Any new paper-operation mode, lineage type, or API workflow must go elsewhere. A future split should separate spec/input decoding from record serialization only if either side grows independently; do not fragment the current deterministic workflow preemptively. |

## Phase-14 plan decomposition

The review also identified `docs/plans/14-analytical-workbench-ux-redesign.md` at 1,261 lines. Although plan/docs are intentionally outside the automated source hard cap, that file had become a planning God object: design-system decisions, six route specifications, implementation tasks, regression policy, standards research, and the scanner boundary all changed for different reasons.

It has therefore been decomposed into:

- `docs/plans/14-analytical-workbench-ux-redesign.md` — concise phase overview/index and cross-phase boundary;
- `docs/plans/14/architecture-and-design-system.md` — presentation architecture, UX laws, tokens, controls, charts, accessibility;
- `docs/plans/14/research-and-portfolio-routes.md` — Research Runs, Experiment Detail, Portfolio Economics and Phase-11 navigation contract;
- `docs/plans/14/pair-and-paper-routes.md` — Pair Workbench and Paper Operations;
- `docs/plans/14/acceptance-and-regression.md` — serious regression, Playwright, Agent Browser and completion gates.

The active scanner/candidate workflow is no longer a footnote inside the UX plan. It now has its own authoritative phase plan: `docs/plans/15-research-scanner-and-candidate-workbench.md`.

## Guardrails for future changes

1. Re-run `scripts/check_source_size.py` before adding substantial responsibility to any warned file.
2. A warned file may grow only when the new behavior shares the same reason to change; otherwise create a focused sibling module first.
3. Do not move code into generic `utils`, base classes, registries, or facades solely to reduce line count.
4. New Phase-15 scanner schemas/persistence/execution orchestration must not be appended to `experiment/manifest.py`, `experiment/artifacts.py`, or `paper_operation.py` just because those files already handle artifacts/configuration.
5. If a warned file exceeds the 700-line hard cap, stop and perform an explicit design split before implementation unless the user grants a documented exception.

## Verification evidence

Fresh review command:

```text
uv run python scripts/check_source_size.py
source-size: ok (8 review warning(s))
```

No production source file was split merely to make that output quieter. The plan split above addresses the actual mixed-responsibility God-object finding while preserving coherent source ownership.
