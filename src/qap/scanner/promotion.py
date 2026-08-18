"""Deterministic Scanner-V1 Slice-1 automatic and manual promotion policy."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import cast

from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerProtocol
from qap.scanner.scout import ScoutTrialRecord, ScoutTrialStatus


class PromotionStatus(StrEnum):
    AUTOMATIC_PROMOTED = "automatic_promoted"
    AUTOMATIC_EXCLUDED = "automatic_excluded"
    MANUAL_PROMOTED = "manual_promoted"


@dataclass(frozen=True, slots=True)
class PromotionRecord:
    candidate_id: str
    promotion_rank: int | None
    promotion_status: PromotionStatus
    budget_reason: str | None
    automatic_selected: bool
    manual_selected: bool
    selected_for_replay: bool
    direct_execution_instrument_id: str | None = None
    deep_replay_run_id: str | None = None
    deep_replay_status: str | None = None
    economic_gate_status: str | None = None


def _canonical_rank_key(record: ScoutTrialRecord) -> tuple[object, ...]:
    proxy = record.scout_relative_wealth_proxy
    if proxy is None:
        raise ValueError("valid automatic scout record must carry a proxy value")
    return (
        -proxy,
        record.scout_turnover_proxy,
        record.venue,
        record.pair_id,
        record.model_family,
        record.orientation,
        record.resolution,
        record.template_id,
        record.candidate_id,
    )


def _pair_assets(pair_id: str) -> tuple[str, str]:
    parts = pair_id.split("/")
    if len(parts) != 2 or not all(part.strip() for part in parts):
        raise ValueError("pair_id must contain exactly two non-empty assets")
    if parts[0] == parts[1]:
        raise ValueError("pair_id assets must be distinct")
    return parts[0], parts[1]


def apply_promotion_policy(
    scout_records: Sequence[ScoutTrialRecord],
    *,
    manual_candidate_ids: Sequence[str] = (),
    protocol: ScannerProtocol = SCANNER_V1_SLICE1,
) -> tuple[PromotionRecord, ...]:
    """Apply frozen automatic diversity caps and separate explicit manual requests."""

    if not isinstance(cast(object, protocol), ScannerProtocol):
        raise TypeError("protocol must be a ScannerProtocol")
    records = tuple(scout_records)
    if any(
        not isinstance(cast(object, record), ScoutTrialRecord) for record in records
    ):
        raise TypeError("scout_records must contain ScoutTrialRecord values")
    if len({record.candidate_id for record in records}) != len(records):
        raise ValueError("scout_records must contain unique candidate IDs")
    horizons = {record.horizon for record in records}
    if len(horizons) > 1:
        raise ValueError("promotion policy operates on one horizon at a time")

    manual_ids = tuple(manual_candidate_ids)
    if any(
        not isinstance(cast(object, candidate_id), str) or not candidate_id
        for candidate_id in manual_ids
    ):
        raise TypeError("manual_candidate_ids must contain non-empty strings")
    if len(set(manual_ids)) != len(manual_ids):
        raise ValueError("manual_candidate_ids must be unique")
    by_id = {record.candidate_id: record for record in records}
    unknown_manual = sorted(set(manual_ids) - set(by_id))
    if unknown_manual:
        raise ValueError(f"unknown manual candidate ID: {unknown_manual[0]}")
    manual_set = set(manual_ids)

    automatic = sorted(
        (
            record
            for record in records
            if record.trial_status is ScoutTrialStatus.VALID
            and record.automatic_neighbor_selected
        ),
        key=_canonical_rank_key,
    )

    automatic_results: dict[str, PromotionRecord] = {}
    asset_counts: dict[str, int] = {}
    pair_family_seen: set[tuple[str, str]] = set()
    promoted_count = 0

    for rank, record in enumerate(automatic, start=1):
        asset_a, asset_b = _pair_assets(record.pair_id)
        pair_family = (record.pair_id, record.model_family)
        reason: str | None = None
        if promoted_count >= protocol.automatic_replay_cap_per_horizon:
            reason = "automatic_replay_cap"
        elif pair_family in pair_family_seen:
            reason = "pair_family_cap"
        elif (
            asset_counts.get(asset_a, 0)
            >= protocol.max_promotions_per_asset_per_horizon
            or asset_counts.get(asset_b, 0)
            >= protocol.max_promotions_per_asset_per_horizon
        ):
            reason = "asset_cap"

        automatic_selected = reason is None
        if automatic_selected:
            promoted_count += 1
            pair_family_seen.add(pair_family)
            asset_counts[asset_a] = asset_counts.get(asset_a, 0) + 1
            asset_counts[asset_b] = asset_counts.get(asset_b, 0) + 1
        manual_selected = record.candidate_id in manual_set
        status = (
            PromotionStatus.AUTOMATIC_PROMOTED
            if automatic_selected
            else (
                PromotionStatus.MANUAL_PROMOTED
                if manual_selected
                else PromotionStatus.AUTOMATIC_EXCLUDED
            )
        )
        automatic_results[record.candidate_id] = PromotionRecord(
            candidate_id=record.candidate_id,
            promotion_rank=rank,
            promotion_status=status,
            budget_reason=reason,
            automatic_selected=automatic_selected,
            manual_selected=manual_selected,
            selected_for_replay=automatic_selected or manual_selected,
        )

    manual_only: list[PromotionRecord] = []
    for candidate_id in sorted(manual_set):
        if candidate_id in automatic_results:
            continue
        manual_only.append(
            PromotionRecord(
                candidate_id=candidate_id,
                promotion_rank=None,
                promotion_status=PromotionStatus.MANUAL_PROMOTED,
                budget_reason=None,
                automatic_selected=False,
                manual_selected=True,
                selected_for_replay=True,
            )
        )

    automatic_ordered = tuple(
        automatic_results[record.candidate_id] for record in automatic
    )
    return (*automatic_ordered, *manual_only)


__all__ = [
    "PromotionRecord",
    "PromotionStatus",
    "apply_promotion_policy",
]
