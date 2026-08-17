# Phase 01 — Domain Kernel and Inventory Semantics Implementation Plan

**Goal:** Implement the smallest authoritative domain kernel for assets, canonical pair identity, portfolio holdings, target allocations, and immutable inventory transitions.

**Architecture:** `qap.portfolio` owns economic state. Domain objects are plain typed dataclasses/value objects using `Decimal` for quantities and weights. Pair orientation is explicit and separate from canonical relationship identity. No market data, policy model, execution venue, or API dependency enters this phase.

**Tech Stack:** Python 3.14, standard-library dataclasses/enums/Decimal, pytest.

## Global Constraints

- Portfolio inventory is the only authoritative mutable economic state; implementation methods should return new states rather than expose mutable dictionaries.
- No negative quantity is valid.
- No float enters authoritative quantity/weight arithmetic.
- `X/Y` and `Y/X` are orientations of one canonical pair identity.
- Do not introduce generic base classes, registries, repositories, services, or dependency-injection containers.

## File Map

**Create:**

- `src/qap/portfolio/__init__.py` — explicit public exports.
- `src/qap/portfolio/assets.py` — `AssetId` value object.
- `src/qap/portfolio/pairs.py` — canonical relationship identity and requested orientation.
- `src/qap/portfolio/state.py` — `PortfolioState` holdings and safe transitions.
- `src/qap/portfolio/allocation.py` — `AllocationTarget` and target validation.
- `tests/unit/portfolio/test_assets.py`
- `tests/unit/portfolio/test_pairs.py`
- `tests/unit/portfolio/test_state.py`
- `tests/unit/portfolio/test_allocation.py`

## Section 01.1 — Asset Identity

**Interfaces:**
- Produces: `AssetId` consumed by every later financial domain.

**Behavior:**
- Trim surrounding whitespace.
- Normalize symbol to uppercase.
- Reject empty symbols and symbols containing `/` because slash belongs to market orientation, not asset identity.
- Preserve no venue-specific metadata in `AssetId`.

**Steps:**
- [ ] Write focused tests for normalization and invalid symbols.
- [ ] Verify tests fail before implementation.
- [ ] Implement frozen/orderable `AssetId` with a single `symbol: str` field and constructor validation.
- [ ] Re-run focused tests.

**Verification:**

```bash
uv run pytest -q tests/unit/portfolio/test_assets.py
```

**Acceptance criteria:**
- `AssetId(" btc ") == AssetId("BTC")`.
- Empty or slash-containing asset symbols fail explicitly.

## Section 01.2 — Canonical Pair and Orientation

**Interfaces:**
- Consumes: `AssetId`.
- Produces: `PairId` canonical identity and `PairOrientation` presentation/execution view.

**Behavior:**
- A pair requires two distinct assets.
- Canonical identity sorts the two `AssetId` values deterministically.
- Orientation stores explicit base/quote order and resolves to the same canonical pair regardless of direction.
- Numeric convention is explicit: `BASE/QUOTE` means QUOTE units per one BASE unit.
- Inversion creates the reciprocal orientation without creating a new pair identity.

**Steps:**
- [ ] Write tests showing `BTC/ETH` and `ETH/BTC` share one `PairId`.
- [ ] Write tests rejecting same-asset pairs.
- [ ] Implement focused immutable value objects; do not add market symbol resolution yet.

**Verification:**

```bash
uv run pytest -q tests/unit/portfolio/test_pairs.py
```

**Acceptance criteria:**
- Orientation identity and inversion behavior are deterministic.
- No execution-market assumptions exist in the pair domain object.

## Section 01.3 — Portfolio State

**Interfaces:**
- Consumes: `AssetId`, `Decimal` quantities.
- Produces: immutable `PortfolioState` and explicit quantity transitions.

**Behavior:**
- Holdings are represented as an immutable mapping from admitted asset to non-negative `Decimal` quantity.
- Missing asset reads as zero through an explicit accessor, not implicit dictionary mutation.
- Applying a quantity delta returns a new state.
- Any transition that would make a balance negative fails before state creation.
- Zero balances may remain represented or be normalized away consistently; choose normalization-away to keep states compact and deterministic.

**Steps:**
- [ ] Write hand-auditable tests for deposits, reductions, zero-removal, and rejected overdraft.
- [ ] Implement `PortfolioState.from_holdings(...)`, `quantity(asset)`, and `apply_deltas(mapping)`.
- [ ] Prevent callers from obtaining a mutable holdings object.

**Verification:**

```bash
uv run pytest -q tests/unit/portfolio/test_state.py
```

**Acceptance criteria:**
- Reapplying the same input to the same state produces an equal output state.
- Negative quantity cannot exist even transiently in returned state.

## Section 01.4 — Allocation Target

**Interfaces:**
- Consumes: admitted assets and `Decimal` weights.
- Produces: validated long-only target allocation for Phase 05.

**Behavior:**
- Weights are non-negative `Decimal` values.
- Target contains at least one asset.
- Sum must equal `Decimal("1")` within a declared constant tolerance of `1e-12`.
- A target cannot contain an asset outside the declared basket passed to validation.
- Target is declarative; it contains no order/trade instructions.

**Steps:**
- [ ] Write tests for exact and tolerance-valid sums, negative weights, out-of-basket assets, and totals outside tolerance.
- [ ] Implement frozen `AllocationTarget` with `for_basket(...)` validation.
- [ ] Keep tolerance defined beside the type, not hidden in configuration.

**Verification:**

```bash
uv run pytest -q tests/unit/portfolio/test_allocation.py
```

**Acceptance criteria:**
- Valid long-only allocations are accepted.
- Invalid target sums/weights/basket membership fail with explicit errors.

## Section 01.5 — Domain Scenario Verification

**Steps:**
- [ ] Add one scenario-style test that starts with two assets, applies deterministic quantity deltas, and validates both resulting holdings and a target allocation.
- [ ] Run all Python verification.

**Verification:**

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests
```

## Phase Exit Criteria

- [ ] Asset, pair, portfolio, and allocation semantics are explicit and deterministic.
- [ ] Authoritative quantities/weights use `Decimal` only.
- [ ] Pair orientation and canonical relationship identity are separated.
- [ ] No negative holdings are representable through public APIs.
- [ ] No speculative model/execution/API abstractions were introduced.

## Stop Conditions

Return to design review if implementing the domain requires an exchange SDK, database, mutable global registry, environment-variable business state, or trade lifecycle objects such as OPEN/CLOSED positions. Those indicate the architecture is drifting away from inventory ownership.
