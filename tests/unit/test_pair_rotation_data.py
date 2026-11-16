"""Offline coverage for PairRotationData without network or admission."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from qap.market import BarInterval, MarketBar, validate_bar_series
from qap.market.instruments import VenueInstrument
from qap.portfolio import AssetId
from qap.product_market_data import ProductMarketData
from qap.product_market_data_binance import (
    BinanceHistoricalAcquirer,
    BinanceHistoricalAcquisitionError,
)
from qap.product_market_data_generation import resolve_immutable_generation
from qap.product_market_data_models import (
    MarketDataGenerationInput,
    MarketDataUpstreamSource,
)
from qap.product_market_data_prepare import (
    ProductMarketDataPreparationError,
    product_dataset_id,
)
from qap.product_pair_rotation_data import PairRotationData
from qap.product_universe import (
    ProductResearchScope,
    ProductUniverse,
    ResolvedProductInstrument,
)

_BASE = BarInterval("15m")
_STALE = datetime(2024, 1, 1, tzinfo=UTC)
_NOW = datetime(2025, 3, 10, 14, 50, tzinfo=UTC)
_CUTOFF = datetime(2025, 3, 10, 14, 45, tzinfo=UTC)


class FakeBinance(BinanceHistoricalAcquirer):
    """Deterministic offline 15m history without network."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.calls: list[tuple[str, datetime, datetime]] = []
        self.should_fail = False

    def close(self) -> None:
        return None

    def acquire_generation_input(
        self,
        *,
        scope: ProductResearchScope,
        instrument: ResolvedProductInstrument,
        dataset_id: str,
        interval: BarInterval,
        start: datetime,
        end_exclusive: datetime,
    ) -> MarketDataGenerationInput:
        self.calls.append((dataset_id, start, end_exclusive))
        if self.should_fail:
            raise BinanceHistoricalAcquisitionError("fake binance outage")
        if interval != _BASE:
            raise AssertionError("pair worker must request 15m only")
        bars: list[MarketBar] = []
        cursor = start
        index = 0
        while cursor < end_exclusive:
            open_price = 100.0 + index * 0.1
            bars.append(
                MarketBar(
                    instrument=instrument.instrument,
                    interval=interval,
                    candle_open_time=cursor,
                    open=open_price,
                    high=open_price + 1.0,
                    low=open_price - 1.0,
                    close=open_price + 0.05,
                    volume=10.0,
                    source_close_time=None,
                )
            )
            cursor += timedelta(minutes=15)
            index += 1
        series = validate_bar_series(bars)
        fingerprint = hashlib.sha256(
            f"{dataset_id}{start.isoformat()}{end_exclusive.isoformat()}".encode()
        ).hexdigest()
        upstream = MarketDataUpstreamSource(
            provider="binance",
            source_family="test-fake-rest-klines",
            source_id=f"fake:{dataset_id}:{start.isoformat()}:{end_exclusive.isoformat()}",
            retrieved_at=datetime.now(UTC),
            source_fingerprint=fingerprint,
        )
        return MarketDataGenerationInput(
            dataset_id=dataset_id,
            resolved_instrument=instrument,
            series=series,
            acquisition_implementation="qap.test.fake-binance.v1",
            upstream_sources=(upstream,),
        )


def _instrument(base: str, symbol: str) -> ResolvedProductInstrument:
    return ResolvedProductInstrument(
        instrument=VenueInstrument(
            venue="binance",
            venue_symbol=symbol,
            base=AssetId(base),
            quote=AssetId("USDT"),
        ),
        base_asset_identity_version=f"{base.lower()}-v1",
        quote_asset_identity_version="usdt-v1",
        directory_observed_at=_STALE,
        source_id=f"binance:{symbol}",
        source_fingerprint=hashlib.sha256(f"src:{symbol}".encode()).hexdigest(),
    )


def _scope(
    first: ResolvedProductInstrument, second: ResolvedProductInstrument
) -> ProductResearchScope:
    return ProductResearchScope(
        directory_id=hashlib.sha256(b"pair-dir").hexdigest(),
        directory_observed_at=_STALE,
        approved_assets=(),
        instruments=(first, second),
    )


def _owners(tmp_path: Path) -> tuple[ProductUniverse, ProductMarketData]:
    workspace = tmp_path / "ws"
    data_root = tmp_path / "md"
    return ProductUniverse(workspace), ProductMarketData(workspace, data_root)


def _start_for(cutoff: datetime, lookback_days: int) -> datetime:
    anchor = cutoff - timedelta(days=lookback_days)
    return datetime(anchor.year, anchor.month, anchor.day, tzinfo=UTC)


def test_first_download_publishes_15m_and_derived(tmp_path: Path) -> None:
    universe, market_data = _owners(tmp_path)
    worker = PairRotationData(universe, market_data)
    scope = _scope(_instrument("BTC", "BTCUSDT"), _instrument("ETH", "ETHUSDT"))
    fake = FakeBinance()
    events: list[tuple[str, int, int]] = []

    def record(label: str, done: int, total: int) -> None:
        events.append((label, done, total))

    projection = worker.prepare(
        scope, now=_NOW, lookback_days=5, progress=record, binance=fake
    )

    assert len(fake.calls) == 2
    assert len(projection.generations) == 8
    assert all(item.provenance_status == "complete" for item in projection.generations)
    assert projection.maintenance.status == "idle"  # pyright: ignore[reportUnknownMemberType]
    assert events[0] == ("prepare", 0, 8)
    assert events[-1][1] == 8 and events[-1][2] == 8
    assert all(done <= total == 8 for _, done, total in events)
    start = _start_for(_CUTOFF, 5)
    for instrument in scope.instruments:
        dataset_15m = product_dataset_id(instrument, _BASE)
        current = next(
            item for item in projection.generations if item.dataset_id == dataset_15m
        )
        assert current.coverage_start == start
        assert current.coverage_end_exclusive == _CUTOFF


def test_no_admission_required(tmp_path: Path) -> None:
    universe, market_data = _owners(tmp_path)
    worker = PairRotationData(universe, market_data)
    scope = _scope(_instrument("BTC", "BTCUSDT"), _instrument("ETH", "ETHUSDT"))
    assert scope.approved_assets == ()
    projection = worker.prepare(scope, now=_NOW, lookback_days=5, binance=FakeBinance())
    assert len(projection.generations) == 8


def test_top_up_beyond_stale_directory(tmp_path: Path) -> None:
    universe, market_data = _owners(tmp_path)
    worker = PairRotationData(universe, market_data)
    scope = _scope(_instrument("BTC", "BTCUSDT"), _instrument("ETH", "ETHUSDT"))
    fake = FakeBinance()
    first = worker.prepare(scope, now=_NOW, lookback_days=5, binance=fake)
    before = {item.dataset_id: item.semantic_fingerprint for item in first.generations}
    later = _NOW + timedelta(days=2)
    later_cutoff = datetime(2025, 3, 12, 14, 45, tzinfo=UTC)
    fake.calls.clear()
    second = worker.prepare(scope, now=later, lookback_days=5, binance=fake)

    assert len(fake.calls) == 2
    for instrument in scope.instruments:
        dataset_15m = product_dataset_id(instrument, _BASE)
        current = next(
            item for item in second.generations if item.dataset_id == dataset_15m
        )
        assert current.coverage_end_exclusive == later_cutoff
        assert current.coverage_start is not None
        assert current.coverage_start <= _start_for(later_cutoff, 5)
        assert current.semantic_fingerprint != before[dataset_15m]


def test_repeat_same_window_makes_no_acquisition(tmp_path: Path) -> None:
    universe, market_data = _owners(tmp_path)
    worker = PairRotationData(universe, market_data)
    scope = _scope(_instrument("BTC", "BTCUSDT"), _instrument("ETH", "ETHUSDT"))
    fake = FakeBinance()
    worker.prepare(scope, now=_NOW, lookback_days=5, binance=fake)
    assert market_data.market_data_root is not None
    files_before = sorted(
        item.relative_to(market_data.market_data_root).as_posix()
        for item in market_data.market_data_root.rglob("*.parquet")
    )
    fake.calls.clear()
    second = worker.prepare(scope, now=_NOW, lookback_days=5, binance=fake)
    files_after = sorted(
        item.relative_to(market_data.market_data_root).as_posix()
        for item in market_data.market_data_root.rglob("*.parquet")
    )
    assert fake.calls == []
    assert files_after == files_before
    assert len(second.generations) == 8


def test_no_incomplete_resampled_buckets(tmp_path: Path) -> None:
    universe, market_data = _owners(tmp_path)
    worker = PairRotationData(universe, market_data)
    scope = _scope(_instrument("BTC", "BTCUSDT"), _instrument("ETH", "ETHUSDT"))
    worker.prepare(scope, now=_NOW, lookback_days=5, binance=FakeBinance())
    assert market_data.market_data_root is not None
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    expectations = {
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "1d": timedelta(days=1),
    }
    projection = market_data.projection()
    for instrument in scope.instruments:
        for label, duration in expectations.items():
            dataset = product_dataset_id(instrument, BarInterval(label))
            current = next(
                item for item in projection.generations if item.dataset_id == dataset
            )
            assert current.coverage_start is not None
            assert current.coverage_end_exclusive is not None
            assert (current.coverage_start - epoch) % duration == timedelta(0)
            assert (current.coverage_end_exclusive - epoch) % duration == timedelta(0)
            assert current.coverage_end_exclusive <= _CUTOFF
            provenance, series = resolve_immutable_generation(
                market_data.market_data_root,
                dataset_id=dataset,
                semantic_fingerprint=current.semantic_fingerprint,
            )
            assert series.interval == BarInterval(label)
            assert provenance.coverage_end_exclusive <= _CUTOFF
    one_hour = next(
        item
        for item in projection.generations
        if item.dataset_id.endswith(":1h") and "BTCUSDT" in item.dataset_id
    )
    assert one_hour.coverage_end_exclusive == datetime(2025, 3, 10, 14, 0, tzinfo=UTC)


def test_derived_lineage_links_exact_15m_parent(tmp_path: Path) -> None:
    universe, market_data = _owners(tmp_path)
    worker = PairRotationData(universe, market_data)
    scope = _scope(_instrument("BTC", "BTCUSDT"), _instrument("ETH", "ETHUSDT"))
    worker.prepare(scope, now=_NOW, lookback_days=5, binance=FakeBinance())
    assert market_data.market_data_root is not None
    projection = market_data.projection()
    for instrument in scope.instruments:
        parent_id = product_dataset_id(instrument, _BASE)
        parent = next(
            item for item in projection.generations if item.dataset_id == parent_id
        )
        for label in ("1h", "4h", "1d"):
            dataset = product_dataset_id(instrument, BarInterval(label))
            current = next(
                item for item in projection.generations if item.dataset_id == dataset
            )
            provenance, series = resolve_immutable_generation(
                market_data.market_data_root,
                dataset_id=dataset,
                semantic_fingerprint=current.semantic_fingerprint,
            )
            assert provenance.derivation is not None  # pyright: ignore[reportUnknownMemberType]
            assert len(provenance.derivation.parents) == 1  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
            parent_link = provenance.derivation.parents[0]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            assert parent_link.dataset_id == parent.dataset_id  # pyright: ignore[reportUnknownMemberType]
            assert parent_link.relative_path == parent.relative_path  # pyright: ignore[reportUnknownMemberType]
            assert parent_link.semantic_fingerprint == parent.semantic_fingerprint  # pyright: ignore[reportUnknownMemberType]
            assert provenance.upstream_sources  # pyright: ignore[reportUnknownMemberType]
            assert series.bars[0].candle_open_time == provenance.coverage_start


def test_resample_uses_first_open_max_high_min_low_last_close_sum_volume(
    tmp_path: Path,
) -> None:
    universe, market_data = _owners(tmp_path)
    worker = PairRotationData(universe, market_data)
    scope = _scope(_instrument("BTC", "BTCUSDT"), _instrument("ETH", "ETHUSDT"))
    worker.prepare(scope, now=_NOW, lookback_days=5, binance=FakeBinance())
    assert market_data.market_data_root is not None
    projection = market_data.projection()
    btc = scope.instruments[0]
    parent = next(
        item
        for item in projection.generations
        if item.dataset_id == product_dataset_id(btc, _BASE)
    )
    _, parent_series = resolve_immutable_generation(
        market_data.market_data_root,
        dataset_id=parent.dataset_id,
        semantic_fingerprint=parent.semantic_fingerprint,
    )
    first_hour = tuple(
        bar
        for bar in parent_series.bars
        if bar.candle_open_time
        < parent_series.bars[0].candle_open_time + timedelta(hours=1)
    )[:4]
    assert len(first_hour) == 4
    child = next(
        item
        for item in projection.generations
        if item.dataset_id == product_dataset_id(btc, BarInterval("1h"))
    )
    _, child_series = resolve_immutable_generation(
        market_data.market_data_root,
        dataset_id=child.dataset_id,
        semantic_fingerprint=child.semantic_fingerprint,
    )
    first = child_series.bars[0]
    assert first.open == first_hour[0].open
    assert first.high == max(bar.high for bar in first_hour)
    assert first.low == min(bar.low for bar in first_hour)
    assert first.close == first_hour[-1].close
    assert first.volume == 40.0


def test_failure_records_maintenance_and_typed_error(tmp_path: Path) -> None:
    universe, market_data = _owners(tmp_path)
    worker = PairRotationData(universe, market_data)
    scope = _scope(_instrument("BTC", "BTCUSDT"), _instrument("ETH", "ETHUSDT"))
    fake = FakeBinance()
    fake.should_fail = True
    try:
        worker.prepare(scope, now=_NOW, lookback_days=5, binance=fake)
    except ProductMarketDataPreparationError:
        pass
    else:
        raise AssertionError("expected typed preparation failure")
    assert market_data.projection().maintenance.status == "failed"  # pyright: ignore[reportUnknownMemberType]
    assert market_data.projection().maintenance.failure_reason is not None  # pyright: ignore[reportUnknownMemberType]


def test_invalid_scopes_rejected(tmp_path: Path) -> None:
    universe, market_data = _owners(tmp_path)
    worker = PairRotationData(universe, market_data)
    btc = _instrument("BTC", "BTCUSDT")
    eth = _instrument("ETH", "ETHUSDT")
    stale_dir = hashlib.sha256(b"pair-dir").hexdigest()
    lone = ProductResearchScope(
        directory_id=stale_dir,
        directory_observed_at=_STALE,
        approved_assets=(),
        instruments=(btc,),
    )
    duplicate = ProductResearchScope(
        directory_id=stale_dir,
        directory_observed_at=_STALE,
        approved_assets=(),
        instruments=(btc, btc),
    )
    gate_instrument = ResolvedProductInstrument(
        instrument=VenueInstrument(
            venue="gate",
            venue_symbol="BTC_USDT",
            base=AssetId("BTC"),
            quote=AssetId("USDT"),
        ),
        base_asset_identity_version="btc-v1",
        quote_asset_identity_version="usdt-v1",
        directory_observed_at=_STALE,
        source_id="gate:BTC_USDT",
        source_fingerprint=hashlib.sha256(b"gate-src").hexdigest(),
    )
    wrong_venue = ProductResearchScope(
        directory_id=stale_dir,
        directory_observed_at=_STALE,
        approved_assets=(),
        instruments=(btc, gate_instrument),
    )
    non_usdt = ResolvedProductInstrument(
        instrument=VenueInstrument(
            venue="binance",
            venue_symbol="BTCETH",
            base=AssetId("BTC"),
            quote=AssetId("ETH"),
        ),
        base_asset_identity_version="btc-v1",
        quote_asset_identity_version="eth-v1",
        directory_observed_at=_STALE,
        source_id="binance:BTCETH",
        source_fingerprint=hashlib.sha256(b"non-usdt").hexdigest(),
    )
    wrong_quote = ProductResearchScope(
        directory_id=stale_dir,
        directory_observed_at=_STALE,
        approved_assets=(),
        instruments=(btc, non_usdt),
    )
    triple = ProductResearchScope(
        directory_id=stale_dir,
        directory_observed_at=_STALE,
        approved_assets=(),
        instruments=(btc, eth, _instrument("SOL", "SOLUSDT")),
    )
    for bad in (lone, duplicate, wrong_venue, wrong_quote, triple):
        try:
            worker.prepare(bad, now=_NOW, lookback_days=5, binance=FakeBinance())
        except ProductMarketDataPreparationError:
            continue
        raise AssertionError("expected invalid scope to be rejected")


def test_client_startup_failure_releases_maintenance_and_allows_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    universe, owner = _owners(tmp_path)
    worker = PairRotationData(universe, owner)
    scope = _scope(_instrument("BTC", "BTCUSDT"), _instrument("ETH", "ETHUSDT"))

    def fail_client() -> None:
        raise RuntimeError("client startup failed")

    with monkeypatch.context() as patch:
        patch.setattr(
            "qap.product_pair_rotation_data.BinanceHistoricalAcquirer", fail_client
        )
        with pytest.raises(ProductMarketDataPreparationError, match="client startup"):
            worker.prepare(scope, now=_NOW, lookback_days=5)
    assert owner.projection().maintenance.status == "failed"
    worker.prepare(scope, now=_NOW, lookback_days=5, binance=FakeBinance())
    assert owner.projection().maintenance.status == "idle"


def test_partial_bar_top_up_skips_unchanged_derived_intervals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    universe, market_data = _owners(tmp_path)
    worker = PairRotationData(universe, market_data)
    scope = _scope(_instrument("BTC", "BTCUSDT"), _instrument("ETH", "ETHUSDT"))
    fake = FakeBinance()
    start_now = datetime(2025, 3, 10, 14, 5, tzinfo=UTC)
    first = worker.prepare(scope, now=start_now, lookback_days=5, binance=fake)
    assert market_data.market_data_root is not None
    derived_before = {
        item.dataset_id: item.semantic_fingerprint
        for item in first.generations
        if not item.dataset_id.endswith(":15m")
    }
    resamples = 0
    original_resample = __import__(
        "qap.product_pair_rotation_resample", fromlist=["resample_15m"]
    ).resample_15m

    def counting_resample(*args: object, **kwargs: object) -> object:
        nonlocal resamples
        resamples += 1
        return original_resample(*args, **kwargs)

    monkeypatch.setattr(
        "qap.product_pair_rotation_resample.resample_15m", counting_resample
    )
    fake.calls.clear()
    second = worker.prepare(
        scope,
        now=start_now + timedelta(minutes=15),
        lookback_days=5,
        binance=fake,
    )
    derived_after = {
        item.dataset_id: item.semantic_fingerprint
        for item in second.generations
        if not item.dataset_id.endswith(":15m")
    }
    assert len(fake.calls) == 2
    assert resamples == 0
    assert derived_after == derived_before


def test_delta_top_up_resamples_only_new_tail_buckets(
    tmp_path: Path,
) -> None:
    universe, market_data = _owners(tmp_path)
    worker = PairRotationData(universe, market_data)
    scope = _scope(_instrument("BTC", "BTCUSDT"), _instrument("ETH", "ETHUSDT"))
    fake = FakeBinance()
    first = worker.prepare(scope, now=_NOW, lookback_days=5, binance=fake)
    assert market_data.market_data_root is not None
    btc_1h_id = product_dataset_id(scope.instruments[0], BarInterval("1h"))
    first_1h = next(item for item in first.generations if item.dataset_id == btc_1h_id)
    _, first_series = resolve_immutable_generation(
        market_data.market_data_root,
        dataset_id=btc_1h_id,
        semantic_fingerprint=first_1h.semantic_fingerprint,
    )
    fake.calls.clear()
    second = worker.prepare(
        scope, now=_NOW + timedelta(hours=2), lookback_days=5, binance=fake
    )
    second_1h = next(
        item for item in second.generations if item.dataset_id == btc_1h_id
    )
    _, second_series = resolve_immutable_generation(
        market_data.market_data_root,
        dataset_id=btc_1h_id,
        semantic_fingerprint=second_1h.semantic_fingerprint,
    )
    assert len(fake.calls) == 2
    assert second_series.bars[: len(first_series.bars)] == first_series.bars
    assert len(second_series.bars) == len(first_series.bars) + 2
    assert second_1h.coverage_end_exclusive == datetime(2025, 3, 10, 16, 0, tzinfo=UTC)
