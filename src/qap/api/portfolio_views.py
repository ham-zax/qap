"""Portfolio HTTP projections from validated immutable experiment artifacts."""

from datetime import UTC, datetime
from decimal import Decimal
from itertools import pairwise
from typing import Any, cast

from qap.api.schemas import (
    AssetDeltaDto,
    ConcentrationSummaryDto,
    CostSummaryDto,
    ExactPointDto,
    FillAuditDto,
    HoldingDto,
    HoldingsSnapshotDto,
    PerformanceSeriesDto,
    PortfolioPerformanceDto,
    PortfolioSnapshotDto,
    RebalanceDecisionAuditDto,
)
from qap.experiment import LoadedRunArtifacts
from qap.portfolio._decimal import exact_multiply, exact_subtract, exact_sum


def portfolio_snapshot(loaded: LoadedRunArtifacts) -> PortfolioSnapshotDto:
    rows = _table_rows(loaded.inventory)
    strategy = loaded.result.role("strategy")
    starting = _initial_holding_snapshot(loaded)
    terminal = _holding_snapshot(rows, role="strategy", first=False)
    hodl_terminal = _holding_snapshot(rows, role="hodl", first=False)
    role_terminals = tuple(
        _holding_snapshot(rows, role=role.role, first=False)
        for role in loaded.result.roles
    )
    role_names = {snapshot.role for snapshot in role_terminals}
    matched_terminal = (
        _holding_snapshot(rows, role="matched_contribution", first=False)
        if "matched_contribution" in role_names
        else None
    )
    history = _holding_history(rows, role="strategy")
    allocation_history = history if history[0] == starting else (starting, *history)
    return PortfolioSnapshotDto(
        run_id=loaded.provenance.run_id,
        starting=starting,
        terminal=terminal,
        hodl_terminal=hodl_terminal,
        role_terminals=role_terminals,
        allocation_history=allocation_history,
        concentration=_concentration_summary(starting, terminal),
        strategy_vs_hodl_terminal_deltas=_holding_deltas(terminal, hodl_terminal),
        strategy_vs_matched_contribution_terminal_deltas=(
            None
            if matched_terminal is None
            else _holding_deltas(terminal, matched_terminal)
        ),
        strategy_costs=CostSummaryDto(
            fill_count=strategy.fill_count,
            fees_value=str(strategy.fees_value),
            slippage_value=str(strategy.slippage_value),
            turnover_value=str(strategy.turnover_value),
        ),
        rebalance_audit=_rebalance_audit(loaded, rows),
    )


def portfolio_performance(loaded: LoadedRunArtifacts) -> PortfolioPerformanceDto:
    rows = _table_rows(loaded.performance)
    series = tuple(
        PerformanceSeriesDto(
            name=name,
            points=tuple(
                ExactPointDto(
                    timestamp=_row_timestamp(row),
                    value=str(row[name]),
                )
                for row in rows
            ),
        )
        for name in loaded.performance.schema.names
        if name != "timestamp"
    )
    return PortfolioPerformanceDto(
        run_id=loaded.provenance.run_id,
        primary_incremental_benchmark=loaded.result.primary_incremental_benchmark,
        maximum_relative_drawdown_vs_hodl=str(
            loaded.result.maximum_relative_drawdown_vs_hodl
        ),
        time_below_hodl_seconds=_time_below_seconds(
            rows,
            column="relative::strategy_vs_hodl",
        ),
        time_below_primary_control_seconds=(
            _time_below_seconds(
                rows,
                column="relative::strategy_vs_primary_control",
            )
            if "relative::strategy_vs_primary_control"
            in loaded.performance.schema.names
            else None
        ),
        series=series,
    )


def _time_below_seconds(
    rows: tuple[dict[str, object], ...],
    *,
    column: str,
) -> int:
    total = 0
    for current, following in pairwise(rows):
        if Decimal(str(current[column])) >= 0:
            continue
        interval = _row_timestamp(following) - _row_timestamp(current)
        if interval.total_seconds() <= 0 or interval.microseconds != 0:
            raise ValueError(
                "performance timestamps must be strictly increasing whole seconds"
            )
        total += interval.days * 86_400 + interval.seconds
    return total


def _table_rows(table: Any) -> tuple[dict[str, object], ...]:
    return tuple(cast(list[dict[str, object]], table.to_pylist()))


def _row_timestamp(row: dict[str, object]) -> datetime:
    timestamp = row.get("timestamp")
    if not isinstance(timestamp, datetime):
        raise ValueError("artifact table row is missing its UTC timestamp")
    return timestamp


def _initial_holding_snapshot(
    loaded: LoadedRunArtifacts,
) -> HoldingsSnapshotDto:
    event = next(
        (
            item
            for item in loaded.events
            if item.get("role") == "strategy"
            and item.get("event_type") == "initial_state"
        ),
        None,
    )
    if event is None:
        raise ValueError("event artifact is missing strategy initial_state")
    payload = _payload(event)
    raw_holdings = payload.get("holdings")
    if not isinstance(raw_holdings, list):
        raise ValueError("initial_state holdings must be a list")
    holdings: list[HoldingDto] = []
    for raw in cast(list[object], raw_holdings):
        if not isinstance(raw, dict):
            raise ValueError("initial_state holding must be an object")
        holding = cast(dict[str, object], raw)
        holdings.append(
            HoldingDto(
                asset=str(holding["asset"]),
                quantity=str(holding["quantity"]),
                value=str(holding["value"]),
                weight=str(holding["weight"]),
            )
        )
    return HoldingsSnapshotDto(
        timestamp=_event_time(event),
        role="strategy",
        holdings=tuple(holdings),
    )


def _holdings_at(
    rows: tuple[dict[str, object], ...],
    *,
    role: str,
    timestamp: datetime,
) -> tuple[HoldingDto, ...]:
    selected = tuple(
        row
        for row in rows
        if row.get("role") == role and _row_timestamp(row) == timestamp
    )
    if not selected:
        return ()
    return tuple(
        HoldingDto(
            asset=str(row["asset"]),
            quantity=str(row["quantity"]),
            value=str(row["value"]),
            weight=str(row["weight"]),
        )
        for row in sorted(selected, key=lambda item: str(item["asset"]))
    )


def _role_timestamps(
    rows: tuple[dict[str, object], ...],
    *,
    role: str,
) -> tuple[datetime, ...]:
    timestamps = tuple(
        sorted({_row_timestamp(row) for row in rows if row.get("role") == role})
    )
    if not timestamps:
        raise ValueError(f"inventory artifact has no rows for role {role}")
    return timestamps


def _holding_snapshot(
    rows: tuple[dict[str, object], ...],
    *,
    role: str,
    first: bool,
) -> HoldingsSnapshotDto:
    timestamps = _role_timestamps(rows, role=role)
    timestamp = timestamps[0] if first else timestamps[-1]
    return HoldingsSnapshotDto(
        timestamp=timestamp,
        role=role,
        holdings=_holdings_at(rows, role=role, timestamp=timestamp),
    )


def _holding_history(
    rows: tuple[dict[str, object], ...],
    *,
    role: str,
) -> tuple[HoldingsSnapshotDto, ...]:
    return tuple(
        HoldingsSnapshotDto(
            timestamp=timestamp,
            role=role,
            holdings=_holdings_at(rows, role=role, timestamp=timestamp),
        )
        for timestamp in _role_timestamps(rows, role=role)
    )


def _concentration_values(snapshot: HoldingsSnapshotDto) -> tuple[str, str]:
    weights = tuple(Decimal(holding.weight) for holding in snapshot.holdings)
    if not weights:
        return "0", "0"
    maximum = max(weights)
    herfindahl = exact_sum(exact_multiply(weight, weight) for weight in weights)
    return str(maximum), str(herfindahl)


def _concentration_summary(
    starting: HoldingsSnapshotDto,
    terminal: HoldingsSnapshotDto,
) -> ConcentrationSummaryDto:
    start_max, start_hhi = _concentration_values(starting)
    terminal_max, terminal_hhi = _concentration_values(terminal)
    return ConcentrationSummaryDto(
        start_max_weight=start_max,
        terminal_max_weight=terminal_max,
        start_herfindahl=start_hhi,
        terminal_herfindahl=terminal_hhi,
    )


def _holding_deltas(
    candidate: HoldingsSnapshotDto,
    comparator: HoldingsSnapshotDto,
) -> tuple[AssetDeltaDto, ...]:
    candidate_by_asset = {holding.asset: holding for holding in candidate.holdings}
    comparator_by_asset = {holding.asset: holding for holding in comparator.holdings}
    assets = tuple(sorted(set(candidate_by_asset) | set(comparator_by_asset)))
    result: list[AssetDeltaDto] = []
    for asset in assets:
        candidate_holding = candidate_by_asset.get(asset)
        comparator_holding = comparator_by_asset.get(asset)
        candidate_quantity = Decimal(
            "0" if candidate_holding is None else candidate_holding.quantity
        )
        comparator_quantity = Decimal(
            "0" if comparator_holding is None else comparator_holding.quantity
        )
        candidate_value = Decimal(
            "0" if candidate_holding is None else candidate_holding.value
        )
        comparator_value = Decimal(
            "0" if comparator_holding is None else comparator_holding.value
        )
        result.append(
            AssetDeltaDto(
                asset=asset,
                quantity_delta=str(
                    exact_subtract(candidate_quantity, comparator_quantity)
                ),
                value_delta=str(exact_subtract(candidate_value, comparator_value)),
            )
        )
    return tuple(result)


def _payload(event: dict[str, object]) -> dict[str, object]:
    payload = event.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("event artifact payload must be an object")
    return cast(dict[str, object], payload)


def _event_time(event: dict[str, object]) -> datetime:
    raw = event.get("event_time")
    if not isinstance(raw, str):
        raise ValueError("event artifact must contain event_time")
    timestamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("event artifact time must be timezone-aware")
    return timestamp.astimezone(UTC)


def _string_mapping(value: object) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("event mapping payload must be an object")
    return {
        str(key): str(item) for key, item in cast(dict[object, object], value).items()
    }


def _fill_dto(event: dict[str, object]) -> FillAuditDto:
    payload = _payload(event)
    return FillAuditDto(
        fill_id=str(payload["fill_id"]),
        side=str(payload["side"]),
        base=str(payload["base"]),
        quote=str(payload["quote"]),
        reference_price=str(payload["reference_price"]),
        execution_price=str(payload["execution_price"]),
        base_quantity=str(payload["base_quantity"]),
        gross_quote_notional=str(payload["gross_quote_notional"]),
        fee_amount=str(payload["fee_amount"]),
        fee_asset=str(payload["fee_asset"]),
        slippage_value=str(payload["slippage_value"]),
    )


def _primary_control_target(
    events: tuple[dict[str, object], ...],
    *,
    decision_index: object,
    control_id: str | None,
) -> dict[str, str] | None:
    if control_id is None:
        return None
    role = f"control:{control_id}"
    for event in events:
        if (
            event.get("role") == role
            and event.get("decision_index") == decision_index
            and event.get("event_type") == "policy_decision"
        ):
            return _string_mapping(_payload(event).get("target_weights"))
    return None


def _rebalance_audit(
    loaded: LoadedRunArtifacts,
    inventory_rows: tuple[dict[str, object], ...],
) -> tuple[RebalanceDecisionAuditDto, ...]:
    events = tuple(loaded.events)
    strategy_events = tuple(
        event for event in events if event.get("role") == "strategy"
    )
    audits: list[RebalanceDecisionAuditDto] = []
    for decision in strategy_events:
        if decision.get("event_type") != "policy_decision":
            continue
        decision_index = decision.get("decision_index")
        related = tuple(
            event
            for event in strategy_events
            if event.get("decision_index") == decision_index
        )
        rebalance = next(
            (event for event in related if event.get("event_type") == "rebalance"),
            None,
        )
        fills = tuple(
            _fill_dto(event) for event in related if event.get("event_type") == "fill"
        )
        decision_payload = _payload(decision)
        rebalance_payload = None if rebalance is None else _payload(rebalance)
        event_time = _event_time(decision)
        requested_deltas = (
            None
            if rebalance_payload is None
            else _string_mapping(rebalance_payload.get("requested_quantity_deltas"))
        )
        audits.append(
            RebalanceDecisionAuditDto(
                decision_id=str(decision_payload["decision_id"]),
                decision_time=event_time,
                reason=str(decision_payload["reason"]),
                evidence_ids=tuple(
                    str(item)
                    for item in cast(list[object], decision_payload["evidence_ids"])
                ),
                current_weights=_string_mapping(
                    decision_payload.get("current_weights")
                ),
                baseline_target_weights=_primary_control_target(
                    events,
                    decision_index=decision_index,
                    control_id=loaded.result.primary_incremental_benchmark,
                ),
                target_weights=_string_mapping(decision_payload.get("target_weights")),
                modeled_fee_bps=str(loaded.manifest.execution.fee_bps),
                modeled_slippage_bps=str(loaded.manifest.execution.slippage_bps),
                requested_quantity_deltas=requested_deltas,
                selected=(
                    False
                    if rebalance_payload is None
                    else bool(rebalance_payload.get("selected"))
                ),
                fills=fills,
                post_fill_holdings=_holdings_at(
                    inventory_rows,
                    role="strategy",
                    timestamp=event_time,
                ),
            )
        )
    return tuple(audits)


__all__ = ["portfolio_performance", "portfolio_snapshot"]
