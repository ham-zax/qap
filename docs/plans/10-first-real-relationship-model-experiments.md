# Phase 10 — First Real Relationship-Model Experiments Implementation Plan

**Goal:** Introduce real statistical relationship evidence only after the inventory/accounting/replay/web chain is trustworthy, beginning with transparent pair and asset-level controls, then deciding through an explicit admission gate whether the historically important Student-t Copula hypothesis still deserves implementation.

**Architecture:** Statistical models live under `qap.relationship.models` and emit relationship observations only. Research policy converts declared model evidence into target-allocation tilts through the normal Phase-05 boundary. Pairwise models, a simple cross-sectional/common-mode control, and any admitted Copula are evaluated through identical replay/cost/benchmark machinery.

**Tech Stack:** Python 3.14, NumPy, SciPy, Pandas where rolling operations require it, pytest; historical v1/v2 inspected read-only under the admission protocol.

## Global Constraints

- Neither model is constitutional or automatically production-authoritative.
- Transparent pairwise and asset-level/common-mode controls are implemented before any Copula logic.
- Historical importance alone never requires reimplementation; the Copula branch may end as `REJECT` after Section 10.1 if there is no present falsifiable question that justifies code.
- Historical implementation details are re-admitted one claim at a time; no runtime import from v1/v2.
- Statistical fit is not economic validation.
- Thresholds/tilt sizes are manifest-declared experiment parameters, not global defaults.
- Research-family lineage, data roles, final-OOS consumption, and selection pressure are explicit.
- Every fitted model declares `OrientationBehavior`; canonical pair identity never implies reciprocal model equivalence automatically.
- No topology/network model, auto-hyperparameter optimizer, model registry, or promotion workflow.

## File Map

**Modify:**
- `pyproject.toml` — add SciPy only when Student-t implementation begins.

**Create:**
- `src/qap/relationship/models/__init__.py`
- `src/qap/relationship/models/rolling_log_ratio.py`
- `src/qap/relationship/models/cross_sectional_relative.py` — simple asset-level residual/deviation control against the declared basket common mode.
- `src/qap/relationship/models/student_t_copula.py` — **conditional:** create only if Section 10.1 admits a specific Student-t experiment.
- `src/qap/policy/evidence_tilt.py` — one bounded research policy for signed evidence scores.
- `src/qap/api/schemas.py` — extend pair evidence DTOs for model-series inspection.
- `src/qap/api/routes/pairs.py` — expose persisted relationship-model evidence for one run/pair.
- `web/src/features/pair-workbench/RelationshipEvidenceChart.tsx` — render model evidence with the existing Lightweight Charts primitive.
- `tests/unit/relationship/models/test_rolling_log_ratio.py`
- `tests/unit/relationship/models/test_cross_sectional_relative.py`
- `tests/unit/relationship/models/test_student_t_copula.py` — **conditional:** create only with the admitted Student-t implementation.
- `tests/unit/policy/test_evidence_tilt.py`
- `tests/scenarios/test_model_experiment_same_execution_contract.py`
- `tests/scenarios/test_model_oos_evaluation.py`
- `docs/research/` — concise experiment result notes only when an actual run is performed; no pre-created bureaucracy.

## Section 10.1 — Historical Admission Review for Copula Work

**Interfaces:**
- Consumes: read-only QAP v1/v2 docs/code and original/public mathematical references already identified by the project.
- Produces: a short implementation note inside the eventual Phase-10 commit or `docs/research/<date>-student-t-admission.md` recording admitted/rejected historical behaviors.

**Required review questions:**
1. What exact historical Student-t/Copula statistic was computed?
2. What input transformation/marginal/PIT semantics did it require?
3. Which parts were technically validated versus merely constitutionalized?
4. Which thresholds or fixed parameters failed to earn broad authority?
5. What negative v2 evidence limits the claim?
6. What clean-QAP contract is actually needed now?

**Admission classification:**
- No current falsifiable question or v2 negative evidence already makes the proposed retest redundant -> `REJECT` and stop the Copula branch without adding SciPy/Copula code.
- Mathematical behavior required for a specific current experiment -> `REIMPLEMENT` from explicit clean tests/specification.
- Historical fixed thresholds, BTC-only authority, mandatory degrees of freedom, or Copula-only policy -> `REJECT` unless current evidence separately justifies them.
- Small pure helper code may be `TRANSPLANT` only after source/license/ownership fit and clean tests are established.

**Steps:**
- [ ] Inspect the smallest relevant historical files with `rg`/focused reads; do not scan/copy the whole old architecture.
- [ ] Record the admitted model definition and explicit non-claims before implementation.

## Section 10.2 — Transparent Rolling Log-Ratio Model

**Interfaces:**
- Consumes: Phase-04 log-ratio series through `as_of` only, declared rolling window length.
- Produces: `RelationshipObservation` with signed standardized deviation score, coverage metadata, and `fit_reciprocity=exact_transform` and `evidence_reciprocity=exact_transform`.

**Formula:**

```text
z_t = (log_ratio_t - rolling_mean_t) / rolling_std_t
```

**Behavior:**
- Rolling window uses observations no later than `t`.
- Require a declared minimum number of observations.
- Zero/near-zero rolling standard deviation yields `insufficient_variance`, not infinity.
- This is a transparent comparison instrument, not an assertion that z-score trading is profitable.

**Steps:**
- [ ] Write hand-calculated and no-lookahead tests.
- [ ] Implement with deterministic rolling semantics and metadata.

**Verification:**

```bash
uv run pytest -q tests/unit/relationship/models/test_rolling_log_ratio.py
```

## Section 10.3 — Signed Evidence Tilt Policy

**Interfaces:**
- Consumes: one signed evidence score, neutral basket allocation, explicit enter/neutral thresholds, explicit maximum tilt.
- Produces: normal `PolicyDecision`/`AllocationTarget`.

**Behavior:**
- Positive score tilts toward one declared orientation leg; negative score tilts symmetrically toward the other.
- Score within neutral band returns neutral target or no-action according to manifest-declared mode.
- Weights remain long-only and within declared max tilt.
- The mapping is intentionally simple so economic differences are attributable to evidence, not an optimizer.

**Steps:**
- [ ] Write symmetric positive/negative/neutral tests.
- [ ] Implement only one score-to-tilt policy used by the transparent control and any Copula output that can lawfully be expressed as the same signed score.
- [ ] If historical Copula evidence is not semantically a signed score, do not force it into this policy; implement one explicit Copula research policy in the same file/package with its own tested semantics instead.

## Section 10.4 — Simple Cross-Sectional/Common-Mode Control

**Purpose:** Test whether explicit pair mining adds information beyond a simpler asset-level relative state built from the same owned basket.

**Interfaces:**
- Consumes: point-in-time returns for all assets in the declared basket and a frozen rolling window.
- Produces: per-asset relative-deviation scores and a normal long-only target-allocation tilt through the existing policy boundary.

**Behavior:**
- Define the simple common mode as the equal-weight mean return of the declared basket at each timestamp; no market-cap feed, PCA, optimizer, or external factor database is introduced.
- For each asset, compute its rolling relative return/deviation versus that common mode using only completed observations.
- Convert the resulting asset-level ranking/deviation into a bounded long-only target using one predeclared rule.
- This is a falsification control: if it matches/beats pairwise models, QAP must not attribute that gain to special pair intelligence.
- It does not claim to reproduce the Liu-Tsyvinski-Wu market/size/momentum factor model. If a pair model later survives the simple controls, a separate attribution experiment may add those richer factors when valid data is available.

**Steps:**
- [ ] Write no-lookahead and hand-calculated three-asset tests.
- [ ] Implement one transparent formula and one bounded allocation mapping; do not tune a family of cross-sectional variants.
- [ ] Record this control under the same research family and benchmark ladder as pairwise candidates.

## Section 10.5 — Student-t Copula Relationship Evidence (only if Section 10.1 returns `REIMPLEMENT`/`TRANSPLANT`)

If Section 10.1 returns `REJECT`, skip Section 10.5 entirely, omit the Copula member from Section 10.6's comparison, do not add SciPy for Copula, and preserve the rejection note as the result of that branch.

**Interfaces:**
- Consumes: synchronized admitted return/PIT inputs according to the admission note, through `as_of` only.
- Produces: typed model-specific `RelationshipObservation` plus any signed relative-dislocation score required by the research policy.

**Behavior:**
- Model parameters are explicit in manifest and output provenance.
- The implementation declares whether its chosen evidence quantity uses `directional_transform` or `refit_required`; it may use `exact_transform` only if that property is mathematically established for the actual fitted output, not merely because raw price ratios invert.
- Degrees of freedom are fit or declared according to the admitted experiment contract; `nu=4` is not hard-coded as constitutional truth.
- No Gaussian-vs-t ban is embedded in core architecture.
- Numerical failure/insufficient sample produces explicit invalid evidence rather than fallback model selection.
- Fit state belongs to the model instance/run and is never global mutable state.

**Steps:**
- [ ] Write synthetic-data tests for parameter recovery/finite outputs only to the degree they prove the chosen mathematical contract.
- [ ] Add historical clean-room parity fixture for one intentionally admitted v1 calculation where source data and expected output are independently reproducible.
- [ ] Implement using SciPy/NumPy with no import from historical repository.
- [ ] Record model/version/parameters and input fingerprint in each observation.

## Section 10.6 — Same-Contract Economic Comparison

**Interfaces:**
- Consumes: frozen experiment manifests differing only in relationship model/model policy parameters.
- Produces: paired economic results under identical data, starting inventory, execution costs, timing, HODL, and simple control.

**Experiments:**
1. Predeclared periodic/fixed-weight and band/partial controls from Phase 07.
2. Rolling-log-ratio pair evidence tilt.
3. Simple cross-sectional/common-mode control.
4. Student-t Copula evidence policy only when the admission gate allowed implementation.

**Behavior:**
- Freeze the whole comparison family (models, parameters, pair/basket, controls, cost scenarios, and primary incremental benchmark) before one `final_oos` evaluation.
- All members of that frozen family may be evaluated on the same final holdout in one committed comparison; after inspection, that holdout is consumed for the next research generation.
- Report HODL-relative portfolio wealth growth, relationship-policy increment over the primary simple control, cost/turnover, drawdown, per-asset contribution, concentration, and number of actionable decisions.
- Report model statistical diagnostics separately from economic results.
- Do not rank/promote a model automatically.

**Steps:**
- [ ] Add scenario ensuring all models route through the same executor and evaluation functions.
- [ ] Create one OOS fixture/run demonstrating result generation even when a model loses.

## Section 10.7 — Selection-Pressure and Factor-Attribution Record

**Behavior:**
- Every pair/model/horizon/parameter combination intentionally evaluated on the same research question shares a `research_family_id` and remains listed/discoverable, including failed siblings.
- If parameters are tuned on exploratory/development data, the chosen family is frozen before final-OOS evaluation.
- A consumed final-OOS result is never re-labeled as fresh validation after inspection.
- If a broad family search is used to support a formal superiority claim, perform an appropriate family-level multiplicity analysis (for example SPA/Reality-Check style) before making that claim; no universal multiplicity framework is built into the kernel.
- If a pair-driven candidate survives HODL, the predeclared simple rebalance control, and the simple cross-sectional/common-mode control, perform a separate common-factor attribution check before calling the remaining return pair-specific alpha. Full market/size/momentum factor attribution is conditional on valid point-in-time factor data and may limit the claim rather than block the whole phase.

**Steps:**
- [ ] Use the Phase-07 family/parent/data-role fields; do not create a second lineage registry.
- [ ] Test that final-OOS consumption remains immutable in persisted result.
- [ ] For any broad search actually used to support a superiority claim, record the selected family-level multiplicity method/result in the concise research note.

## Section 10.8 — Persist and Visualize Model Evidence

**Interfaces:**
- Consumes: relationship-model observations produced during a Phase-10 run.
- Produces: optional `runs/<run_id>/evidence.parquet`, pair-evidence API DTO/route data, and a Pair Workbench evidence chart.

**Behavior:**
- `evidence.parquet` stores timestamp, canonical pair/orientation, model ID/version, evidence field name, numeric presentation value, validity/status, and input/data fingerprint references.
- Evidence artifact is present only for runs that actually produce model evidence; its absence in older/model-free runs is normal.
- API exposes persisted evidence for the requested run/pair without recomputing the model in a route handler.
- React renders evidence in a synchronized lower pane using the existing Lightweight Charts wrapper; it does not introduce ECharts or model-side math.
- The pane labels evidence as statistical/model state and keeps HODL-relative economics visually separate.

**Steps:**
- [ ] Extend Phase-07 artifact writer/reader with schema-versioned optional `evidence.parquet`.
- [ ] Add API contract coverage for one evidence series and a model-free run with no evidence artifact.
- [ ] Add `RelationshipEvidenceChart.tsx` and synchronize it with the pair ratio chart's time range/crosshair.
- [ ] Add a focused frontend test for model label/value rendering; avoid pixel snapshots.

## Phase Verification

```bash
uv run pytest -q tests/unit/relationship/models tests/unit/policy/test_evidence_tilt.py tests/scenarios/test_model_experiment_same_execution_contract.py tests/scenarios/test_model_oos_evaluation.py tests/contract/api
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests
cd web
pnpm typecheck
pnpm test
pnpm build
```

For any actual experiment run, also verify its manifest/data/code fingerprints and inspect the generated result/evidence artifacts before writing a conclusion.

## Phase Exit Criteria

- [ ] Transparent rolling pair model and simple cross-sectional/common-mode control work without lookahead.
- [ ] Historical Student-t hypothesis has a documented admission decision and is either rejected without code or reimplemented through the clean contract only when a current falsifiable experiment justified it.
- [ ] Model outputs never bypass policy/allocation/execution boundaries.
- [ ] Models/controls are compared economically under identical costs/timing/benchmark-ladder semantics.
- [ ] Research family, final-OOS consumption, selection pressure, and model orientation behavior are explicit.
- [ ] Pair-specific alpha is not claimed when the result is explained by the simple cross-sectional/common-mode control or remains unattributed to broader common factors.
- [ ] Model evidence is inspectable in the existing Pair Workbench without frontend financial recomputation.
- [ ] No model receives automatic runtime authority.

## Stop Conditions

Return to research/design review if Copula implementation requires restoring v1's fixed constitutional thresholds, global model registry, BTC-only objective, giant gate stack, or hidden model state. A statistically elegant model that cannot demonstrate incremental economic value over the predeclared simple rebalancing control remains research-only. Do not expand Phase 10 into a full asset-pricing/factor-data platform merely to satisfy attribution; report the limitation and admit richer factor data only when a surviving candidate makes that question material.

## Final Targeted Phase-10 Admission Clarifications

### Executable pair-blind control
The common-mode/cross-sectional control is a real allocation policy, not merely an explanatory regression. It cannot see the explicitly mined canonical pair identity and must pass through the same target-allocation bounds, no-trade logic, timing, fees, slippage, quantization, and deterministic execution machinery as the pair-conditioned candidate.

Do not force realized turnover to match between control and candidate: deciding not to trade may be legitimate value. Report gross performance, turnover, concentration, explicit costs, and net incremental wealth separately.

### Two-asset degeneracy
For a basket containing only `X` and `Y`, an equal-weight internal common-mode residual is algebraically proportional to `r_X-r_Y`; it is not an independent falsification of pair information. A two-asset experiment may claim incremental value beyond HODL/mechanical/cost-aware rebalancing, but a stronger common-mode-independent pair claim needs a predeclared external broad-market proxy or additional basket assets.

### Incremental inferential object
For serious Phase-10 claims, evaluate both terminal relative wealth and the Phase-03 incremental net log-relative series against the predeclared strongest admissible non-pair control. Any uncertainty procedure must respect serial dependence.

### Student-t admission refinement
Student-t remains an early serious hypothesis after the transparent relationship control. Keep the first test small: one predeclared pair/small basket, one marginal transform, one lookback/refit schedule, one long-only allocation mapping, one cost model, chronological development, then one sealed final holdout.

A Gaussian Copula comparator is mandatory only when the claim is specifically that **Student-t tail dependence** adds incremental value. It is useful but not mandatory for the narrower first claim that one frozen Student-t-conditioned long-only policy beats the existing transparent/non-pair controls.

### Reuse statistical libraries
- Use `statsmodels` for established regression/econometric primitives instead of hand-rolling them.
- Evaluate `pyvinecopulib` before implementing Copula estimation/family logic ourselves; keep it behind `qap.relationship.models` so third-party types never become domain contracts.
- Use `arch` for block-bootstrap/family-level procedures when the research claim actually requires them.
- When pair/model/horizon scanning becomes large enough to justify acceleration, use DuckDB for Parquet pruning and Polars for vectorized feature computation rather than creating a custom scan engine.
- `vectorbt` may be evaluated as an isolated exploratory parameter-sweep accelerator; any surviving candidate must be replayed through QAP before economic/OOS conclusions.
- `skfolio` may be evaluated for candidate long-only target weights/CV only after transparent controls exist; it never mutates QAP inventory or defines success.
