import math
from datetime import UTC, datetime

import pytest

from qap.market import BarInterval
from qap.portfolio import AssetId, PairOrientation
from qap.relationship import (
    EvidenceKind,
    EvidenceReciprocity,
    FitReciprocity,
    RelationshipSeries,
)

BTC = AssetId("BTC")
ETH = AssetId("ETH")
INTERVAL = BarInterval("1h")
ORIENTATION = PairOrientation(base=ETH, quote=BTC)
TIMESTAMPS = tuple(datetime(2024, 1, 1, hour, tzinfo=UTC) for hour in (10, 11, 12, 13))


def _log_ratio_series(
    values: tuple[float, ...],
    *,
    orientation: PairOrientation = ORIENTATION,
) -> RelationshipSeries:
    base_fingerprint = "e" * 64 if orientation.base == ETH else "b" * 64
    quote_fingerprint = "b" * 64 if orientation.quote == BTC else "e" * 64
    return RelationshipSeries.from_values(
        pair_id=orientation.pair_id,
        orientation=orientation,
        interval=INTERVAL,
        timestamps=TIMESTAMPS[: len(values)],
        as_of=datetime(2024, 1, 1, 14, tzinfo=UTC),
        base_source_fingerprint=base_fingerprint,
        quote_source_fingerprint=quote_fingerprint,
        evidence_kind=EvidenceKind.LOG_RATIO,
        fit_reciprocity=FitReciprocity.EXACT_TRANSFORM,
        evidence_reciprocity=EvidenceReciprocity.EXACT_TRANSFORM,
        values=values,
    )


def test_rolling_log_ratio_score_matches_hand_calculated_population_zscore() -> None:
    from qap.relationship.models import rolling_log_ratio_observation

    observation = rolling_log_ratio_observation(
        _log_ratio_series((0.0, 1.0, 2.0, 100.0)),
        window_bars=3,
        min_observations=3,
        as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
    )

    assert observation.status.value == "valid"
    assert observation.pair_id == ORIENTATION.pair_id
    assert observation.orientation == ORIENTATION
    assert observation.model_id == "rolling_log_ratio_zscore"
    assert observation.model_version == "1"
    assert observation.fit_reciprocity is FitReciprocity.EXACT_TRANSFORM
    assert observation.evidence_reciprocity is EvidenceReciprocity.EXACT_TRANSFORM
    assert observation.window_observations == 3
    assert observation.required_observations == 3
    assert observation.coverage_observations == 3
    assert observation.values["score"] == pytest.approx(math.sqrt(3.0 / 2.0))
    assert len(observation.input_fingerprint) == 64
    assert observation.base_source_fingerprint == "e" * 64
    assert observation.quote_source_fingerprint == "b" * 64


def test_rolling_log_ratio_ignores_points_not_completed_by_as_of() -> None:
    from qap.relationship.models import rolling_log_ratio_observation

    baseline = rolling_log_ratio_observation(
        _log_ratio_series((0.0, 1.0, 2.0)),
        window_bars=3,
        min_observations=3,
        as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
    )
    with_future = rolling_log_ratio_observation(
        _log_ratio_series((0.0, 1.0, 2.0, 1000.0)),
        window_bars=3,
        min_observations=3,
        as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
    )

    assert with_future.values == baseline.values
    assert with_future.input_fingerprint == baseline.input_fingerprint


def test_rolling_log_ratio_reports_insufficient_history_without_fallback() -> None:
    from qap.relationship.models import rolling_log_ratio_observation

    observation = rolling_log_ratio_observation(
        _log_ratio_series((0.0, 1.0, 2.0)),
        window_bars=3,
        min_observations=3,
        as_of=datetime(2024, 1, 1, 12, tzinfo=UTC),
    )

    assert observation.status.value == "insufficient_history"
    assert observation.coverage_observations == 2
    assert observation.values == {}


@pytest.mark.parametrize(
    "values",
    [
        (1.0, 1.0, 1.0),
        (1.0, 1.0 + 1e-15, 1.0 + 2e-15),
    ],
)
def test_rolling_log_ratio_reports_insufficient_variance(
    values: tuple[float, ...],
) -> None:
    from qap.relationship.models import rolling_log_ratio_observation

    observation = rolling_log_ratio_observation(
        _log_ratio_series(values),
        window_bars=3,
        min_observations=3,
        as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
    )

    assert observation.status.value == "insufficient_variance"
    assert observation.values == {}


def test_rolling_log_ratio_reciprocal_orientation_has_exact_signed_transform() -> None:
    from qap.relationship.models import rolling_log_ratio_observation

    direct = rolling_log_ratio_observation(
        _log_ratio_series((0.0, 1.0, 2.0)),
        window_bars=3,
        min_observations=3,
        as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
    )
    reverse = rolling_log_ratio_observation(
        _log_ratio_series(
            (-0.0, -1.0, -2.0),
            orientation=ORIENTATION.inverted(),
        ),
        window_bars=3,
        min_observations=3,
        as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
    )

    assert reverse.pair_id == direct.pair_id
    assert reverse.values["score"] == pytest.approx(-direct.values["score"])


def test_rolling_log_ratio_requires_log_ratio_input_and_valid_window_contract() -> None:
    from qap.relationship.models import rolling_log_ratio_observation

    ratio = RelationshipSeries.from_values(
        pair_id=ORIENTATION.pair_id,
        orientation=ORIENTATION,
        interval=INTERVAL,
        timestamps=TIMESTAMPS[:3],
        as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
        base_source_fingerprint="e" * 64,
        quote_source_fingerprint="b" * 64,
        evidence_kind=EvidenceKind.RATIO,
        fit_reciprocity=FitReciprocity.EXACT_TRANSFORM,
        evidence_reciprocity=EvidenceReciprocity.EXACT_TRANSFORM,
        values=(1.0, 2.0, 3.0),
    )

    with pytest.raises(ValueError, match="log-ratio"):
        rolling_log_ratio_observation(
            ratio,
            window_bars=3,
            min_observations=3,
            as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="min_observations"):
        rolling_log_ratio_observation(
            _log_ratio_series((0.0, 1.0, 2.0)),
            window_bars=3,
            min_observations=4,
            as_of=datetime(2024, 1, 1, 13, tzinfo=UTC),
        )
