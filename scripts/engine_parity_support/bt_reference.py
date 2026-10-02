"""Independent spot accounting through bt; no imports of QAP state or execution."""

import importlib
from collections.abc import Callable, Mapping
from typing import Protocol, cast

from scripts.engine_parity_support.contracts import (
    Outcome,
    PairInputs,
    Settings,
    Strategy,
    target_weight,
)


class Security(Protocol):
    @property
    def position(self) -> float: ...
    def transact(self, q: float, *, price: float | None = None) -> None: ...


class BtStrategy(Protocol):
    @property
    def capital(self) -> float: ...
    @property
    def children(self) -> Mapping[str, Security]: ...
    def use_integer_positions(self, enabled: bool) -> None: ...
    def setup(self, frame: object, *, bidoffer: object) -> None: ...
    def update(self, date: object) -> None: ...
    def adjust(self, amount: float) -> None: ...
    def transact(self, q: float, *, child: str) -> None: ...
    def set_commissions(self, fn: Callable[[float, float], float]) -> None: ...


class BtModule(Protocol):
    def Strategy(self, name: str) -> BtStrategy: ...


class PandasModule(Protocol):
    def DataFrame(
        self, data: Mapping[str, list[float]], *, index: object
    ) -> object: ...
    def to_datetime(self, values: object, *, utc: bool) -> object: ...


def sell_owned(security: Security, requested: float, price: float) -> int:
    """Prevent bt's broader short-selling action space from entering this test."""
    quantity = min(requested, security.position)
    if quantity <= 0:
        return 0
    before = security.position
    security.transact(-quantity, price=price)
    return int(security.position != before)


def initialize(inputs: PairInputs, settings: Settings) -> BtStrategy:
    """Seed already-owned inventory without charging a fictitious acquisition fee."""
    bt = cast(BtModule, importlib.import_module("bt"))
    pd = cast(PandasModule, importlib.import_module("pandas"))
    frame = pd.DataFrame(
        {
            asset: [row[i] for row in inputs.opens]
            for i, asset in enumerate(inputs.assets)
        },
        index=pd.to_datetime(inputs.dates, utc=True),
    )
    engine = bt.Strategy("independent-spot-reference")
    engine.use_integer_positions(False)
    # bt requires bid-offer tracking to book explicit next-open fill prices.
    # Zero spread enables that accounting; adverse slippage is passed per trade.
    spread = pd.DataFrame(
        {asset: [0.0] * len(inputs.dates) for asset in inputs.assets},
        index=pd.to_datetime(inputs.dates, utc=True),
    )
    engine.setup(frame, bidoffer=spread)
    engine.update(inputs.dates[0])
    quantities = tuple(
        settings.starting_value / 2 / price for price in inputs.closes[0]
    )
    engine.adjust(sum(q * p for q, p in zip(quantities, inputs.opens[0], strict=True)))
    for asset, quantity in zip(inputs.assets, quantities, strict=True):
        engine.transact(quantity, child=asset)
    engine.set_commissions(lambda q, p: abs(q) * p * settings.fee_rate)
    return engine


def run_reference(
    inputs: PairInputs, strategy: Strategy, settings: Settings
) -> Outcome:
    engine = initialize(inputs, settings)
    ratios = tuple(a / b for a, b in inputs.closes)
    legs = 0
    for index, prices in enumerate(inputs.closes[:-1]):
        quantities = tuple(engine.children[asset].position for asset in inputs.assets)
        values = tuple(q * p for q, p in zip(quantities, prices, strict=True))
        total = sum(values) + engine.capital
        weight = target_weight(strategy, index, values[0], total, ratios, settings)
        if weight is None:
            continue
        weights = (weight, 1 - weight)
        deltas = tuple(
            total * w / p - q
            for w, p, q in zip(
                weights,
                prices,
                quantities,
                strict=True,
            )
        )
        # QAP's minimum is half the total absolute target value change,
        # including the zero-weight settlement coordinate.
        notional = (
            sum(abs(d * p) for d, p in zip(deltas, prices, strict=True))
            + abs(engine.capital)
        ) / 2
        if notional < settings.minimum_notional:
            continue
        engine.update(inputs.dates[index + 1])
        ordering = sorted(
            range(2), key=lambda i: (-abs(deltas[i] * prices[i]), inputs.assets[i])
        )
        for i in ordering:
            if deltas[i] >= 0:
                continue
            security = engine.children[inputs.assets[i]]
            legs += sell_owned(
                security,
                -deltas[i],
                inputs.opens[index + 1][i] * (1 - settings.slippage_rate),
            )
        for i in ordering:
            if deltas[i] <= 0:
                continue
            budget = min(deltas[i] * prices[i], engine.capital)
            if budget <= 0:
                continue
            price = inputs.opens[index + 1][i] * (1 + settings.slippage_rate)
            quantity = budget / (price * (1 + settings.fee_rate))
            security = engine.children[inputs.assets[i]]
            before = security.position
            security.transact(quantity, price=price)
            legs += int(security.position != before)
        if engine.capital < -1e-8 or any(
            s.position < -1e-12 for s in engine.children.values()
        ):
            raise ArithmeticError("Reference engine attempted unowned inventory")
    quantities = tuple(engine.children[asset].position for asset in inputs.assets)
    holdings = (quantities[0], quantities[1])
    terminal = (
        sum(q * p for q, p in zip(holdings, inputs.closes[-1], strict=True))
        + engine.capital
    )
    return Outcome(terminal, legs, holdings, engine.capital)
