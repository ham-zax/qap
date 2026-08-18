import math
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from qap.market import (
    BarInterval,
    MarketBar,
    VenueInstrument,
    align_bar_series,
    validate_bar_series,
)
from qap.portfolio import AssetId, PairOrientation
from qap.relationship import EvidenceReciprocity, FitReciprocity

BTC = AssetId("BTC")
ETH = AssetId("ETH")
USDT = AssetId("USDT")
INTERVAL = BarInterval("1h")
START = datetime(2024, 1, 1, 10, tzinfo=UTC)
FINGERPRINTS = {BTC: "b" * 64, ETH: "e" * 64}


def _series(asset: AssetId, closes: tuple[float, ...], *, quote: AssetId = USDT):
    instrument = VenueInstrument(
        venue="fixture",
        venue_symbol=f"{asset.key}{quote.key}",
        base=asset,
        quote=quote,
    )
    return validate_bar_series(
        tuple(
            MarketBar(
                instrument=instrument,
                interval=INTERVAL,
                candle_open_time=START + position * INTERVAL.duration,
                source_close_time=(
                    START
                    + (position + 1) * INTERVAL.duration
                    - timedelta(milliseconds=1)
                ),
                open=close,
                high=close,
                low=close,
                close=close,
                volume=1.0,
            )
            for position, close in enumerate(closes)
        )
    )


def _aligned(
    btc: tuple[float, ...],
    eth: tuple[float, ...],
    *,
    eth_quote: AssetId = USDT,
):
    return align_bar_series((_series(BTC, btc), _series(ETH, eth, quote=eth_quote)))


def _expected_residual_zscore(
    numerator: tuple[float, ...], denominator: tuple[float, ...]
) -> float:
    y = np.log(np.asarray(numerator, dtype=np.float64))
    x = np.log(np.asarray(denominator, dtype=np.float64))
    design = np.column_stack((np.ones(len(x), dtype=np.float64), x))
    coefficients, *_ = np.linalg.lstsq(design, y, rcond=None)
    residuals = y - design @ coefficients
    return float(residuals[-1] / np.std(residuals, ddof=0))


def test_rolling_residual_matches_oriented_ols_residual_zscore() -> None:
    from qap.relationship.models import rolling_residual_observation

    btc = (100.0, 103.0, 101.0, 108.0, 111.0, 109.0)
    eth = (50.0, 52.0, 51.0, 55.0, 54.0, 58.0)
    observation = rolling_residual_observation(
        _aligned(btc, eth),
        orientation=PairOrientation(base=ETH, quote=BTC),
        source_fingerprints=FINGERPRINTS,
        window_bars=6,
        min_observations=6,
        as_of=START + 6 * INTERVAL.duration,
    )

    assert observation.status.value == "valid"
    assert observation.model_id == "rolling_log_price_ols_residual_zscore"
    assert observation.model_version == "1"
    assert observation.fit_reciprocity is FitReciprocity.REFIT_REQUIRED
    assert observation.evidence_reciprocity is EvidenceReciprocity.MODEL_SPECIFIC
    assert observation.values["score"] == pytest.approx(
        _expected_residual_zscore(eth, btc)
    )
    assert observation.values["beta"] != 0.0
    assert observation.base_source_fingerprint == "e" * 64
    assert observation.quote_source_fingerprint == "b" * 64
    assert len(observation.input_fingerprint) == 64


def test_rolling_residual_ignores_incomplete_future_bar() -> None:
    from qap.relationship.models import rolling_residual_observation

    as_of = START + 6 * INTERVAL.duration
    baseline = rolling_residual_observation(
        _aligned(
            (100.0, 103.0, 101.0, 108.0, 111.0, 109.0),
            (50.0, 52.0, 51.0, 55.0, 54.0, 58.0),
        ),
        orientation=PairOrientation(base=ETH, quote=BTC),
        source_fingerprints=FINGERPRINTS,
        window_bars=6,
        min_observations=6,
        as_of=as_of,
    )
    with_future = rolling_residual_observation(
        _aligned(
            (100.0, 103.0, 101.0, 108.0, 111.0, 109.0, 500.0),
            (50.0, 52.0, 51.0, 55.0, 54.0, 58.0, 1.0),
        ),
        orientation=PairOrientation(base=ETH, quote=BTC),
        source_fingerprints=FINGERPRINTS,
        window_bars=6,
        min_observations=6,
        as_of=as_of,
    )

    assert with_future.values == baseline.values
    assert with_future.input_fingerprint == baseline.input_fingerprint


def test_residual_reverse_orientation_is_refit_not_exact_negation() -> None:
    from qap.relationship.models import rolling_residual_observation

    aligned = _aligned(
        (100.0, 103.0, 101.0, 108.0, 111.0, 109.0),
        (50.0, 52.0, 51.0, 55.0, 54.0, 58.0),
    )
    direct = rolling_residual_observation(
        aligned,
        orientation=PairOrientation(base=ETH, quote=BTC),
        source_fingerprints=FINGERPRINTS,
        window_bars=6,
        min_observations=6,
        as_of=START + 6 * INTERVAL.duration,
    )
    reverse = rolling_residual_observation(
        aligned,
        orientation=PairOrientation(base=BTC, quote=ETH),
        source_fingerprints=FINGERPRINTS,
        window_bars=6,
        min_observations=6,
        as_of=START + 6 * INTERVAL.duration,
    )

    assert reverse.input_fingerprint != direct.input_fingerprint
    assert reverse.values["score"] != pytest.approx(-direct.values["score"])


def test_rolling_residual_reports_insufficient_history_and_degenerate_fit() -> None:
    from qap.relationship.models import rolling_residual_observation

    insufficient = rolling_residual_observation(
        _aligned((100.0, 101.0), (50.0, 51.0)),
        orientation=PairOrientation(base=ETH, quote=BTC),
        source_fingerprints=FINGERPRINTS,
        window_bars=4,
        min_observations=3,
        as_of=START + 2 * INTERVAL.duration,
    )
    assert insufficient.status.value == "insufficient_history"
    assert insufficient.values == {}

    denominator = (100.0, 110.0, 121.0, 133.1)
    numerator = tuple(value**2 for value in denominator)
    degenerate = rolling_residual_observation(
        _aligned(denominator, numerator),
        orientation=PairOrientation(base=ETH, quote=BTC),
        source_fingerprints=FINGERPRINTS,
        window_bars=4,
        min_observations=4,
        as_of=START + 4 * INTERVAL.duration,
    )
    assert degenerate.status.value == "insufficient_variance"
    assert degenerate.values == {}


def test_rolling_residual_requires_common_reference_coordinate() -> None:
    from qap.relationship.models import rolling_residual_observation

    with pytest.raises(ValueError, match="common quote/reference coordinate"):
        rolling_residual_observation(
            _aligned(
                (100.0, 103.0, 101.0),
                (50.0, 52.0, 51.0),
                eth_quote=BTC,
            ),
            orientation=PairOrientation(base=ETH, quote=BTC),
            source_fingerprints=FINGERPRINTS,
            window_bars=3,
            min_observations=3,
            as_of=START + 3 * INTERVAL.duration,
        )


def test_rolling_residual_score_is_finite_for_valid_observation() -> None:
    from qap.relationship.models import rolling_residual_observation

    observation = rolling_residual_observation(
        _aligned(
            (100.0, 104.0, 102.0, 107.0, 105.0),
            (80.0, 81.0, 79.0, 83.0, 84.0),
        ),
        orientation=PairOrientation(base=ETH, quote=BTC),
        source_fingerprints=FINGERPRINTS,
        window_bars=5,
        min_observations=5,
        as_of=START + 5 * INTERVAL.duration,
    )

    assert math.isfinite(observation.values["score"])
