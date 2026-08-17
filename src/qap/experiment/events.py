"""Deterministic exact JSONL event records for experiment audit trails."""

import json
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from qap.experiment.runner import ExperimentRun
from qap.portfolio import AssetId, PortfolioState, holding_values_at_prices
from qap.portfolio._decimal import divide, exact_sum

_EVENT_SCHEMA = "qap.experiment.event.v1"


def _decimal_mapping(values: Mapping[AssetId, Decimal]) -> dict[str, str]:
    return {asset.key: str(value) for asset, value in sorted(values.items())}


def _state_holdings(
    run: ExperimentRun,
    *,
    state: PortfolioState,
    prices: Mapping[AssetId, Decimal],
) -> list[dict[str, str]]:
    values = holding_values_at_prices(state, prices)
    total = exact_sum(values.values())
    holdings: list[dict[str, str]] = []
    for key in run.manifest.basket:
        asset = run.manifest.asset(key)
        quantity = state.quantity(asset)
        value = values.get(asset, Decimal("0"))
        weight = divide(value, total) if total > Decimal("0") else Decimal("0")
        holdings.append(
            {
                "asset": asset.key,
                "quantity": str(quantity),
                "value": str(value),
                "weight": str(weight),
            }
        )
    return holdings


def _state_weights(
    run: ExperimentRun,
    *,
    state: PortfolioState,
    prices: Mapping[AssetId, Decimal],
) -> dict[str, str]:
    values = holding_values_at_prices(state, prices)
    total = exact_sum(values.values())
    result: dict[str, str] = {}
    for key in run.manifest.basket:
        asset = run.manifest.asset(key)
        value = values.get(asset, Decimal("0"))
        weight = divide(value, total) if total > Decimal("0") else Decimal("0")
        result[asset.key] = str(weight)
    return result


def _base_record(
    *,
    run: ExperimentRun,
    role: str,
    sequence: int,
    decision_index: int,
    event_type: str,
    event_time: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": _EVENT_SCHEMA,
        "run_id": run.provenance.run_id,
        "role": role,
        "sequence": sequence,
        "decision_index": decision_index,
        "event_type": event_type,
        "event_time": event_time,
        "payload": payload,
    }


def build_event_records(run: ExperimentRun) -> tuple[dict[str, Any], ...]:
    """Serialize flows, decisions, rebalances, executions, and fills in order."""

    records: list[dict[str, Any]] = []
    sequence = 0
    for role in run.roles:
        if role.trace.steps:
            first_step = role.trace.steps[0]
            records.append(
                _base_record(
                    run=run,
                    role=role.role,
                    sequence=sequence,
                    decision_index=first_step.decision_index,
                    event_type="initial_state",
                    event_time=first_step.decision_time.isoformat(),
                    payload={
                        "holdings": _state_holdings(
                            run,
                            state=first_step.state_before_flows,
                            prices=first_step.price_snapshot.prices,
                        )
                    },
                )
            )
            sequence += 1
        for step in role.trace.steps:
            for flow in step.applied_flows:
                records.append(
                    _base_record(
                        run=run,
                        role=role.role,
                        sequence=sequence,
                        decision_index=step.decision_index,
                        event_type="external_flow",
                        event_time=flow.effective_time.isoformat(),
                        payload={
                            "flow_id": flow.flow_id,
                            "asset": flow.asset.key,
                            "quantity_delta": str(flow.quantity_delta),
                        },
                    )
                )
                sequence += 1

            target = step.decision.target
            records.append(
                _base_record(
                    run=run,
                    role=role.role,
                    sequence=sequence,
                    decision_index=step.decision_index,
                    event_type="policy_decision",
                    event_time=step.decision_time.isoformat(),
                    payload={
                        "decision_id": step.decision.decision_id,
                        "policy_id": step.decision.policy_id,
                        "reason": step.decision.reason.value,
                        "evidence_ids": list(step.decision.evidence_ids),
                        "current_weights": _state_weights(
                            run,
                            state=step.state_at_decision,
                            prices=step.price_snapshot.prices,
                        ),
                        "target_weights": (
                            None
                            if target is None
                            else {
                                asset.key: str(weight)
                                for asset, weight in target.weights.items()
                            }
                        ),
                    },
                )
            )
            sequence += 1

            if step.rebalance is not None:
                requested = step.rebalance.requested_plan
                selected = step.rebalance.selected_plan
                records.append(
                    _base_record(
                        run=run,
                        role=role.role,
                        sequence=sequence,
                        decision_index=step.decision_index,
                        event_type="rebalance",
                        event_time=step.decision_time.isoformat(),
                        payload={
                            "requested_one_way_notional": str(
                                requested.one_way_rebalance_notional
                            ),
                            "requested_quantity_deltas": _decimal_mapping(
                                requested.quantity_deltas
                            ),
                            "selected": selected is not None,
                            "selected_quantity_deltas": (
                                None
                                if selected is None
                                else _decimal_mapping(selected.quantity_deltas)
                            ),
                            "filter_reason": (
                                None
                                if step.rebalance.reason is None
                                else step.rebalance.reason.value
                            ),
                        },
                    )
                )
                sequence += 1

            if step.execution is not None or step.no_fill_reason is not None:
                records.append(
                    _base_record(
                        run=run,
                        role=role.role,
                        sequence=sequence,
                        decision_index=step.decision_index,
                        event_type="execution_outcome",
                        event_time=step.decision_time.isoformat(),
                        payload={
                            "executed": step.fill is not None,
                            "direct_reason": (
                                None
                                if step.execution is None
                                or step.execution.reason is None
                                else step.execution.reason.value
                            ),
                            "replay_reason": (
                                None
                                if step.no_fill_reason is None
                                else step.no_fill_reason.value
                            ),
                            "reference_time": (
                                None
                                if step.execution_reference_time is None
                                else step.execution_reference_time.isoformat()
                            ),
                            "reference_price": (
                                None
                                if step.execution_reference_price is None
                                else str(step.execution_reference_price)
                            ),
                        },
                    )
                )
                sequence += 1

            fill = step.fill
            if fill is not None:
                records.append(
                    _base_record(
                        run=run,
                        role=role.role,
                        sequence=sequence,
                        decision_index=step.decision_index,
                        event_type="fill",
                        event_time=fill.execution_timestamp.isoformat(),
                        payload={
                            "fill_id": fill.fill_id,
                            "decision_id": fill.decision_id,
                            "venue": fill.venue,
                            "venue_symbol": fill.venue_symbol,
                            "base": fill.base.key,
                            "quote": fill.quote.key,
                            "side": fill.side.value,
                            "reference_price": str(fill.reference_price),
                            "execution_price": str(fill.execution_price),
                            "base_quantity": str(fill.base_quantity),
                            "gross_quote_notional": str(fill.gross_quote_notional),
                            "fee_amount": str(fill.fee_amount),
                            "fee_asset": fill.fee_asset.key,
                            "slippage_value": str(fill.slippage_value),
                            "balance_deltas": _decimal_mapping(fill.balance_deltas),
                        },
                    )
                )
                sequence += 1
    return tuple(records)


def write_event_records(path: Path, run: ExperimentRun) -> None:
    lines = [
        json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        for record in build_event_records(run)
    ]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def read_event_records(path: Path, *, run_id: str) -> tuple[dict[str, Any], ...]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        raw: object = json.loads(line)
        if not isinstance(raw, dict):
            raise ValueError(f"event line {line_number} must be a JSON object")
        record = cast(dict[str, Any], raw)
        if record.get("schema_version") != _EVENT_SCHEMA:
            raise ValueError(f"event line {line_number} has unknown schema")
        if record.get("run_id") != run_id:
            raise ValueError(f"event line {line_number} has mismatched run_id")
        if record.get("sequence") != len(records):
            raise ValueError("event sequence must be contiguous and deterministic")
        records.append(record)
    return tuple(records)


__all__ = ["build_event_records", "read_event_records", "write_event_records"]
