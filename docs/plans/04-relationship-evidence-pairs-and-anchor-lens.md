# Phase 04 — Relationship Evidence, Pairs, and Anchor Lens Implementation Plan

**Goal:** Implement transparent, model-free relative relationship evidence for any admitted pair, including raw ratio, log ratio, normalized paths, explicit orientation, and anchor decomposition.

**Architecture:** `qap.relationship` consumes synchronized point-in-time market series and produces immutable evidence objects. It does not own portfolio state, choose allocations, or claim predictiveness.

**Tech Stack:** Python 3.14, NumPy, existing market/portfolio domain types, pytest.

## Global Constraints

- Pair identity is canonical; orientation is explicit.
- Relationship functions consume already-admitted/aligned data and never fetch data themselves.
- Evidence is descriptive in this phase, not predictive.
- Anchor views are decomposition/context and cannot become hidden target-asset authority.
- No Copula, cointegration, z-score strategy, topology, or model registry is introduced.

## File Map

**Create:**
- `src/qap/relationship/__init__.py`
- `src/qap/relationship/observation.py` — generic immutable relationship-series metadata/result container plus model-facing orientation-behavior enum.
- `src/qap/relationship/ratio.py` — raw ratio, reciprocal orientation, log ratio.
- `src/qap/relationship/normalized.py` — normalized-to-one/hundred visual series data.
- `src/qap/relationship/anchor.py` — `X/A`, `Y/A`, and decomposition checks.
- `tests/unit/relationship/test_ratio.py`
- `tests/unit/relationship/test_normalized.py`
- `tests/unit/relationship/test_anchor.py`
- `tests/scenarios/test_pair_relationship_fixture.py`

## Section 04.1 — Relationship Observation Contract

**Interfaces:**
- Consumes: canonical `PairId`, requested `PairOrientation`, as-of timestamps, source data fingerprints.
- Produces: immutable `RelationshipSeries` with values plus provenance.

**Behavior:**
- Record canonical pair identity and requested base/quote orientation separately.
- Record interval/window start/end/as-of timestamps.
- Record source fingerprints for both legs.
- Record evidence kind such as `ratio` or `log_ratio`; do not add a plugin registry.
- Define model-facing `OrientationBehavior = exact_transform | directional_transform | refit_required`. Raw/log-ratio evidence is `exact_transform`; later models must declare their own behavior rather than inheriting this property accidentally.
- Invalid/insufficient data is represented by an explicit exception/result status, never NaN-filled output.

**Steps:**
- [ ] Write construction/metadata tests, including the three allowed orientation-behavior values.
- [ ] Implement focused dataclass/container suitable for later API serialization.

## Section 04.2 — Raw and Log Ratio

**Interfaces:**
- Consumes: two exactly aligned positive **completed-bar close-price** arrays in requested orientation.
- Produces: `X/Y` and `log(X/Y)` series.

**Behavior:**
- All inputs must be finite and strictly positive.
- `Y/X` is calculated from the same aligned observations and canonical pair identity.
- Reciprocal relation holds within declared float tolerance.
- Log inverse relation holds: `log(Y/X) = -log(X/Y)`.

**Steps:**
- [ ] Write tests with exact simple prices and randomized-but-seeded finite arrays.
- [ ] Implement vectorized ratio/log functions using NumPy.
- [ ] Keep tolerance local and explicit; do not round displayed values in the financial computation layer.

**Verification:**

```bash
uv run pytest -q tests/unit/relationship/test_ratio.py
```

## Section 04.3 — Normalized Price Paths

**Interfaces:**
- Consumes: aligned positive X and Y series.
- Produces: visual comparison series normalized to first admitted value.

**Behavior:**
- First point equals exactly `1.0` in computation form.
- Normalization is labeled visual/descriptive evidence and is not fed directly into execution.
- Reject empty series and zero/non-finite first values.

**Steps:**
- [ ] Add tests showing normalized path explains whether relative change came from X, Y, or both.
- [ ] Implement pure normalization function.

## Section 04.4 — Anchor Decomposition

**Interfaces:**
- Consumes: exactly aligned price series for X, Y, and anchor A in one common quote/reference coordinate.
- Produces: `X/Y`, `X/A`, `Y/A` synchronized series plus decomposition error diagnostic.

**Behavior:**

For synchronized positive prices:

```text
X/Y = (X/A) / (Y/A)
log(X/Y) = log(X/A) - log(Y/A)
```

- Anchor must be distinct from X and Y for the three-series lens; if anchor equals one leg, return the mathematically reduced view explicitly rather than pretending three independent series exist.
- Decomposition tolerance failure is a data/alignment error, not a model signal.

**Steps:**
- [ ] Write a hand-calculated three-asset fixture.
- [ ] Test ratio and log identities across the whole aligned window.
- [ ] Implement `build_anchor_lens(...)` returning synchronized descriptive series.

**Verification:**

```bash
uv run pytest -q tests/unit/relationship/test_anchor.py
```

## Section 04.5 — End-to-End Pair Fixture

**Scenario:**
- Load committed BTC/USDT and ETH/USDT fixtures from Phase 02.
- Align them.
- Build ETH/BTC and BTC/ETH views.
- Build normalized ETH and BTC overlays.
- Use USDT as the common coordinate only for the decomposition math; do not treat USDT as the economic objective.

**Steps:**
- [ ] Add scenario assertions for canonical identity, reciprocal orientation, log sign, and source fingerprints.
- [ ] Confirm no evaluation/portfolio state changes occur.

**Verification:**

```bash
uv run pytest -q tests/scenarios/test_pair_relationship_fixture.py
```

## Phase Verification

```bash
uv run pytest -q tests/unit/relationship tests/scenarios/test_pair_relationship_fixture.py
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests
```

## Phase Exit Criteria

- [ ] Raw/log ratios are deterministic and orientation-correct.
- [ ] Canonical relationship identity is separate from model orientation behavior; later directional/asymmetric models are not forced into reciprocal sign/inversion semantics.
- [ ] Normalized paths are available as descriptive evidence.
- [ ] Anchor decomposition identities are executable and verified.
- [ ] Provenance/data fingerprints flow into relationship output.
- [ ] No predictive model or portfolio mutation exists in `qap.relationship`.

## Stop Conditions

Do not add a model framework, pair-ranking system, network graph, thresholds, predictive labels, or automatic anchor selection. Those are separate hypotheses and must not contaminate the transparent relationship baseline.

## Targeted Quant Review Addendum — Reciprocal Fit vs Evidence Semantics

One `orientation_behavior` field is too coarse for fitted statistical models. QAP distinguishes reciprocity of the **fitted joint object** from reciprocity of the **oriented evidence derived from it**.

```text
fit_reciprocity:
  exact_transform | refit_required | model_specific

evidence_reciprocity:
  exact_transform | directional_transform | model_specific
```

Examples later phases must preserve:
- raw/log ratio: exact representation/oriented transform;
- Pearson/Spearman/Kendall dependence: symmetric under coordinate exchange;
- conventional Engle-Granger residual construction: refit required when regression normalization reverses;
- ordinary bivariate Gaussian or Student-t joint Copula: one exchangeable fitted joint model, while conditional/h-function evidence is directional;
- rotated or explicitly asymmetric Copulas: model/rotation-specific semantics must be declared.

Trial accounting follows the research operation: exact reversals are not new trials; deterministic directional views from one joint fit are not independent discoveries; separately refitted reciprocal orientations are correlated variants in the same `research_family_id`; choosing the better orientation after seeing performance counts as selection.
