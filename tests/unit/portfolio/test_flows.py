from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from qap.portfolio import AssetId, ExternalInventoryFlow

D = Decimal
BTC = AssetId("BTC")


def test_external_flow_exposes_one_exact_inventory_delta() -> None:
    flow = ExternalInventoryFlow(
        flow_id="deposit-1",
        effective_time=datetime(2024, 1, 1, tzinfo=timezone(timedelta(0))),
        asset=BTC,
        quantity_delta=D("0.2500"),
    )

    assert flow.flow_id == "deposit-1"
    assert flow.event_id == "deposit-1"
    assert flow.effective_time == datetime(2024, 1, 1, tzinfo=UTC)
    assert flow.quantity_delta == D("0.25")
    assert dict(flow.balance_deltas) == {BTC: D("0.25")}


@pytest.mark.parametrize(
    "quantity_delta",
    [D("0"), D("NaN"), D("Infinity")],
)
def test_external_flow_rejects_non_effective_quantity_delta(
    quantity_delta: Decimal,
) -> None:
    with pytest.raises(ValueError, match="quantity_delta"):
        ExternalInventoryFlow(
            flow_id="invalid-flow",
            effective_time=datetime(2024, 1, 1, tzinfo=UTC),
            asset=BTC,
            quantity_delta=quantity_delta,
        )


def test_external_flow_requires_utc_effective_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware UTC"):
        ExternalInventoryFlow(
            flow_id="naive-flow",
            effective_time=datetime(2024, 1, 1),
            asset=BTC,
            quantity_delta=D("1"),
        )
