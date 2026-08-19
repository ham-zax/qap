"""Explicit-capital qualification orchestration for prospective scanner evidence."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import cast

from qap.market import fingerprint_bar_series, read_parquet_bar_series
from qap.market.instruments import VenueInstrument
from qap.market.metadata import MarketMetadata
from qap.market.microstructure import PublicBookSnapshot, PublicMarketMetadataSnapshot
from qap.market.microstructure_storage import (
    read_public_book_snapshots,
    read_public_market_metadata_snapshots,
)
from qap.market.public_capture import CaptureKind, capture_file
from qap.market.public_evidence import PublicEvidenceBundle
from qap.portfolio._decimal import divide, exact_add, exact_multiply
from qap.scanner.catalog import ScannerCatalog
from qap.scanner.liquidity import BookSide, friction_evidence, walk_quote_notional
from qap.scanner.liquidity_policy import (
    CandidateCapacity,
    RequiredTradeFractions,
    candidate_capital_ceiling,
    evaluate_capture_contract,
    evaluate_directional_c95,
    find_directional_safe_size,
    required_trade_fractions,
)
from qap.scanner.models import ScanInputIdentity
from qap.scanner.prospective import CandidateFreeze, ForwardCheckpoint
from qap.scanner.prospective_artifact_schemas import CHECKPOINT_TABLE
from qap.scanner.prospective_artifacts import read_forward_cohort
from qap.scanner.prospective_integrity import (
    completed_generation_dirs,
    validate_completed_generation,
)
from qap.scanner.protocol import SCANNER_V1_SLICE1
from qap.scanner.qualification import QualificationRequest, qualify_candidate
from qap.scanner.qualification_artifacts import (
    QualificationEvidence,
    publish_qualification,
)


class QualificationRunError(ValueError):
    """Raised when qualification cannot be tied to authoritative evidence."""


def _utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise QualificationRunError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class ForwardQapState:
    """Scanner-owned view of the current QAP state needed for qualification."""

    qap_run_id: str
    direct_dataset_id: str
    instrument: VenueInstrument
    base_quantity: Decimal
    quote_quantity: Decimal


CurrentQapStateLoader = Callable[
    [
        CandidateFreeze,
        datetime,
        ScannerCatalog,
        Path,
        Path,
        datetime | None,
    ],
    ForwardQapState,
]
QualificationReplayRunner = Callable[
    [
        CandidateFreeze,
        ForwardCheckpoint,
        datetime,
        Decimal,
        Decimal,
        ScannerCatalog,
        Path,
        Path,
        datetime | None,
    ],
    tuple[str, bool, bool],
]


def _checkpoint_and_freeze(
    cohort_root: Path,
    checkpoint_id: str,
) -> tuple[Path, ForwardCheckpoint, CandidateFreeze]:
    try:
        cohort = read_forward_cohort(cohort_root)
    except (OSError, ValueError) as exc:
        raise QualificationRunError("forward cohort definition is malformed") from exc
    for directory in completed_generation_dirs(cohort_root):
        manifest, tables = validate_completed_generation(directory)
        if manifest.get("checkpoint_id") != checkpoint_id:
            continue
        rows = tables[CHECKPOINT_TABLE].to_pylist()
        if len(rows) != 1 or not isinstance(rows[0], dict):
            raise QualificationRunError("forward checkpoint is malformed")
        row = cast(dict[str, object], rows[0])
        try:
            raw_slices = json.loads(cast(str, row["forward_slices_json"]))
            if not isinstance(raw_slices, list):
                raise TypeError
            slice_items = cast(list[object], raw_slices)
            if row["evidence_role"] != "prospective":
                raise ValueError("forward checkpoint evidence role is invalid")
            checkpoint = ForwardCheckpoint(
                cohort_id=cast(str, row["cohort_id"]),
                candidate_id=cast(str, row["candidate_id"]),
                freeze_id=cast(str, row["freeze_id"]),
                checkpoint_index=cast(int, row["checkpoint_index"]),
                freeze_at=cast(datetime, row["freeze_at"]),
                eligible_information_end=cast(
                    datetime, row["eligible_information_end"]
                ),
                forward_start=cast(datetime, row["forward_start"]),
                first_outcome_complete_at=cast(
                    datetime, row["first_outcome_complete_at"]
                ),
                evidence_window_start=cast(datetime, row["evidence_window_start"]),
                evidence_window_end=cast(datetime, row["evidence_window_end"]),
                information_end=cast(datetime, row["information_end"]),
                forward_slices=tuple(
                    ScanInputIdentity.model_validate(item) for item in slice_items
                ),
                evidence_role="prospective",
                prospective_protocol_version=cast(
                    str, row["prospective_protocol_version"]
                ),
                prospective_protocol_identity=cast(
                    str, row["prospective_protocol_identity"]
                ),
                created_at=cast(datetime, row["information_end"]),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise QualificationRunError("forward checkpoint is malformed") from exc
        if checkpoint.checkpoint_id != checkpoint_id:
            raise QualificationRunError("forward checkpoint identity mismatch")
        freeze = next(
            (
                item
                for item in cohort.candidate_freezes
                if item.freeze_id == checkpoint.freeze_id
            ),
            None,
        )
        if freeze is None:
            raise QualificationRunError("checkpoint freeze is not in cohort")
        return directory, checkpoint, freeze
    raise QualificationRunError("completed forward checkpoint not found")


def _direct_context(
    *,
    freeze: CandidateFreeze,
    as_of: datetime,
    catalog: ScannerCatalog,
    data_root: Path,
    run_root: Path,
    load_current_state: CurrentQapStateLoader,
    run_timestamp: datetime | None,
) -> tuple[VenueInstrument, Decimal, Decimal, str]:
    state = load_current_state(
        freeze,
        as_of,
        catalog,
        data_root,
        run_root,
        run_timestamp,
    )
    current = catalog.source(state.direct_dataset_id)
    series = read_parquet_bar_series(data_root / current.relative_path)
    if series.instrument != state.instrument:
        raise QualificationRunError("current QAP direct-market lineage is incomplete")
    if fingerprint_bar_series(series) != current.expected_semantic_fingerprint:
        raise QualificationRunError("current direct-market source fingerprint mismatch")
    matches = tuple(bar for bar in series.bars if bar.bar_end_exclusive == as_of)
    if len(matches) != 1:
        raise QualificationRunError("qualification direct-market price is unavailable")
    price = Decimal(str(matches[0].close))
    base_value = exact_multiply(state.base_quantity, price)
    total_value = exact_add(base_value, state.quote_quantity)
    if total_value <= 0:
        raise QualificationRunError("current QAP terminal valuation is invalid")
    return state.instrument, price, divide(base_value, total_value), state.qap_run_id


def _capture_state(
    *,
    capture_root: Path,
    instrument: VenueInstrument,
    as_of: datetime,
    capture_evidence: PublicEvidenceBundle | None = None,
) -> tuple[
    tuple[PublicBookSnapshot, ...],
    tuple[PublicBookSnapshot, ...],
    PublicMarketMetadataSnapshot | None,
    bool,
]:
    if capture_evidence is None:
        l1_path = capture_file(
            capture_root,
            venue=instrument.venue,
            venue_symbol=instrument.venue_symbol,
            kind=CaptureKind.L1,
        )
        depth_path = capture_file(
            capture_root,
            venue=instrument.venue,
            venue_symbol=instrument.venue_symbol,
            kind=CaptureKind.DEPTH,
        )
        metadata_path = capture_file(
            capture_root,
            venue=instrument.venue,
            venue_symbol=instrument.venue_symbol,
            kind=CaptureKind.METADATA,
        )
        l1 = read_public_book_snapshots(l1_path) if l1_path.is_file() else ()
        depth = read_public_book_snapshots(depth_path) if depth_path.is_file() else ()
        metadata_rows = (
            read_public_market_metadata_snapshots(metadata_path)
            if metadata_path.is_file()
            else ()
        )
    else:
        if any(item.instrument != instrument for item in capture_evidence.l1):
            raise QualificationRunError("collector L1 evidence instrument mismatch")
        if any(item.instrument != instrument for item in capture_evidence.depth):
            raise QualificationRunError("collector depth evidence instrument mismatch")
        if any(
            item.metadata.instrument != instrument for item in capture_evidence.metadata
        ):
            raise QualificationRunError(
                "collector metadata evidence instrument mismatch"
            )
        l1 = capture_evidence.l1
        depth = capture_evidence.depth
        metadata_rows = capture_evidence.metadata
    metadata = next(
        (item for item in reversed(metadata_rows) if item.observed_at <= as_of),
        None,
    )
    coverage = evaluate_capture_contract(
        tuple(item.observed_at for item in l1),
        tuple(item.observed_at for item in depth),
        window_end=as_of,
    )
    window_l1 = tuple(
        item
        for item in l1
        if coverage.window_start <= item.observed_at < coverage.window_end
    )
    window_depth = tuple(
        item
        for item in depth
        if coverage.window_start <= item.observed_at < coverage.window_end
    )
    return (
        window_l1,
        window_depth,
        metadata,
        coverage.satisfied and metadata is not None,
    )


def _two_way(metadata: MarketMetadata) -> bool:
    if metadata.instrument.venue == "binance":
        return metadata.status == "TRADING"
    if metadata.instrument.venue == "gate":
        return metadata.status == "TRADABLE"
    return False


def _order_constraints_satisfied(
    metadata: MarketMetadata,
    *,
    price: Decimal,
    capital: Decimal,
    required: RequiredTradeFractions,
) -> bool:
    if metadata.minimum_price is not None and price < metadata.minimum_price:
        return False
    if metadata.maximum_price is not None and price > metadata.maximum_price:
        return False
    min_quantity = metadata.market_minimum_quantity or metadata.minimum_quantity
    max_quantity = metadata.market_maximum_quantity or metadata.maximum_quantity
    for fraction in (required.required_buy, required.required_sell):
        notional = exact_multiply(capital, fraction)
        quantity = divide(notional, price)
        if (
            metadata.minimum_notional_applies_to_market
            and metadata.minimum_notional is not None
            and notional < metadata.minimum_notional
        ):
            return False
        if (
            metadata.maximum_notional_applies_to_market
            and metadata.maximum_notional is not None
            and notional > metadata.maximum_notional
        ):
            return False
        if min_quantity is not None and quantity < min_quantity:
            return False
        if max_quantity is not None and quantity > max_quantity:
            return False
    return True


def _empirical_slippage_bps(
    depth: tuple[PublicBookSnapshot, ...],
    *,
    capital: Decimal,
    required: RequiredTradeFractions,
) -> Decimal | None:
    costs = SCANNER_V1_SLICE1.cost_policy
    totals: list[Decimal] = []
    for side, fraction in (
        (BookSide.BUY_BASE, required.required_buy),
        (BookSide.SELL_BASE, required.required_sell),
    ):
        quote_notional = exact_multiply(capital, fraction)
        evidence = tuple(
            friction_evidence(
                walk_quote_notional(
                    snapshot,
                    side=side,
                    quote_notional=quote_notional,
                ),
                fee_bps=costs.adverse_fee_bps,
            )
            for snapshot in depth
        )
        result = evaluate_directional_c95(
            evidence,
            side=side,
            quote_notional=quote_notional,
        )
        if not result.feasible or result.c95_friction_bps is None:
            return None
        totals.append(result.c95_friction_bps)
    slippage = max(totals) - costs.adverse_fee_bps
    return max(Decimal("0"), slippage)


def qualify_forward_checkpoint(
    *,
    cohort_root: str | Path,
    checkpoint_id: str,
    as_of: datetime,
    requested_capital: Decimal,
    catalog: ScannerCatalog,
    data_root: str | Path,
    capture_root: str | Path,
    run_root: str | Path,
    load_current_state: CurrentQapStateLoader,
    run_qualification: QualificationReplayRunner,
    run_timestamp: datetime | None = None,
    capture_evidence: PublicEvidenceBundle | None = None,
) -> Path:
    """Qualify one completed forward checkpoint at explicit hypothetical capital."""

    root = Path(cohort_root).resolve()
    checkpoint_directory, checkpoint, freeze = _checkpoint_and_freeze(
        root, checkpoint_id
    )
    qualification_as_of = _utc(as_of, field="as_of")
    if qualification_as_of < checkpoint.information_end:
        raise QualificationRunError("as_of must not precede the completed checkpoint")
    if not requested_capital.is_finite() or requested_capital <= 0:
        raise QualificationRunError("requested capital must be positive finite")
    del checkpoint_directory
    instrument, price, current_weight, current_state_run_id = _direct_context(
        freeze=freeze,
        as_of=qualification_as_of,
        catalog=catalog,
        data_root=Path(data_root).resolve(),
        run_root=Path(run_root).resolve(),
        load_current_state=load_current_state,
        run_timestamp=run_timestamp,
    )
    l1, depth, metadata_snapshot, capture_satisfied = _capture_state(
        capture_root=Path(capture_root).resolve(),
        instrument=instrument,
        as_of=qualification_as_of,
        capture_evidence=capture_evidence,
    )
    metadata = None if metadata_snapshot is None else metadata_snapshot.metadata
    current_two_way = metadata is not None and _two_way(metadata)
    required = required_trade_fractions(current_weight)
    capacity: CandidateCapacity | None = None
    buy_safe = sell_safe = None
    qualified_depth: tuple[PublicBookSnapshot, ...] = ()
    if capture_satisfied and metadata is not None:
        qualified_depth = depth
        try:
            buy_safe = find_directional_safe_size(
                qualified_depth,
                side=BookSide.BUY_BASE,
                market_metadata=metadata,
            )
            sell_safe = find_directional_safe_size(
                qualified_depth,
                side=BookSide.SELL_BASE,
                market_metadata=metadata,
            )
            capacity = candidate_capital_ceiling(
                q_safe_buy=buy_safe.q_safe,
                q_safe_sell=sell_safe.q_safe,
                current_base_weight=current_weight,
            )
        except ValueError:
            capacity = None

    ceiling = None if capacity is None else capacity.candidate_capital_ceiling
    requested_run_id: str | None = None
    requested_baseline = requested_adverse = False
    lower_capital: Decimal | None = None
    lower_run_id: str | None = None
    lower_baseline = lower_adverse = False
    tested_capital = (
        requested_capital if ceiling is None else min(requested_capital, ceiling)
    )
    constraints_satisfied = False
    if (
        capture_satisfied
        and metadata is not None
        and current_two_way
        and ceiling is not None
    ):
        constraints_satisfied = _order_constraints_satisfied(
            metadata,
            price=price,
            capital=tested_capital,
            required=required,
        )
        empirical = (
            _empirical_slippage_bps(
                qualified_depth,
                capital=tested_capital,
                required=required,
            )
            if constraints_satisfied
            else None
        )
        if empirical is not None:
            run_id, baseline, adverse = run_qualification(
                freeze,
                checkpoint,
                qualification_as_of,
                tested_capital,
                empirical,
                catalog,
                Path(data_root).resolve(),
                Path(run_root).resolve(),
                run_timestamp,
            )
            if requested_capital <= ceiling:
                requested_run_id = run_id
                requested_baseline = baseline
                requested_adverse = adverse
            else:
                lower_capital = tested_capital
                lower_run_id = run_id
                lower_baseline = baseline
                lower_adverse = adverse

    book_snapshot_ids: set[str] = {item.snapshot_id for item in (*l1, *depth)}
    metadata_snapshot_ids: set[str] = (
        {metadata_snapshot.snapshot_id} if metadata_snapshot is not None else set()
    )
    snapshot_ids = tuple(sorted(book_snapshot_ids | metadata_snapshot_ids))
    request = QualificationRequest(
        candidate_id=freeze.candidate_id,
        freeze_id=freeze.freeze_id,
        as_of=qualification_as_of,
        requested_capital=requested_capital,
        prospective_protocol_version=freeze.prospective_protocol_version,
        prospective_protocol_identity=freeze.prospective_protocol_identity,
        current_state_qap_run_id=current_state_run_id,
        capture_snapshot_ids=snapshot_ids,
        market_metadata_fingerprint=(
            None if metadata_snapshot is None else metadata_snapshot.snapshot_id
        ),
        eligibility_resolved=metadata_snapshot is not None,
        capture_contract_satisfied=capture_satisfied,
        current_two_way_trading=current_two_way,
        order_constraints_satisfied=constraints_satisfied,
        candidate_capital_ceiling=ceiling,
        requested_capital_qap_run_id=requested_run_id,
        requested_baseline_gate_passed=requested_baseline,
        requested_adverse_gate_passed=requested_adverse,
        lower_tested_capital=lower_capital,
        lower_capital_qap_run_id=lower_run_id,
        lower_baseline_gate_passed=lower_baseline,
        lower_adverse_gate_passed=lower_adverse,
    )
    decision = qualify_candidate(request)
    evidence = QualificationEvidence(
        checkpoint_id=checkpoint.checkpoint_id,
        decision=decision,
        q_star_buy=None if buy_safe is None else buy_safe.q_star,
        q_safe_buy=None if buy_safe is None else buy_safe.q_safe,
        q_star_sell=None if sell_safe is None else sell_safe.q_star,
        q_safe_sell=None if sell_safe is None else sell_safe.q_safe,
        current_base_weight=current_weight,
        required_buy_fraction=required.required_buy,
        required_sell_fraction=required.required_sell,
    )
    return publish_qualification(root, evidence)


__all__ = [
    "ForwardQapState",
    "QualificationRunError",
    "qualify_forward_checkpoint",
]
