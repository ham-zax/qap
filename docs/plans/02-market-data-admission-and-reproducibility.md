# Phase 02 — Market-Data Admission and Reproducibility Implementation Plan

**Goal:** Admit historical spot-market observations through an explicit, reproducible, point-in-time-safe data contract before any strategy logic consumes them.

**Architecture:** `qap.market` owns immutable bar semantics, validation, alignment, local dataset loading, and fingerprints. The first implementation consumes committed CSV fixtures and local Parquet datasets; no exchange SDK or network dependency is introduced yet.

**Tech Stack:** Python 3.14, NumPy, Pandas, PyArrow/Parquet, `hashlib`, pytest.

## Global Constraints

- Canonical timezone is UTC.
- Bar timestamp means candle-open time.
- Historical decision inputs must contain completed bars only.
- Instrument base/quote orientation is explicit.
- Inverse and synthetic markets are never silently substituted.
- Runtime market data is not committed to Git; tiny deterministic fixtures are.
- Fingerprints cover the semantic data used by a run, not merely a filename.

## File Map

**Modify:**
- `pyproject.toml` — add NumPy, Pandas, PyArrow runtime dependencies.

**Create:**
- `src/qap/market/__init__.py`
- `src/qap/market/bars.py` — bar and instrument observation types.
- `src/qap/market/validation.py` — duplicate/gap/order/price validation.
- `src/qap/market/alignment.py` — exact timestamp intersection/alignment.
- `src/qap/market/storage.py` — CSV fixture and Parquet local loading/writing.
- `src/qap/market/fingerprint.py` — canonical semantic fingerprint.
- `tests/unit/market/test_bars.py`
- `tests/unit/market/test_validation.py`
- `tests/unit/market/test_alignment.py`
- `tests/unit/market/test_fingerprint.py`
- `tests/scenarios/test_market_dataset_roundtrip.py`
- `tests/fixtures/market/BTCUSDT_1h.csv`
- `tests/fixtures/market/ETHUSDT_1h.csv`

## Section 02.1 — Market Instrument and Bar Contract

**Interfaces:**
- Consumes: `AssetId`, `PairOrientation`.
- Produces: `MarketInstrument`, `MarketBar`, ordered bar series.

**Behavior:**
- `MarketInstrument` declares venue plus explicit base/quote assets.
- `MarketBar` stores interval, UTC candle-open timestamp, OHLC prices as finite positive floats, and non-negative volume when present.
- Reject naive datetimes; timestamps must be timezone-aware UTC.
- Reject bars whose high/low relationships contradict OHLC values.

**Steps:**
- [ ] Write tests for valid bars and malformed timestamps/OHLC values.
- [ ] Implement focused immutable types.
- [ ] Keep exchange-specific symbol strings outside the asset/pair identity layer.

**Verification:**

```bash
uv run pytest -q tests/unit/market/test_bars.py
```

## Section 02.2 — Series Validation

**Interfaces:**
- Consumes: ordered bars for one instrument/interval.
- Produces: validated immutable series or explicit validation error.

**Behavior:**
- Timestamps strictly increase.
- Duplicate timestamp is an error.
- Interval step must match declared cadence for admitted executable datasets. Internal gaps are rejected; any future exploratory display policy for sparse data belongs at the presentation boundary and does not weaken this contract.
- Non-finite prices/volume are errors.
- Validation reports exact offending timestamps/reason.

**Steps:**
- [ ] Write duplicate, out-of-order, gap, and non-finite tests.
- [ ] Implement `validate_bar_series` without silent sorting or deduplication.
- [ ] Sorting belongs to import preparation, not validation; executable inputs fail if order is wrong.

**Verification:**

```bash
uv run pytest -q tests/unit/market/test_validation.py
```

## Section 02.3 — Exact Alignment

**Interfaces:**
- Consumes: two or more validated series.
- Produces: timestamp-aligned close/open arrays with one common index.

**Behavior:**
- Alignment uses exact timestamp intersection.
- The function reports dropped-leading/trailing timestamps and rejects internal gaps for executable mode.
- No forward-fill/backfill of market prices is allowed.
- Returned arrays preserve orientation/instrument metadata.

**Steps:**
- [ ] Write tests with unequal leading/trailing windows and an internal missing bar.
- [ ] Implement alignment with explicit metadata about source lengths and resulting range.

**Verification:**

```bash
uv run pytest -q tests/unit/market/test_alignment.py
```

## Section 02.4 — Local Storage Contract

**Interfaces:**
- Consumes: committed CSV fixtures or validated in-memory series.
- Produces: deterministic local Parquet datasets with manifest metadata.

**Behavior:**
- CSV fixture schema is fixed and documented in loader code/tests.
- Parquet file contains instrument metadata, interval, and UTC timestamps.
- Roundtrip preserves semantic timestamps and numeric values within exact serialized representation/tolerance established by fixture tests.
- Runtime Parquet lives below gitignored `data/market/`; test roundtrips use temporary directories.

**Steps:**
- [ ] Add small hand-auditable BTC/USDT and ETH/USDT hourly fixtures covering at least 12 consecutive bars.
- [ ] Implement CSV load -> validation -> Parquet write -> Parquet read.
- [ ] Do not add download/network behavior.

**Verification:**

```bash
uv run pytest -q tests/scenarios/test_market_dataset_roundtrip.py
```

## Section 02.5 — Semantic Data Fingerprint

**Interfaces:**
- Consumes: validated dataset metadata and ordered values.
- Produces: stable SHA-256 fingerprint string.

**Behavior:**
- Fingerprint includes venue, base/quote, interval, timestamps, OHLCV values, and schema version in canonical order.
- Filename and filesystem path do not affect the fingerprint.
- Any authoritative value/timestamp/orientation change changes the fingerprint.
- Rewriting equivalent data to a different path yields the same fingerprint.

**Steps:**
- [ ] Write tests for path invariance and value/orientation sensitivity.
- [ ] Implement canonical byte serialization local to `fingerprint.py`; do not hash Python `repr` output.

**Verification:**

```bash
uv run pytest -q tests/unit/market/test_fingerprint.py
```

## Section 02.6 — Point-in-Time Window API

**Interfaces:**
- Consumes: validated series and an `as_of` completed-bar timestamp.
- Produces: an immutable slice containing no later bar.

**Behavior:**
- Each bar has `close_time = candle_open_time + interval`.
- `history_through(decision_time)` includes exactly bars whose `close_time <= decision_time`.
- For contiguous hourly bars, a decision at 11:00 may use the bar opened at 10:00 and may not use any OHLC value from the bar opened at 11:00.
- The caller cannot treat a bar-open timestamp as evidence that the same bar has already completed.
- A later decision/replay layer receives a slice/facade that cannot expose future rows accidentally.

**Steps:**
- [ ] Add tests proving a timestamp after `as_of` is inaccessible through the returned history.
- [ ] Implement the smallest slice API needed by Phase 04 and Phase 06.

## Phase Verification

```bash
uv sync
uv run pytest -q tests/unit/market tests/scenarios/test_market_dataset_roundtrip.py
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests
```

## Phase Exit Criteria

- [ ] Historical bars have explicit UTC/orientation/interval semantics.
- [ ] Duplicate, gap, order, and malformed-price failures are visible.
- [ ] Exact alignment does not impute missing prices.
- [ ] Local Parquet roundtrip is reproducible.
- [ ] Semantic fingerprint is path-independent and data-sensitive.
- [ ] Point-in-time slices cannot expose future bars through their public API.
- [ ] No exchange SDK/network client exists yet.

## Stop Conditions

Do not add CCXT, exchange authentication, websocket streaming, database storage, auto-gap repair, or implicit symbol inversion in this phase. Any of those requires a later demonstrated use case and its own plan.
