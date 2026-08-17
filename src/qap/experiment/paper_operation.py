"""Deterministic forward-paper operator workflow over recorded public inputs."""

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from qap.execution import CostModel, execute_multi_asset_rebalance
from qap.experiment.integrity import build_integrity_record, read_and_validate_integrity
from qap.experiment.paper_artifact_semantics import validate_paper_operation_semantics
from qap.experiment.provenance import code_fingerprint
from qap.experiment.reconciliation import ReconciliationReport, reconcile_fill_sequence
from qap.market import PriceSnapshot, VenueInstrument
from qap.market.adapters.binance_public import BinancePublicAdapter
from qap.policy import build_rebalance_plan
from qap.portfolio import AllocationTarget, AssetId, PortfolioState

_SCHEMA_VERSION = "qap.paper_operation.v1"
_SPEC_SCHEMA_VERSION = "qap.paper_operation_spec.v1"
_OPERATION_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_FORWARD_PAPER_RULE = (
    "This artifact is an operational paper-rebalance dry run, not prospective "
    "candidate evidence. Prospective evidence requires frozen candidate lineage "
    "and an observation period beginning after the freeze."
)


def valid_paper_operation_id(value: object) -> bool:
    return isinstance(value, str) and _OPERATION_ID.fullmatch(value) is not None


@dataclass(frozen=True, slots=True)
class PaperOperationArtifactPaths:
    """Immutable paths for one forward-paper operation artifact."""

    operation_id: str
    operation_directory: Path
    operation_file: Path
    integrity_file: Path


def _object(value: object, *, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    result: dict[str, object] = {}
    for key, item in cast(dict[object, object], value).items():
        if not isinstance(key, str):
            raise ValueError(f"{field} keys must be strings")
        result[key] = item
    return result


def _array(value: object, *, field: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return cast(list[object], value)


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _decimal(value: object, *, field: str) -> Decimal:
    raw = _text(value, field=field)
    try:
        parsed = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"{field} must be an exact decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field} must be finite")
    return parsed


def _decimal_mapping(value: object, *, field: str) -> dict[AssetId, Decimal]:
    raw = _object(value, field=field)
    result: dict[AssetId, Decimal] = {}
    for key, item in raw.items():
        asset = AssetId(key)
        if asset in result:
            raise ValueError(f"{field} contains duplicate canonical assets")
        result[asset] = _decimal(item, field=f"{field}.{key}")
    return result


def _timestamp(value: object) -> datetime:
    raw = _text(value, field="execution_timestamp")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("execution_timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("execution_timestamp must be UTC")
    return parsed.astimezone(UTC)


def _repository_file(repository_root: Path, relative: object) -> Path:
    raw = _text(relative, field="exchange_info_fixture")
    root = repository_root.resolve()
    path = (root / raw).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            "exchange_info_fixture must stay within repository_root"
        ) from exc
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def _load_json_object(path: Path, *, field: str) -> dict[str, object]:
    try:
        value: object = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field} must contain valid JSON") from exc
    return _object(value, field=field)


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("utf-8")


def _input_fingerprint(
    spec: Mapping[str, object],
    exchange_info: Mapping[str, object],
) -> str:
    digest = sha256()
    digest.update(b"qap.paper-operation-input.v1\0")
    digest.update(_canonical_json({"spec": spec, "exchange_info": exchange_info}))
    return digest.hexdigest()


def _holdings(state: PortfolioState) -> dict[str, str]:
    return {asset.key: str(quantity) for asset, quantity in state.holdings.items()}


def _metadata_record(metadata: object) -> dict[str, object]:
    from qap.market import MarketMetadata

    if not isinstance(metadata, MarketMetadata):
        raise TypeError("metadata must be MarketMetadata")
    return {
        "venue": metadata.instrument.venue,
        "venue_symbol": metadata.instrument.venue_symbol,
        "base": metadata.instrument.base.key,
        "quote": metadata.instrument.quote.key,
        "status": metadata.status,
        "price_tick": str(metadata.price_tick),
        "minimum_price": (
            None if metadata.minimum_price is None else str(metadata.minimum_price)
        ),
        "maximum_price": (
            None if metadata.maximum_price is None else str(metadata.maximum_price)
        ),
        "quantity_step": str(metadata.quantity_step),
        "minimum_quantity": (
            None
            if metadata.minimum_quantity is None
            else str(metadata.minimum_quantity)
        ),
        "maximum_quantity": (
            None
            if metadata.maximum_quantity is None
            else str(metadata.maximum_quantity)
        ),
        "minimum_notional": (
            None
            if metadata.minimum_notional is None
            else str(metadata.minimum_notional)
        ),
        "maximum_notional": (
            None
            if metadata.maximum_notional is None
            else str(metadata.maximum_notional)
        ),
        "minimum_notional_applies_to_market": (
            metadata.minimum_notional_applies_to_market
        ),
        "maximum_notional_applies_to_market": (
            metadata.maximum_notional_applies_to_market
        ),
        "notional_average_price_minutes": metadata.notional_average_price_minutes,
        "market_quantity_step": (
            None
            if metadata.market_quantity_step is None
            else str(metadata.market_quantity_step)
        ),
        "market_minimum_quantity": (
            None
            if metadata.market_minimum_quantity is None
            else str(metadata.market_minimum_quantity)
        ),
        "market_maximum_quantity": (
            None
            if metadata.market_maximum_quantity is None
            else str(metadata.market_maximum_quantity)
        ),
    }


def _fill_record(fill: object) -> dict[str, object]:
    from qap.execution import Fill

    if not isinstance(fill, Fill):
        raise TypeError("fill must be Fill")
    return {
        "fill_id": fill.fill_id,
        "decision_id": fill.decision_id,
        "execution_timestamp": fill.execution_timestamp.isoformat(),
        "venue": fill.instrument.venue,
        "venue_symbol": fill.instrument.venue_symbol,
        "side": fill.side.value,
        "base_quantity": str(fill.base_quantity),
        "reference_price": str(fill.reference_price),
        "execution_price": str(fill.execution_price),
        "gross_quote_notional": str(fill.gross_quote_notional),
        "fee_quote": str(fill.fee_amount),
        "slippage_quote": str(fill.slippage_value),
        "balance_deltas": {
            asset.key: str(delta) for asset, delta in fill.balance_deltas.items()
        },
    }


def _reconciliation_record(report: ReconciliationReport) -> dict[str, object]:
    return {
        "matches": report.matches,
        "reported_fee_total": str(report.reported_fee_total),
        "recomputed_fee_total": str(report.recomputed_fee_total),
        "reported_turnover": str(report.reported_turnover),
        "recomputed_turnover": str(report.recomputed_turnover),
        "reported_slippage_total": str(report.reported_slippage_total),
        "recomputed_slippage_total": str(report.recomputed_slippage_total),
        "expected_terminal_value": (
            None
            if report.expected_terminal_value is None
            else str(report.expected_terminal_value)
        ),
        "recomputed_terminal_value": (
            None
            if report.recomputed_terminal_value is None
            else str(report.recomputed_terminal_value)
        ),
        "economic_differences": [
            {
                "fill_id": difference.fill_id,
                "field": difference.field,
                "reported": str(difference.reported),
                "recomputed": str(difference.recomputed),
            }
            for difference in report.economic_differences
        ],
        "steps": [
            {
                "fill_id": step.fill_id,
                "matches": step.matches,
                "differences": [
                    {
                        "asset": difference.asset.key,
                        "expected": str(difference.expected),
                        "recomputed": str(difference.recomputed),
                        "delta": str(difference.delta),
                    }
                    for difference in step.differences
                ],
            }
            for step in report.steps
        ],
    }


def _build_record(
    spec: dict[str, object],
    exchange_info: dict[str, object],
    *,
    code_fingerprint_value: str,
) -> dict[str, object]:
    if spec.get("schema_version") != _SPEC_SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {_SPEC_SCHEMA_VERSION}")
    operation_id = _text(spec.get("operation_id"), field="operation_id")
    if not valid_paper_operation_id(operation_id):
        raise ValueError("operation_id contains unsupported characters")
    if spec.get("data_role") != "forward_paper":
        raise ValueError("data_role must be forward_paper")
    derived_evidence_fields = {
        "candidate_freeze",
        "evidence_class",
        "prospective_candidate_evidence",
    }
    declared_evidence_fields = sorted(derived_evidence_fields.intersection(spec))
    if declared_evidence_fields:
        raise ValueError(
            "prospective candidate evidence cannot be self-declared by a "
            "paper-operation spec; evidence classification is derived by the verified "
            "lineage workflow"
        )
    execution_timestamp = _timestamp(spec.get("execution_timestamp"))
    bridge = AssetId(_text(spec.get("bridge"), field="bridge"))
    starting_holdings = _decimal_mapping(
        spec.get("starting_holdings"), field="starting_holdings"
    )
    target_weights = _decimal_mapping(
        spec.get("target_weights"), field="target_weights"
    )
    valuation_prices = _decimal_mapping(
        spec.get("valuation_prices"), field="valuation_prices"
    )
    starting_state = PortfolioState.from_holdings(starting_holdings)
    target = AllocationTarget.for_basket(target_weights, basket=target_weights)
    prices = PriceSnapshot.from_prices(
        timestamp=execution_timestamp,
        numeraire=bridge,
        prices=valuation_prices,
    )
    plan = build_rebalance_plan(
        current_state=starting_state,
        target=target,
        prices=prices,
        execution_only_bridge=bridge,
    )

    raw_instruments = _array(spec.get("instruments"), field="instruments")
    instruments: list[VenueInstrument] = []
    reference_prices: dict[VenueInstrument, Decimal] = {}
    market_notional_reference_prices: dict[VenueInstrument, Decimal] = {}
    metadata_by_instrument: dict[VenueInstrument, object] = {}
    for position, raw_item in enumerate(raw_instruments):
        item = _object(raw_item, field=f"instruments[{position}]")
        symbol = _text(item.get("venue_symbol"), field="venue_symbol")
        base = AssetId(_text(item.get("base"), field="base"))
        quote = AssetId(_text(item.get("quote"), field="quote"))
        venue_base_asset = _text(item.get("venue_base_asset"), field="venue_base_asset")
        venue_quote_asset = _text(
            item.get("venue_quote_asset"), field="venue_quote_asset"
        )
        metadata = BinancePublicAdapter.market_metadata_from_payload(
            exchange_info,
            venue_symbol=symbol,
            base=base,
            quote=quote,
            venue_base_asset=venue_base_asset,
            venue_quote_asset=venue_quote_asset,
        )
        instrument = metadata.instrument
        if instrument in reference_prices:
            raise ValueError(f"duplicate instrument {symbol}")
        instruments.append(instrument)
        reference_prices[instrument] = _decimal(
            item.get("reference_price"), field=f"{symbol}.reference_price"
        )
        market_notional_reference_prices[instrument] = _decimal(
            item.get("notional_reference_price"),
            field=f"{symbol}.notional_reference_price",
        )
        metadata_by_instrument[instrument] = metadata

    from qap.market import MarketMetadata

    typed_metadata: dict[VenueInstrument, MarketMetadata] = {}
    for instrument, metadata in metadata_by_instrument.items():
        if not isinstance(metadata, MarketMetadata):
            raise TypeError("normalized market metadata has unexpected type")
        typed_metadata[instrument] = metadata

    cost_model = CostModel(
        fee_bps=_decimal(spec.get("fee_bps"), field="fee_bps"),
        slippage_bps=_decimal(spec.get("slippage_bps"), field="slippage_bps"),
    )
    result = execute_multi_asset_rebalance(
        decision_id=operation_id,
        execution_timestamp=execution_timestamp,
        plan=plan,
        bridge=bridge,
        instruments=tuple(instruments),
        reference_prices=reference_prices,
        market_notional_reference_prices=market_notional_reference_prices,
        market_metadata=typed_metadata,
        cost_model=cost_model,
    )
    reconciliation = reconcile_fill_sequence(
        starting_state=starting_state,
        fills=result.fills,
        expected_states=result.states_after_fills,
        valuation_prices=prices,
    )
    if not reconciliation.matches or reconciliation.ending_state != result.ending_state:
        raise ValueError("paper operation reconciliation failed")

    return {
        "schema_version": _SCHEMA_VERSION,
        "operation_id": operation_id,
        "data_role": "forward_paper",
        "evidence_class": "operational_dry_run",
        "prospective_candidate_evidence": False,
        "execution_timestamp": execution_timestamp.isoformat(),
        "input_fingerprint": _input_fingerprint(spec, exchange_info),
        "code_fingerprint": code_fingerprint_value,
        "fee_bps": _text(spec.get("fee_bps"), field="fee_bps"),
        "slippage_bps": _text(spec.get("slippage_bps"), field="slippage_bps"),
        "source_note": _text(spec.get("source_note"), field="source_note"),
        "bridge": bridge.key,
        "starting_holdings": _holdings(starting_state),
        "target_weights": {
            asset.key: str(weight) for asset, weight in target.weights.items()
        },
        "valuation_prices": {
            asset.key: str(price) for asset, price in prices.prices.items()
        },
        "reference_prices": {
            instrument.venue_symbol: str(price)
            for instrument, price in sorted(
                reference_prices.items(), key=lambda item: item[0].venue_symbol
            )
        },
        "market_notional_reference_prices": {
            instrument.venue_symbol: str(price)
            for instrument, price in sorted(
                market_notional_reference_prices.items(),
                key=lambda item: item[0].venue_symbol,
            )
        },
        "market_metadata": {
            instrument.venue_symbol: _metadata_record(metadata)
            for instrument, metadata in sorted(
                typed_metadata.items(), key=lambda item: item[0].venue_symbol
            )
        },
        "orders": [
            {
                "phase": order.phase.value,
                "asset": order.asset.key,
                "route_id": order.route_id,
                "requested_source_quantity": str(order.requested_source_quantity),
                "fill_ids": [fill.fill_id for fill in order.fills],
                "leg_reason": (
                    None if order.leg_reason is None else order.leg_reason.value
                ),
            }
            for order in result.orders
        ],
        "fills": [_fill_record(fill) for fill in result.fills],
        "ending_holdings": _holdings(result.ending_state),
        "bridge_target_quantity": str(result.bridge_target_quantity),
        "bridge_residual": str(result.bridge_residual),
        "tracking_errors": [
            {
                "asset": item.asset.key,
                "target_weight": str(item.target_weight),
                "actual_weight": str(item.actual_weight),
                "weight_error": str(item.weight_error),
                "unfilled_quantity": str(item.unfilled_quantity),
                "unfilled_value": str(item.unfilled_value),
            }
            for item in result.tracking_errors
        ],
        "total_fee_quote": str(reconciliation.recomputed_fee_total),
        "total_slippage_quote": str(reconciliation.recomputed_slippage_total),
        "reconciliation": _reconciliation_record(reconciliation),
        "research_boundary": {
            "eligible_for_parameter_selection": False,
            "eligible_for_model_promotion": False,
            "eligible_for_deployment_evidence": False,
            "rule": _FORWARD_PAPER_RULE,
        },
    }


def run_paper_operation_to_artifact(
    spec_path: Path,
    *,
    repository_root: Path,
    output_root: Path,
) -> PaperOperationArtifactPaths:
    """Execute one recorded forward-paper operation and write immutable JSON."""

    spec = _load_json_object(spec_path, field="paper operation spec")
    exchange_path = _repository_file(repository_root, spec.get("exchange_info_fixture"))
    exchange_info = _load_json_object(exchange_path, field="exchange_info_fixture")
    record = _build_record(
        spec,
        exchange_info,
        code_fingerprint_value=code_fingerprint(repository_root),
    )
    operation_id = cast(str, record["operation_id"])
    operation_directory = output_root / operation_id
    operation_file = operation_directory / "paper_operation.json"
    integrity_file = operation_directory / "integrity.json"
    try:
        operation_directory.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise FileExistsError(f"paper operation {operation_id} already exists") from exc
    temporary = operation_directory / ".paper_operation.json.tmp"
    temporary.write_bytes(_canonical_json(record))
    temporary.replace(operation_file)
    integrity = build_integrity_record(
        operation_directory,
        artifact_id=operation_id,
        file_names=(operation_file.name,),
    )
    integrity_file.write_bytes(_canonical_json(integrity.model_dump(mode="json")))
    return PaperOperationArtifactPaths(
        operation_id=operation_id,
        operation_directory=operation_directory,
        operation_file=operation_file,
        integrity_file=integrity_file,
    )


def read_paper_operation_artifact(path: Path) -> dict[str, Any]:
    """Read one immutable paper-operation artifact and revalidate its economics."""

    read_and_validate_integrity(
        path.parent,
        artifact_id=path.parent.name,
        required_files=frozenset({path.name}),
        allowed_files=frozenset({path.name}),
    )
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    record = _object(raw, field="paper operation artifact")
    if record.get("schema_version") != _SCHEMA_VERSION:
        raise ValueError(f"paper operation schema must be {_SCHEMA_VERSION}")
    if record.get("operation_id") != path.parent.name:
        raise ValueError("paper operation identity does not match its directory")
    validate_paper_operation_semantics(record)
    return cast(dict[str, Any], record)


__all__ = [
    "PaperOperationArtifactPaths",
    "read_paper_operation_artifact",
    "run_paper_operation_to_artifact",
    "valid_paper_operation_id",
]
