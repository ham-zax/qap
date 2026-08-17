# Phase 02 — Market-Data Admission and Reproducibility Implementation Plan

**Goal:** Admit historical spot-market observations through an explicit, reproducible, point-in-time-safe data contract before any strategy logic consumes them.

**Architecture:** `qap.market` owns immutable bar semantics, venue-instrument mappings, validation, alignment, one bounded unauthenticated public spot-data adapter, local dataset storage, and fingerprints. Network acquisition is an adapter at the edge; admitted datasets become immutable local artifacts before any strategy/research code consumes them. No exchange SDK, authentication, or trading capability is introduced.

**Tech Stack:** Python 3.14, NumPy, Pandas, PyArrow/Parquet, HTTPX, `hashlib`, pytest.

## Global Constraints

- Canonical timezone is UTC.
- Bar timestamp means candle-open time.
- Historical decision inputs must contain completed bars only.
- Instrument base/quote orientation is explicit.
- Inverse and synthetic markets are never silently substituted.
- Runtime market data is not committed to Git; tiny deterministic fixtures are.
- Fingerprints cover the semantic data used by a run, not merely a filename.
- Any real dataset inspected before the experiment protocol exists is development/exploratory evidence and cannot later be relabeled as untouched final OOS.
- The initial research universe mode is `declared_fixed_basket`; historical discovery/investable-universe claims are blocked until point-in-time listing/eligibility sources exist.

## File Map

**Modify:**
- `pyproject.toml` — add NumPy, Pandas, PyArrow, and HTTPX runtime dependencies.

**Create:**
- `src/qap/market/__init__.py`
- `src/qap/market/bars.py` — bar observation types and source/native timestamp fields.
- `src/qap/market/instruments.py` — `VenueInstrument` mapping from stable `AssetId` values to one venue symbol/orientation plus observed validity metadata.
- `src/qap/market/prices.py` — immutable `PriceSnapshot` (timestamp, numeraire, explicit Decimal asset prices) shared by valuation and rebalance planning.
- `src/qap/market/validation.py` — duplicate/gap/order/price validation.
- `src/qap/market/alignment.py` — exact timestamp intersection/alignment.
- `src/qap/market/storage.py` — CSV fixture and Parquet local loading/writing.
- `src/qap/market/adapters/binance_public.py` — one unauthenticated Binance Spot public REST adapter for klines/current instrument metadata; no SDK/auth/trade endpoints.
- `src/qap/market/fingerprint.py` — canonical semantic fingerprint.
- `tests/unit/market/test_bars.py`
- `tests/unit/market/test_validation.py`
- `tests/unit/market/test_alignment.py`
- `tests/unit/market/test_fingerprint.py`
- `tests/unit/market/test_instruments.py`
- `tests/unit/market/test_prices.py`
- `tests/integration/market/test_binance_public_adapter.py` — recorded-response contract test by default; explicitly marked live-network smoke is optional/manual.
- `tests/scenarios/test_market_dataset_roundtrip.py`
- `tests/fixtures/market/BTCUSDT_1h.csv`
- `tests/fixtures/market/ETHUSDT_1h.csv`

## Section 02.1 — Market Instrument and Bar Contract

**Interfaces:**
- Consumes: `AssetId`, `PairOrientation`.
- Produces: `MarketInstrument`, `MarketBar`, ordered bar series.

**Behavior:**
- `VenueInstrument` declares venue, source `venue_symbol`, explicit stable base/quote `AssetId` values, and optional observed `valid_from`/`valid_to` metadata.
- Unknown historical listing validity is represented as unknown, not guessed from today's exchange metadata. Such data remains usable for a declared-fixed-basket retrospective but not for a point-in-time discovery claim.
- `MarketBar` stores interval, UTC candle-open timestamp, optional raw/source close timestamp, OHLC prices as finite positive floats, and non-negative volume when present.
- Reject naive datetimes; timestamps must be timezone-aware UTC.
- Reject bars whose high/low relationships contradict OHLC values.

**Steps:**
- [ ] Write tests for valid bars, source timestamp preservation, malformed timestamps/OHLC values, and venue-symbol mapping without mutating `AssetId` identity.
- [ ] Implement focused immutable types.
- [ ] Keep exchange-specific symbol strings outside the asset/pair identity layer.

**Verification:**

```bash
uv run pytest -q tests/unit/market/test_bars.py
```

## Section 02.2 — Explicit Price Snapshot

**Interfaces:**
- Consumes: stable `AssetId` values, one declared numeraire, UTC timestamp, explicit asset->numeraire prices.
- Produces: immutable `PriceSnapshot` used later by evaluation and rebalance planning.

**Behavior:**
- Prices are positive `Decimal` values; the numeraire asset has price exactly `1` in its own units.
- Missing asset prices are not synthesized and no executable route is inferred.
- Converting a bar float into a snapshot uses an explicit stable decimal serialization at the boundary; the snapshot never stores binary-float accounting truth.
- `qap.market` owns observed prices; valuation mathematics remains in `qap.evaluation`.

**Steps:**
- [ ] Write tests for complete snapshot, missing/non-positive price, numeraire self-price, and timezone-aware timestamp.
- [ ] Implement the small immutable price container without valuation/P&L methods.

## Section 02.3 — Series Validation

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

## Section 02.4 — Exact Alignment

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

## Section 02.5 — One Bounded Public Spot Adapter

**Interfaces:**
- Consumes: explicit venue symbol, interval, start/end window.
- Produces: raw public response mapped to `VenueInstrument` + `MarketBar` records, then passed through normal validation/storage.

**Behavior:**
- Use only Binance Spot endpoints documented with public/`NONE` security at implementation time; prefer the market-data-only host where the official docs support it.
- Fetch klines and only the minimum current instrument metadata needed for orientation/identity. Never create API keys, sign requests, query balances, or call order/margin/futures/options endpoints.
- Preserve source open/close timestamps exactly and derive `bar_end_exclusive` internally from interval rather than pretending source close timestamps use that same convention.
- Network acquisition never feeds strategy code directly: validated results are written to the normal immutable local dataset contract and fingerprinted before use.
- HTTP/rate-limit/source failures are explicit. No alternate venue or synthetic symbol fallback occurs.
- Any downloaded history inspected in this phase is `development` evidence by default.

**Steps:**
- [ ] At implementation time, verify the current official Binance Spot public market-data contract and record the endpoint/field assumptions in adapter tests/comments.
- [ ] Implement the adapter with HTTPX; do not add CCXT or an exchange SDK.
- [ ] Build deterministic recorded-response fixtures for kline/instrument parsing.
- [ ] Add an opt-in network smoke marker that is skipped by default and never required for ordinary unit verification.

**Verification:**

```bash
uv run pytest -q tests/integration/market/test_binance_public_adapter.py
```

## Section 02.6 — Local Storage Contract

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

## Section 02.7 — Semantic Data Fingerprint

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

## Section 02.8 — Point-in-Time Window API

**Interfaces:**
- Consumes: validated series and an `as_of` completed-bar timestamp.
- Produces: an immutable slice containing no later bar.

**Behavior:**
- Each bar has internal `bar_end_exclusive = candle_open_time + interval`; raw venue close time, when supplied, is preserved separately.
- `history_through(decision_time)` includes exactly bars whose `bar_end_exclusive <= decision_time`.
- For contiguous hourly bars, a decision at 11:00 may use the bar opened at 10:00 and may not use any OHLC value from the bar opened at 11:00.
- The caller cannot treat a bar-open timestamp as evidence that the same bar has already completed.
- A later decision/replay layer receives a slice/facade that cannot expose future rows accidentally.

**Steps:**
- [ ] Add tests proving a timestamp after `as_of` is inaccessible through the returned history.
- [ ] Implement the smallest slice API needed by Phase 04 and Phase 06.

## Phase Verification

```bash
uv sync
uv run pytest -q tests/unit/market tests/integration/market/test_binance_public_adapter.py tests/scenarios/test_market_dataset_roundtrip.py
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests
```

## Phase Exit Criteria

- [ ] Historical bars have explicit UTC/orientation/interval semantics and preserve source-native close timestamps separately from internal completion boundaries.
- [ ] Stable asset identity is separated from venue symbol/instrument mapping.
- [ ] A small shared `PriceSnapshot` provides explicit Decimal mark prices without making portfolio depend on evaluation.
- [ ] One public unauthenticated Spot adapter can acquire and admit data without creating any trading/auth surface.
- [ ] Duplicate, gap, order, and malformed-price failures are visible.
- [ ] Exact alignment does not impute missing prices.
- [ ] Local Parquet roundtrip is reproducible.
- [ ] Semantic fingerprint is path-independent and data-sensitive.
- [ ] Point-in-time slices cannot expose future bars through their public API.
- [ ] No exchange SDK, authentication, private-account endpoint, or trading endpoint exists.

## Stop Conditions

Do not add CCXT/exchange SDKs, exchange authentication, private account access, trading/order endpoints, websocket streaming, database storage, auto-gap repair, dynamic-universe discovery, or implicit symbol inversion in this phase. A current venue listing record may not be used to fabricate historical point-in-time eligibility.

## OSS Reuse Addendum — Public Data and Columnar Storage

Reuse mature infrastructure selectively:
- `httpx` is sufficient for the intentionally tiny public-market adapter unless a bounded spike shows official `binance-sdk-spot` materially reduces code without leaking private/trading semantics into QAP contracts.
- CCXT is mature and MIT-licensed, but its enormous exchange/instrument/trading surface is not the default Phase-02 dependency. Treat it as reference or a later multi-venue adapter candidate.
- Use PyArrow for Parquet/Arrow serialization rather than implementing columnar storage logic. Do not add Polars alongside pandas/NumPy merely for fashion; another dataframe engine needs measured justification.
- For bulk Binance history, prefer the official public-data archives and published checksums where they fit the requested window; feed them through the same QAP admission/fingerprint path as API data.
- DuckDB/Polars remain deferred until broad scanning actually begins; they do not become Phase-02 storage authorities.
- Keep Binance Spot public endpoint/filter semantics behind `qap.market.adapters`; third-party response objects never cross into domain contracts.
