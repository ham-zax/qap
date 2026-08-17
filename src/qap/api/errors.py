"""Stable API-boundary errors that do not expose local implementation details."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApiBoundaryError(Exception):
    code: str
    message: str
    status_code: int
    context: dict[str, str]


def run_not_found(run_id: str) -> ApiBoundaryError:
    return ApiBoundaryError(
        code="run_not_found",
        message="Run was not found.",
        status_code=404,
        context={"run_id": run_id},
    )


def corrupt_artifact(run_id: str) -> ApiBoundaryError:
    return ApiBoundaryError(
        code="corrupt_artifact",
        message="Run artifacts are invalid.",
        status_code=409,
        context={"run_id": run_id},
    )


def invalid_pair_orientation(
    *,
    asset_x: str,
    asset_y: str,
    orientation: str,
) -> ApiBoundaryError:
    return ApiBoundaryError(
        code="invalid_pair_orientation",
        message="Pair orientation does not match the requested assets.",
        status_code=422,
        context={
            "asset_x": asset_x,
            "asset_y": asset_y,
            "orientation": orientation,
        },
    )


def anchor_unavailable(*, run_id: str, anchor: str) -> ApiBoundaryError:
    return ApiBoundaryError(
        code="anchor_unavailable",
        message="Anchor series is unavailable for this run.",
        status_code=404,
        context={"run_id": run_id, "anchor": anchor},
    )


def market_data_unavailable(run_id: str) -> ApiBoundaryError:
    return ApiBoundaryError(
        code="market_data_unavailable",
        message="Committed market data is unavailable for this run.",
        status_code=409,
        context={"run_id": run_id},
    )


__all__ = [
    "ApiBoundaryError",
    "anchor_unavailable",
    "corrupt_artifact",
    "invalid_pair_orientation",
    "market_data_unavailable",
    "run_not_found",
]
