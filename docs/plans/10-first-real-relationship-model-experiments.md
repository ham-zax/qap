# Phase 10 — First Real Relationship-Model Experiments Implementation Plan

**Goal:** Introduce real statistical relationship evidence only after the inventory/accounting/replay/web chain is trustworthy, beginning with a transparent rolling log-ratio control and then deciding through an explicit admission gate whether the historically important Student-t Copula hypothesis still deserves implementation.

**Architecture:** Statistical models live under `qap.relationship.models` and emit relationship observations only. Research policy converts declared model evidence into target-allocation tilts through the normal Phase-05 boundary. Both models are evaluated through identical replay/cost/HODL/control machinery.

**Tech Stack:** Python 3.14, NumPy, SciPy, Pandas where rolling operations require it, pytest; historical v1/v2 inspected read-only under the admission protocol.

## Global Constraints

- Neither model is constitutional or automatically production-authoritative.
- The transparent control is implemented before any Copula logic.
- Historical importance alone never requires reimplementation; the Copula branch may end as `REJECT` after Section 10.1 if there is no present falsifiable question that justifies code.
- Historical implementation details are re-admitted one claim at a time; no runtime import from v1/v2.
- Statistical fit is not economic validation.
- Thresholds/tilt sizes are manifest-declared experiment parameters, not global defaults.
- OOS windows and selection pressure are explicit.
- No topology/network model, auto-hyperparameter optimizer, model registry, or promotion workflow.

## File Map

**Modify:**
- `pyproject.toml` — add SciPy only when Student-t implementation begins.

**Create:**
- `src/qap/relationship/models/__init__.py`
- `src/qap/relationship/models/rolling_log_ratio.py`
- `src/qap/relationship/models/student_t_copula.py`
- `src/qap/policy/evidence_tilt.py` — one bounded research policy for signed evidence scores.
- `src/qap/api/schemas.py` — extend pair evidence DTOs for model-series inspection.
- `src/qap/api/routes/pairs.py` — expose persisted relationship-model evidence for one run/pair.
- `web/src/features/pair-workbench/RelationshipEvidenceChart.tsx` — render model evidence with the existing Lightweight Charts primitive.
- `tests/unit/relationship/models/test_rolling_log_ratio.py`
- `tests/unit/relationship/models/test_student_t_copula.py`
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
- Produces: `RelationshipObservation` with signed standardized deviation score and coverage metadata.

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

## Section 10.4 — Student-t Copula Relationship Evidence (only if Section 10.1 returns `REIMPLEMENT`/`TRANSPLANT`)

If Section 10.1 returns `REJECT`, skip Sections 10.4–10.5's Copula-specific work, do not add SciPy for Copula, and preserve the rejection note as the result of that branch.

**Interfaces:**
- Consumes: synchronized admitted return/PIT inputs according to the admission note, through `as_of` only.
- Produces: typed model-specific `RelationshipObservation` plus any signed relative-dislocation score required by the research policy.

**Behavior:**
- Model parameters are explicit in manifest and output provenance.
- Degrees of freedom are fit or declared according to the admitted experiment contract; `nu=4` is not hard-coded as constitutional truth.
- No Gaussian-vs-t ban is embedded in core architecture.
- Numerical failure/insufficient sample produces explicit invalid evidence rather than fallback model selection.
- Fit state belongs to the model instance/run and is never global mutable state.

**Steps:**
- [ ] Write synthetic-data tests for parameter recovery/finite outputs only to the degree they prove the chosen mathematical contract.
- [ ] Add historical clean-room parity fixture for one intentionally admitted v1 calculation where source data and expected output are independently reproducible.
- [ ] Implement using SciPy/NumPy with no import from historical repository.
- [ ] Record model/version/parameters and input fingerprint in each observation.

## Section 10.5 — Same-Contract Economic Comparison

**Interfaces:**
- Consumes: frozen experiment manifests differing only in relationship model/model policy parameters.
- Produces: paired economic results under identical data, starting inventory, execution costs, timing, HODL, and simple control.

**Experiments:**
1. Simple periodic rebalance control from Phase 07.
2. Rolling-log-ratio evidence tilt.
3. Student-t Copula evidence policy only when the admission gate allowed implementation.

**Behavior:**
- Use identical OOS window for final comparison.
- Report HODL-relative portfolio wealth growth, cost/turnover, per-asset contribution, concentration, and number of actionable decisions.
- Report model statistical diagnostics separately from economic results.
- Do not rank/promote a model automatically.

**Steps:**
- [ ] Add scenario ensuring all models route through the same executor and evaluation functions.
- [ ] Create one OOS fixture/run demonstrating result generation even when a model loses.

## Section 10.6 — Selection-Pressure Record

**Behavior:**
- Every model/parameter combination intentionally evaluated on the same research question is listed in the result note/manifest family.
- If parameters are tuned in-sample, the chosen rule is frozen before OOS evaluation.
- OOS result is not re-labeled as validation after inspection.
- No automatic multiple-testing correction framework is required yet; the minimum requirement is honest enumeration and frozen OOS evaluation.

**Steps:**
- [ ] Add experiment metadata field/list for related model/parameter trials if Phase-07 manifest cannot already express it.
- [ ] Test that OOS role remains immutable in persisted result.

## Section 10.7 — Persist and Visualize Model Evidence

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

- [ ] Transparent rolling relationship model works without lookahead.
- [ ] Historical Student-t hypothesis has a documented admission decision and is either rejected without code or reimplemented through the clean contract only when a current falsifiable experiment justified it.
- [ ] Model outputs never bypass policy/allocation/execution boundaries.
- [ ] Models are compared economically under identical costs/timing/baselines.
- [ ] OOS and selection-pressure metadata are explicit.
- [ ] Model evidence is inspectable in the existing Pair Workbench without frontend financial recomputation.
- [ ] No model receives automatic runtime authority.

## Stop Conditions

Return to research/design review if Copula implementation requires restoring v1's fixed constitutional thresholds, global model registry, BTC-only objective, giant gate stack, or hidden model state. A statistically elegant model that cannot demonstrate incremental economic value over HODL/simple control remains research-only.
