"""Fail-closed orientation transforms for persisted model evidence."""

from qap.portfolio import PairOrientation
from qap.relationship.observation import EvidenceReciprocity, RelationshipDataError


def reorient_model_evidence_value(
    *,
    model_id: str,
    evidence_field: str,
    evidence_reciprocity: EvidenceReciprocity,
    persisted_orientation: PairOrientation,
    requested_orientation: PairOrientation,
    value: float | None,
) -> float | None:
    """Transform one persisted model value into the explicitly requested orientation."""

    if persisted_orientation.pair_id != requested_orientation.pair_id:
        raise RelationshipDataError("model evidence orientation changed canonical pair")
    if persisted_orientation == requested_orientation:
        return value
    if evidence_reciprocity is not EvidenceReciprocity.EXACT_TRANSFORM:
        raise RelationshipDataError(
            "requested reciprocal model evidence has no exact registered transform"
        )
    if model_id == "rolling_log_ratio_zscore" and evidence_field == "score":
        return None if value is None else -value
    raise RelationshipDataError(
        "no reciprocal transform registered for model evidence "
        f"{model_id}:{evidence_field}"
    )


__all__ = ["reorient_model_evidence_value"]
