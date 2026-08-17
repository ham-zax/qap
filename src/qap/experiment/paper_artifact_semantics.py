"""Read-time deterministic revalidation of persisted paper-operation evidence."""

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import cast

from qap.execution import CostModel, execute_multi_asset_rebalance
from qap.experiment.reconciliation import reconcile_fill_sequence
from qap.market import MarketMetadata, PriceSnapshot, VenueInstrument
from qap.policy import build_rebalance_plan
from qap.portfolio import AllocationTarget, AssetId, PortfolioState


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


def _optional_decimal(value: object, *, field: str) -> Decimal | None:
    if value is None:
        return None
    return _decimal(value, field=field)


def _decimal_asset_mapping(value: object, *, field: str) -> dict[AssetId, Decimal]:
    result: dict[AssetId, Decimal] = {}
    for key, item in _object(value, field=field).items():
        result[AssetId(key)] = _decimal(item, field=f"{field}.{key}")
    return result


def _decimal_symbol_mapping(value: object, *, field: str) -> dict[str, Decimal]:
    return {
        key: _decimal(item, field=f"{field}.{key}")
        for key, item in _object(value, field=field).items()
    }


def _fingerprint(value: object, *, field: str) -> str:
    normalized = _text(value, field=field).lower()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(f"{field} must be a SHA-256 hex fingerprint")
    return normalized


def _bool(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be boolean")
    return value


def _int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    return value


def _metadata(record: Mapping[str, object]) -> dict[str, MarketMetadata]:
    normalized: dict[str, MarketMetadata] = {}
    for symbol, raw in _object(
        record.get("market_metadata"), field="market_metadata"
    ).items():
        item = _object(raw, field=f"market_metadata.{symbol}")
        instrument = VenueInstrument(
            venue=_text(item.get("venue"), field=f"{symbol}.venue"),
            venue_symbol=_text(
                item.get("venue_symbol"), field=f"{symbol}.venue_symbol"
            ),
            base=AssetId(_text(item.get("base"), field=f"{symbol}.base")),
            quote=AssetId(_text(item.get("quote"), field=f"{symbol}.quote")),
        )
        if instrument.venue_symbol != symbol:
            raise ValueError("paper market metadata symbol key is inconsistent")
        normalized[symbol] = MarketMetadata(
            instrument=instrument,
            status=_text(item.get("status"), field=f"{symbol}.status"),
            price_tick=_decimal(item.get("price_tick"), field=f"{symbol}.price_tick"),
            minimum_price=_optional_decimal(
                item.get("minimum_price"), field=f"{symbol}.minimum_price"
            ),
            maximum_price=_optional_decimal(
                item.get("maximum_price"), field=f"{symbol}.maximum_price"
            ),
            quantity_step=_decimal(
                item.get("quantity_step"), field=f"{symbol}.quantity_step"
            ),
            minimum_quantity=_optional_decimal(
                item.get("minimum_quantity"), field=f"{symbol}.minimum_quantity"
            ),
            maximum_quantity=_optional_decimal(
                item.get("maximum_quantity"), field=f"{symbol}.maximum_quantity"
            ),
            minimum_notional=_optional_decimal(
                item.get("minimum_notional"), field=f"{symbol}.minimum_notional"
            ),
            maximum_notional=_optional_decimal(
                item.get("maximum_notional"), field=f"{symbol}.maximum_notional"
            ),
            minimum_notional_applies_to_market=_bool(
                item.get("minimum_notional_applies_to_market"),
                field=f"{symbol}.minimum_notional_applies_to_market",
            ),
            maximum_notional_applies_to_market=_bool(
                item.get("maximum_notional_applies_to_market"),
                field=f"{symbol}.maximum_notional_applies_to_market",
            ),
            notional_average_price_minutes=_int(
                item.get("notional_average_price_minutes"),
                field=f"{symbol}.notional_average_price_minutes",
            ),
            market_quantity_step=_optional_decimal(
                item.get("market_quantity_step"), field=f"{symbol}.market_quantity_step"
            ),
            market_minimum_quantity=_optional_decimal(
                item.get("market_minimum_quantity"),
                field=f"{symbol}.market_minimum_quantity",
            ),
            market_maximum_quantity=_optional_decimal(
                item.get("market_maximum_quantity"),
                field=f"{symbol}.market_maximum_quantity",
            ),
        )
    return normalized


def _compare_decimal(actual: Decimal, raw: object, *, field: str) -> None:
    if actual != _decimal(raw, field=field):
        raise ValueError(f"paper semantic mismatch: {field}")


def _compare_holdings(state: PortfolioState, raw: object, *, field: str) -> None:
    expected = _decimal_asset_mapping(raw, field=field)
    if dict(state.holdings) != expected:
        raise ValueError(f"paper semantic mismatch: {field}")


def _validate_orders(record: Mapping[str, object], result: object) -> None:
    from qap.execution.multi_asset import MultiAssetRebalanceResult

    if not isinstance(result, MultiAssetRebalanceResult):
        raise TypeError("result must be MultiAssetRebalanceResult")
    raw_orders = _array(record.get("orders"), field="orders")
    if len(raw_orders) != len(result.orders):
        raise ValueError("paper semantic mismatch: order count")
    for position, (raw, expected) in enumerate(
        zip(raw_orders, result.orders, strict=True)
    ):
        item = _object(raw, field=f"orders[{position}]")
        if item.get("phase") != expected.phase.value:
            raise ValueError("paper semantic mismatch: order phase")
        if item.get("asset") != expected.asset.key:
            raise ValueError("paper semantic mismatch: order asset")
        if item.get("route_id") != expected.route_id:
            raise ValueError("paper semantic mismatch: order route")
        _compare_decimal(
            expected.requested_source_quantity,
            item.get("requested_source_quantity"),
            field=f"orders[{position}].requested_source_quantity",
        )
        raw_fill_ids = tuple(
            _text(value, field="order fill_id")
            for value in _array(item.get("fill_ids"), field="fill_ids")
        )
        if raw_fill_ids != tuple(fill.fill_id for fill in expected.fills):
            raise ValueError("paper semantic mismatch: order fill IDs")
        expected_reason = (
            None if expected.leg_reason is None else expected.leg_reason.value
        )
        if item.get("leg_reason") != expected_reason:
            raise ValueError("paper semantic mismatch: order reason")


def _validate_fills(record: Mapping[str, object], result: object) -> None:
    from qap.execution.multi_asset import MultiAssetRebalanceResult

    if not isinstance(result, MultiAssetRebalanceResult):
        raise TypeError("result must be MultiAssetRebalanceResult")
    raw_fills = _array(record.get("fills"), field="fills")
    if len(raw_fills) != len(result.fills):
        raise ValueError("paper semantic mismatch: fill count")
    for position, (raw, expected) in enumerate(
        zip(raw_fills, result.fills, strict=True)
    ):
        item = _object(raw, field=f"fills[{position}]")
        text_fields = {
            "fill_id": expected.fill_id,
            "decision_id": expected.decision_id,
            "venue": expected.venue,
            "venue_symbol": expected.venue_symbol,
            "side": expected.side.value,
        }
        for field, expected_value in text_fields.items():
            if item.get(field) != expected_value:
                raise ValueError(f"paper semantic mismatch: fills[{position}].{field}")
        if (
            datetime.fromisoformat(
                _text(item.get("execution_timestamp"), field="execution_timestamp")
            )
            != expected.execution_timestamp
        ):
            raise ValueError("paper semantic mismatch: fill execution timestamp")
        for field, expected_value in (
            ("base_quantity", expected.base_quantity),
            ("reference_price", expected.reference_price),
            ("execution_price", expected.execution_price),
            ("gross_quote_notional", expected.gross_quote_notional),
            ("fee_quote", expected.fee_amount),
            ("slippage_quote", expected.slippage_value),
        ):
            _compare_decimal(
                expected_value, item.get(field), field=f"fills[{position}].{field}"
            )
        deltas = _decimal_asset_mapping(
            item.get("balance_deltas"), field="balance_deltas"
        )
        if dict(expected.balance_deltas) != deltas:
            raise ValueError("paper semantic mismatch: fill balance deltas")


def _validate_tracking(record: Mapping[str, object], result: object) -> None:
    from qap.execution.multi_asset import MultiAssetRebalanceResult

    if not isinstance(result, MultiAssetRebalanceResult):
        raise TypeError("result must be MultiAssetRebalanceResult")
    raw_items = _array(record.get("tracking_errors"), field="tracking_errors")
    if len(raw_items) != len(result.tracking_errors):
        raise ValueError("paper semantic mismatch: tracking error count")
    for position, (raw, expected) in enumerate(
        zip(raw_items, result.tracking_errors, strict=True)
    ):
        item = _object(raw, field=f"tracking_errors[{position}]")
        if item.get("asset") != expected.asset.key:
            raise ValueError("paper semantic mismatch: tracking asset")
        for field, expected_value in (
            ("target_weight", expected.target_weight),
            ("actual_weight", expected.actual_weight),
            ("weight_error", expected.weight_error),
            ("unfilled_quantity", expected.unfilled_quantity),
            ("unfilled_value", expected.unfilled_value),
        ):
            _compare_decimal(
                expected_value,
                item.get(field),
                field=f"tracking_errors[{position}].{field}",
            )


def _validate_reconciliation(
    record: Mapping[str, object], result: object, prices: PriceSnapshot
) -> None:
    from qap.execution.multi_asset import MultiAssetRebalanceResult

    if not isinstance(result, MultiAssetRebalanceResult):
        raise TypeError("result must be MultiAssetRebalanceResult")
    report = reconcile_fill_sequence(
        starting_state=result.starting_state,
        fills=result.fills,
        expected_states=result.states_after_fills,
        valuation_prices=prices,
    )
    raw = _object(record.get("reconciliation"), field="reconciliation")
    if raw.get("matches") is not report.matches or not report.matches:
        raise ValueError("paper semantic mismatch: reconciliation status")
    for field, expected in (
        ("reported_fee_total", report.reported_fee_total),
        ("recomputed_fee_total", report.recomputed_fee_total),
        ("reported_turnover", report.reported_turnover),
        ("recomputed_turnover", report.recomputed_turnover),
        ("reported_slippage_total", report.reported_slippage_total),
        ("recomputed_slippage_total", report.recomputed_slippage_total),
    ):
        _compare_decimal(expected, raw.get(field), field=f"reconciliation.{field}")
    if (
        report.expected_terminal_value is None
        or report.recomputed_terminal_value is None
    ):
        raise ValueError("paper semantic reconciliation is missing terminal valuation")
    _compare_decimal(
        report.expected_terminal_value,
        raw.get("expected_terminal_value"),
        field="reconciliation.expected_terminal_value",
    )
    _compare_decimal(
        report.recomputed_terminal_value,
        raw.get("recomputed_terminal_value"),
        field="reconciliation.recomputed_terminal_value",
    )
    if _array(raw.get("economic_differences"), field="economic_differences"):
        raise ValueError("paper semantic mismatch: reconciliation economic differences")
    _compare_decimal(
        report.recomputed_fee_total,
        record.get("total_fee_quote"),
        field="total_fee_quote",
    )
    _compare_decimal(
        report.recomputed_slippage_total,
        record.get("total_slippage_quote"),
        field="total_slippage_quote",
    )


def validate_paper_operation_semantics(record: Mapping[str, object]) -> None:
    """Replay persisted normalized inputs and cross-check every economic output."""

    operation_id = _text(record.get("operation_id"), field="operation_id")
    _fingerprint(record.get("input_fingerprint"), field="input_fingerprint")
    _fingerprint(record.get("code_fingerprint"), field="code_fingerprint")
    bridge = AssetId(_text(record.get("bridge"), field="bridge"))
    execution_timestamp = datetime.fromisoformat(
        _text(record.get("execution_timestamp"), field="execution_timestamp")
    )
    starting_state = PortfolioState.from_holdings(
        _decimal_asset_mapping(
            record.get("starting_holdings"), field="starting_holdings"
        )
    )
    target_weights = _decimal_asset_mapping(
        record.get("target_weights"), field="target_weights"
    )
    target = AllocationTarget.for_basket(target_weights, basket=target_weights)
    prices = PriceSnapshot.from_prices(
        timestamp=execution_timestamp,
        numeraire=bridge,
        prices=_decimal_asset_mapping(
            record.get("valuation_prices"), field="valuation_prices"
        ),
    )
    metadata_by_symbol = _metadata(record)
    references = _decimal_symbol_mapping(
        record.get("reference_prices"), field="reference_prices"
    )
    notional_references = _decimal_symbol_mapping(
        record.get("market_notional_reference_prices"),
        field="market_notional_reference_prices",
    )
    instruments = tuple(item.instrument for item in metadata_by_symbol.values())
    metadata = {item.instrument: item for item in metadata_by_symbol.values()}
    reference_prices = {
        instrument: references[instrument.venue_symbol] for instrument in instruments
    }
    market_notional_reference_prices = {
        instrument: notional_references[instrument.venue_symbol]
        for instrument in instruments
    }
    plan = build_rebalance_plan(
        current_state=starting_state,
        target=target,
        prices=prices,
        execution_only_bridge=bridge,
    )
    result = execute_multi_asset_rebalance(
        decision_id=operation_id,
        execution_timestamp=execution_timestamp,
        plan=plan,
        bridge=bridge,
        instruments=instruments,
        reference_prices=reference_prices,
        market_notional_reference_prices=market_notional_reference_prices,
        market_metadata=metadata,
        cost_model=CostModel(
            fee_bps=_decimal(record.get("fee_bps"), field="fee_bps"),
            slippage_bps=_decimal(record.get("slippage_bps"), field="slippage_bps"),
        ),
    )
    _validate_orders(record, result)
    _validate_fills(record, result)
    _compare_holdings(
        result.ending_state, record.get("ending_holdings"), field="ending_holdings"
    )
    _compare_decimal(
        result.bridge_target_quantity,
        record.get("bridge_target_quantity"),
        field="bridge_target_quantity",
    )
    _compare_decimal(
        result.bridge_residual, record.get("bridge_residual"), field="bridge_residual"
    )
    _validate_tracking(record, result)
    _validate_reconciliation(record, result, prices)


__all__ = ["validate_paper_operation_semantics"]
