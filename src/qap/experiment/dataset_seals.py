"""Trusted research-role seals for datasets whose information state is reserved."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime

from qap.experiment.manifest import DataRole, ExperimentManifest


@dataclass(frozen=True, slots=True)
class DatasetSeal:
    """One repository-trusted data-role reservation keyed by semantic bytes."""

    semantic_fingerprint: str
    window_start: datetime
    window_end: datetime
    required_role: DataRole
    label: str


_RESERVED_FINAL_OOS = DatasetSeal(
    semantic_fingerprint=(
        "b3069c70fb61f1e7fb6a8b1d338194817ba8896dfd2618b96091c8c46686f2a5"
    ),
    window_start=datetime(2024, 1, 1, tzinfo=UTC),
    window_end=datetime(2025, 1, 1, tzinfo=UTC),
    required_role=DataRole.FINAL_OOS,
    label="BTCUSDT daily 2024 reserved final-OOS holdout",
)

_DATASET_SEALS = (_RESERVED_FINAL_OOS,)
_SEAL_BY_FINGERPRINT = {seal.semantic_fingerprint: seal for seal in _DATASET_SEALS}


def validate_expected_fingerprints_for_role(
    fingerprints: Iterable[str],
    *,
    data_role: DataRole,
) -> None:
    """Reject reserved semantic bytes before a caller reads their backing files."""

    for fingerprint in fingerprints:
        seal = _SEAL_BY_FINGERPRINT.get(fingerprint)
        if seal is None or data_role is seal.required_role:
            continue
        role = data_role.value
        raise ValueError(
            f"reserved final-OOS dataset cannot be used as {role}: {seal.label}"
        )


def validate_dataset_seals(manifest: ExperimentManifest) -> None:
    """Reject use of sealed dataset bytes outside their exact research role/window."""

    validate_expected_fingerprints_for_role(
        (source.expected_semantic_fingerprint for source in manifest.data_sources),
        data_role=manifest.data_role,
    )
    for source in manifest.data_sources:
        seal = _SEAL_BY_FINGERPRINT.get(source.expected_semantic_fingerprint)
        if seal is None:
            continue
        if (
            manifest.data_window.start != seal.window_start
            or manifest.data_window.end != seal.window_end
        ):
            raise ValueError(
                "reserved final-OOS dataset must use its exact sealed window: "
                f"{seal.label}"
            )


__all__ = [
    "DatasetSeal",
    "validate_dataset_seals",
    "validate_expected_fingerprints_for_role",
]
