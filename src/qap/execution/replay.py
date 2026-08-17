"""Deterministic point-in-time replay for one declared direct spot market."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol, cast, runtime_checkable

from qap.execution.costs import CostModel
from qap.execution.direct import DirectExecutionResult, execute_direct_rebalance_leg
from qap.execution.fills import ExecutionQuantization, Fill
from qap.market import (
    AlignedBarSeries,
    CompletedBarHistory,
    PriceSnapshot,
    VenueInstrument,
    validate_bar_series,
)
from qap.policy import (
    PolicyDecision,
    RebalanceFilterResult,
    build_rebalance_plan,
    filter_minimum_notional,
)
from qap.portfolio import (
    AssetId,
    ExternalInventoryFlow,
    PortfolioLedger,
    PortfolioState,
)
from qap.portfolio._decimal import divide

_ONE = Decimal("1")
EvidenceBuilder = Callable[[tuple[CompletedBarHistory, ...]], Iterable[str]]


@runtime_checkable
class ReplayPolicy(Protocol):
    """Structural policy boundary shared by replay and later controls/models."""

    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        price_snapshot: PriceSnapshot,
        applied_flows: tuple[ExternalInventoryFlow, ...],
        evidence_ids: Iterable[str] = (),
    ) -> PolicyDecision: ...


class ReplayNoFillReason(StrEnum):
    """Replay-level reason that cannot be represented by direct execution."""

    NO_NEXT_BAR = "no_next_bar"


@dataclass(frozen=True, slots=True)
class ReplayStep:
    """One causal decision boundary and its resulting inventory snapshot."""

    decision_index: int
    decision_time: datetime
    visible_timestamps: tuple[datetime, ...]
    applied_flows: tuple[ExternalInventoryFlow, ...]
    state_before_flows: PortfolioState
    state_at_decision: PortfolioState
    price_snapshot: PriceSnapshot
    valuation_price_snapshot: PriceSnapshot
    decision: PolicyDecision
    rebalance: RebalanceFilterResult | None
    execution: DirectExecutionResult | None
    no_fill_reason: ReplayNoFillReason | None
    execution_reference_time: datetime | None
    execution_reference_price: Decimal | None
    state_after: PortfolioState

    @property
    def fill(self) -> Fill | None:
        """Return the modeled fill when direct execution succeeded."""

        if self.execution is None:
            return None
        return self.execution.fill


@dataclass(frozen=True, slots=True)
class ReplayTrace:
    """Immutable deterministic replay artifact for one run configuration."""

    run_id: str
    starting_state: PortfolioState
    ending_state: PortfolioState
    steps: tuple[ReplayStep, ...]
    declared_flows: tuple[ExternalInventoryFlow, ...]
    unapplied_flows: tuple[ExternalInventoryFlow, ...]

    @property
    def fills(self) -> tuple[Fill, ...]:
        """Return fills in deterministic application order."""

        return tuple(step.fill for step in self.steps if step.fill is not None)

    @property
    def applied_flows(self) -> tuple[ExternalInventoryFlow, ...]:
        """Return external flows in deterministic application order."""

        return tuple(flow for step in self.steps for flow in step.applied_flows)


def _validated_run_id(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("run_id must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError("run_id must not be empty")
    return normalized


def _ordered_flows(
    values: Iterable[ExternalInventoryFlow],
) -> tuple[ExternalInventoryFlow, ...]:
    if not isinstance(cast(object, values), Iterable):
        raise TypeError("external_flows must be iterable")

    copied: list[ExternalInventoryFlow] = []
    for position, value in enumerate(cast(Iterable[object], values)):
        if not isinstance(value, ExternalInventoryFlow):
            raise TypeError(
                f"external flow at position {position} must be an ExternalInventoryFlow"
            )
        copied.append(value)

    # Python's sort is stable: chronological order is canonical while a
    # manifest's declared order remains authoritative for equal-time flows.
    ordered = tuple(sorted(copied, key=lambda item: item.effective_time))
    flow_ids = [flow.flow_id for flow in ordered]
    if len(set(flow_ids)) != len(flow_ids):
        raise ValueError("external flow IDs must be unique within one replay")
    return ordered


def _decision_price_snapshot(
    *,
    aligned: AlignedBarSeries,
    decision_index: int,
    decision_time: datetime,
    numeraire: AssetId,
) -> PriceSnapshot:
    prices: dict[AssetId, Decimal] = {numeraire: _ONE}

    for item in aligned.series:
        instrument = item.instrument
        close = Decimal(str(item.bars[decision_index].close))
        if instrument.quote == numeraire:
            priced_asset = instrument.base
            price = close
        elif instrument.base == numeraire:
            priced_asset = instrument.quote
            price = divide(_ONE, close)
        else:
            # Cross-market series may supply evidence or an explicit execution
            # reference, but they are never synthesized into valuation prices.
            continue
        if priced_asset in prices:
            raise ValueError(
                f"multiple aligned instruments price asset {priced_asset.key}"
            )
        prices[priced_asset] = price

    return PriceSnapshot.from_prices(
        timestamp=decision_time,
        numeraire=numeraire,
        prices=prices,
    )


def _valuation_price_snapshot(
    *,
    aligned: AlignedBarSeries,
    decision_index: int,
    decision_time: datetime,
    numeraire: AssetId,
) -> PriceSnapshot:
    """Mark post-decision inventory at the causal execution boundary.

    Non-final steps use the next contiguous bar open for every directly
    numeraire-priced asset, matching the timestamp and reference used by any
    modeled fill. The final step has no next bar and therefore uses the last
    completed close as the terminal mark.
    """

    has_next_bar = decision_index + 1 < len(aligned.timestamps)
    mark_index = decision_index + 1 if has_next_bar else decision_index
    prices: dict[AssetId, Decimal] = {numeraire: _ONE}

    for item in aligned.series:
        instrument = item.instrument
        bar = item.bars[mark_index]
        raw_price = bar.open if has_next_bar else bar.close
        mark = Decimal(str(raw_price))
        if instrument.quote == numeraire:
            priced_asset = instrument.base
            price = mark
        elif instrument.base == numeraire:
            priced_asset = instrument.quote
            price = divide(_ONE, mark)
        else:
            continue
        if priced_asset in prices:
            raise ValueError(
                f"multiple aligned instruments price asset {priced_asset.key}"
            )
        prices[priced_asset] = price

    return PriceSnapshot.from_prices(
        timestamp=decision_time,
        numeraire=numeraire,
        prices=prices,
    )


def _empty_evidence(
    histories: tuple[CompletedBarHistory, ...],
) -> tuple[str, ...]:
    del histories
    return ()


def run_deterministic_replay(
    *,
    run_id: str,
    aligned: AlignedBarSeries,
    ledger: PortfolioLedger,
    policy: ReplayPolicy,
    execution_instrument: VenueInstrument,
    numeraire: AssetId,
    cost_model: CostModel,
    min_rebalance_notional: Decimal,
    quantization: ExecutionQuantization = ExecutionQuantization(),
    external_flows: Iterable[ExternalInventoryFlow] = (),
    evidence_builder: EvidenceBuilder = _empty_evidence,
) -> ReplayTrace:
    """Replay completed-bar decisions with next-open execution references."""

    normalized_run_id = _validated_run_id(run_id)
    if not isinstance(cast(object, aligned), AlignedBarSeries):
        raise TypeError("aligned must be an AlignedBarSeries")
    if not isinstance(cast(object, ledger), PortfolioLedger):
        raise TypeError("ledger must be a PortfolioLedger")
    if not isinstance(cast(object, policy), ReplayPolicy):
        raise TypeError("policy must implement the ReplayPolicy contract")
    if not isinstance(cast(object, execution_instrument), VenueInstrument):
        raise TypeError("execution_instrument must be a VenueInstrument")
    if not isinstance(cast(object, numeraire), AssetId):
        raise TypeError("numeraire must be an AssetId")
    if not isinstance(cast(object, cost_model), CostModel):
        raise TypeError("cost_model must be a CostModel")
    if not isinstance(cast(object, min_rebalance_notional), Decimal):
        raise TypeError("min_rebalance_notional must be Decimal")
    if not min_rebalance_notional.is_finite() or min_rebalance_notional < Decimal("0"):
        raise ValueError("min_rebalance_notional must be finite and non-negative")
    if not isinstance(cast(object, quantization), ExecutionQuantization):
        raise TypeError("quantization must be an ExecutionQuantization")
    if not callable(evidence_builder):
        raise TypeError("evidence_builder must be callable")

    try:
        execution_series = aligned.for_instrument(execution_instrument)
    except KeyError as exc:
        raise ValueError(
            "execution instrument must be present exactly in aligned market data"
        ) from exc

    validated_series = tuple(validate_bar_series(item.bars) for item in aligned.series)
    declared_flows = _ordered_flows(external_flows)
    starting_state = ledger.current_state
    steps: list[ReplayStep] = []
    next_flow_index = 0

    for decision_index, candle_open_time in enumerate(aligned.timestamps):
        decision_time = candle_open_time + aligned.interval.duration
        state_before_flows = ledger.current_state
        applied_flows: list[ExternalInventoryFlow] = []
        while (
            next_flow_index < len(declared_flows)
            and declared_flows[next_flow_index].effective_time <= decision_time
        ):
            flow = declared_flows[next_flow_index]
            ledger.apply_flow(flow)
            applied_flows.append(flow)
            next_flow_index += 1
        state_at_decision = ledger.current_state
        price_snapshot = _decision_price_snapshot(
            aligned=aligned,
            decision_index=decision_index,
            decision_time=decision_time,
            numeraire=numeraire,
        )
        valuation_price_snapshot = _valuation_price_snapshot(
            aligned=aligned,
            decision_index=decision_index,
            decision_time=decision_time,
            numeraire=numeraire,
        )

        histories = tuple(
            series.history_through(decision_time) for series in validated_series
        )
        visible_timestamps = aligned.timestamps[: decision_index + 1]
        if any(history.timestamps != visible_timestamps for history in histories):
            raise ValueError("causal aligned histories disagree at decision time")
        evidence_ids = tuple(evidence_builder(histories))
        decision = policy.decide(
            as_of=decision_time,
            current_state=state_at_decision,
            price_snapshot=price_snapshot,
            applied_flows=tuple(applied_flows),
            evidence_ids=evidence_ids,
        )
        if not isinstance(cast(object, decision), PolicyDecision):
            raise TypeError("policy must return a PolicyDecision")
        if decision.as_of != decision_time:
            raise ValueError("policy decision time must match the replay boundary")
        if decision.current_state != state_at_decision:
            raise ValueError(
                "policy decision inventory snapshot must match the replay ledger"
            )

        rebalance: RebalanceFilterResult | None = None
        execution: DirectExecutionResult | None = None
        no_fill_reason: ReplayNoFillReason | None = None
        execution_reference_time: datetime | None = None
        execution_reference_price: Decimal | None = None

        if decision.target is not None:
            requested_plan = build_rebalance_plan(
                current_state=state_at_decision,
                target=decision.target,
                prices=price_snapshot,
            )
            rebalance = filter_minimum_notional(
                requested_plan,
                min_rebalance_notional,
            )

            selected_plan = rebalance.selected_plan
            if selected_plan is not None:
                if decision_index + 1 >= len(aligned.timestamps):
                    no_fill_reason = ReplayNoFillReason.NO_NEXT_BAR
                else:
                    next_bar = execution_series.bars[decision_index + 1]
                    if next_bar.candle_open_time != decision_time:
                        raise ValueError(
                            "next execution bar must be contiguous with decision time"
                        )
                    execution_reference_time = next_bar.candle_open_time
                    execution_reference_price = Decimal(str(next_bar.open))
                    execution = execute_direct_rebalance_leg(
                        fill_id=(f"{normalized_run_id}:{decision.decision_id}:leg-0"),
                        decision_id=decision.decision_id,
                        execution_timestamp=next_bar.candle_open_time,
                        instrument=execution_instrument,
                        quantity_deltas=selected_plan.quantity_deltas,
                        current_state=state_at_decision,
                        reference_price=execution_reference_price,
                        cost_model=cost_model,
                        quantization=quantization,
                    )
                    if execution.fill is not None:
                        ledger.apply_fill(execution.fill)

        steps.append(
            ReplayStep(
                decision_index=decision_index,
                decision_time=decision_time,
                visible_timestamps=visible_timestamps,
                applied_flows=tuple(applied_flows),
                state_before_flows=state_before_flows,
                state_at_decision=state_at_decision,
                price_snapshot=price_snapshot,
                valuation_price_snapshot=valuation_price_snapshot,
                decision=decision,
                rebalance=rebalance,
                execution=execution,
                no_fill_reason=no_fill_reason,
                execution_reference_time=execution_reference_time,
                execution_reference_price=execution_reference_price,
                state_after=ledger.current_state,
            )
        )

    return ReplayTrace(
        run_id=normalized_run_id,
        starting_state=starting_state,
        ending_state=ledger.current_state,
        steps=tuple(steps),
        declared_flows=declared_flows,
        unapplied_flows=declared_flows[next_flow_index:],
    )
