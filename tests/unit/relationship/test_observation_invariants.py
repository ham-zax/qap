from datetime import UTC, datetime
from typing import Any

import pytest

from qap.portfolio import AssetId, PairOrientation
from qap.relationship import (
    EvidenceReciprocity,
    FitReciprocity,
    RelationshipDataError,
    RelationshipObservation,
    RelationshipObservationStatus,
)
from qap.relationship.models import (
    CrossSectionalRelativeObservation,
    CrossSectionalRelativeStatus,
)

BTC = AssetId("BTC")
ETH = AssetId("ETH")
SOL = AssetId("SOL")
ORIENTATION = PairOrientation(base=BTC, quote=ETH)
AT = datetime(2024, 1, 1, tzinfo=UTC)


def _relationship_observation(**overrides: Any) -> RelationshipObservation:
    values: dict[str, Any] = {
        "pair_id": ORIENTATION.pair_id,
        "orientation": ORIENTATION,
        "as_of": AT,
        "model_id": "test-model",
        "model_version": "1",
        "fit_reciprocity": FitReciprocity.EXACT_TRANSFORM,
        "evidence_reciprocity": EvidenceReciprocity.EXACT_TRANSFORM,
        "status": RelationshipObservationStatus.VALID,
        "window_observations": 10,
        "required_observations": 5,
        "coverage_observations": 10,
        "base_source_fingerprint": "a" * 64,
        "quote_source_fingerprint": "b" * 64,
        "input_fingerprint": "c" * 64,
        "values": {"score": 1.0},
    }
    values.update(overrides)
    return RelationshipObservation(**values)


def _cross_sectional_observation(**overrides: Any) -> CrossSectionalRelativeObservation:
    values: dict[str, Any] = {
        "as_of": AT,
        "model_id": "cross-sectional",
        "model_version": "1",
        "assets": (BTC, ETH, SOL),
        "window_returns": 2,
        "coverage_returns": 2,
        "status": CrossSectionalRelativeStatus.VALID,
        "pair_independence_limited": False,
        "common_mode_returns": (0.01, -0.02),
        "scores": {BTC: 0.1, ETH: -0.05, SOL: -0.05},
        "input_fingerprint": "d" * 64,
    }
    values.update(overrides)
    return CrossSectionalRelativeObservation(**values)


def test_relationship_observation_rejects_non_integer_counts() -> None:
    with pytest.raises(TypeError, match="window_observations must be an integer"):
        _relationship_observation(window_observations=10.5)


def test_relationship_observation_status_must_match_coverage() -> None:
    with pytest.raises(RelationshipDataError, match="valid.*coverage"):
        _relationship_observation(coverage_observations=0)

    with pytest.raises(RelationshipDataError, match="insufficient_history.*coverage"):
        _relationship_observation(
            status=RelationshipObservationStatus.INSUFFICIENT_HISTORY,
            coverage_observations=5,
            values={},
        )

    with pytest.raises(RelationshipDataError, match="insufficient_variance.*coverage"):
        _relationship_observation(
            status=RelationshipObservationStatus.INSUFFICIENT_VARIANCE,
            coverage_observations=4,
            values={},
        )


@pytest.mark.parametrize(
    ("overrides", "error"),
    [
        ({"as_of": datetime(2024, 1, 1)}, "as_of must be timezone-aware UTC"),
        ({"model_id": ""}, "model_id must be a non-empty string"),
        ({"model_version": ""}, "model_version must be a non-empty string"),
        ({"assets": (BTC, BTC, SOL)}, "assets must be unique"),
        ({"window_returns": -1}, "window_returns must be positive"),
        ({"coverage_returns": 3}, "coverage_returns must be within"),
        (
            {"common_mode_returns": (float("nan"), 0.0)},
            "common_mode_returns must be finite",
        ),
        ({"scores": {BTC: float("inf"), ETH: 0.0, SOL: 0.0}}, "scores must be finite"),
        ({"input_fingerprint": "bogus"}, "input fingerprint must be a SHA-256"),
    ],
)
def test_cross_sectional_observation_rejects_forged_fields(
    overrides: dict[str, Any],
    error: str,
) -> None:
    with pytest.raises((TypeError, ValueError, RelationshipDataError), match=error):
        _cross_sectional_observation(**overrides)


def test_cross_sectional_observation_status_must_match_payload() -> None:
    with pytest.raises(RelationshipDataError, match="valid.*coverage"):
        _cross_sectional_observation(coverage_returns=1)

    with pytest.raises(RelationshipDataError, match="insufficient_history.*payload"):
        _cross_sectional_observation(
            status=CrossSectionalRelativeStatus.INSUFFICIENT_HISTORY,
            coverage_returns=1,
        )
