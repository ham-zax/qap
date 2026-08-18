from decimal import Decimal

import pytest

from qap.policy.graph_basket import (
    BasketGraphEdge,
    resolve_graph_target,
    update_edge_opinions,
)
from qap.portfolio import AllocationTarget, AssetId, PairOrientation
from qap.portfolio._decimal import divide, exact_add, exact_sum

A = AssetId("AAA")
B = AssetId("BBB")
C = AssetId("CCC")
D = AssetId("DDD")
E = AssetId("EEE")
F = AssetId("FFF")


def _edge(edge_id: str, left: AssetId, right: AssetId) -> BasketGraphEdge:
    asset_a, asset_b = sorted((left, right))
    return BasketGraphEdge(
        edge_id=edge_id,
        asset_a=asset_a,
        asset_b=asset_b,
        candidate_orientation=PairOrientation(base=left, quote=right),
    )


def _neutral(*assets: AssetId) -> AllocationTarget:
    weight = divide(Decimal("1"), Decimal(len(assets)))
    return AllocationTarget.for_basket(
        {asset: weight for asset in assets},
        basket=assets,
    )


def _weights(target: AllocationTarget) -> dict[str, Decimal]:
    return {asset.key: weight for asset, weight in target.weights.items()}


def test_edge_opinion_hysteresis_maps_candidate_orientation_and_fails_closed() -> None:
    edge = _edge("ab", A, B)

    entered = update_edge_opinions(
        (edge,),
        previous=None,
        scores={"ab": -2.0},
    )
    assert entered.complete is True
    assert entered.opinions == {"ab": 1}

    retained = update_edge_opinions(
        (edge,),
        previous=entered.opinions,
        scores={"ab": -1.0},
    )
    assert retained.opinions == {"ab": 1}

    missing = update_edge_opinions(
        (edge,),
        previous=retained.opinions,
        scores={"ab": None},
    )
    assert missing.complete is False
    assert missing.invalid_edge_ids == ("ab",)
    assert missing.opinions == retained.opinions

    neutral = update_edge_opinions(
        (edge,),
        previous=retained.opinions,
        scores={"ab": 0.5},
    )
    assert neutral.opinions == {"ab": 0}

    reverse = _edge("ba", B, A)
    reverse_entered = update_edge_opinions(
        (reverse,),
        previous=None,
        scores={"ba": -2.0},
    )
    assert reverse_entered.opinions == {"ba": -1}


def test_three_asset_chain_matches_hand_calculation_and_stays_long_only() -> None:
    target = resolve_graph_target(
        _neutral(A, B, C),
        (A, B, C),
        (_edge("ab", A, B), _edge("bc", B, C)),
        {"ab": 1, "bc": 1},
    )
    weights = _weights(target)
    neutral = divide(Decimal("1"), Decimal("3"))

    assert weights == {
        "AAA": exact_add(neutral, Decimal("0.10")),
        "BBB": neutral,
        "CCC": exact_add(neutral, Decimal("-0.10")),
    }
    assert all(weight > 0 for weight in weights.values())
    assert (exact_sum(weights.values()) - Decimal("1")).copy_abs() <= Decimal("1e-12")


def test_pure_cycle_is_neutral() -> None:
    target = resolve_graph_target(
        _neutral(A, B, C),
        (A, B, C),
        (
            _edge("ab", A, B),
            _edge("bc", B, C),
            _edge("ac", A, C),
        ),
        {"ab": 1, "bc": 1, "ac": -1},
    )
    neutral = divide(Decimal("1"), Decimal("3"))

    assert _weights(target) == {"AAA": neutral, "BBB": neutral, "CCC": neutral}


def test_disconnected_components_only_redistribute_their_own_neutral_capital() -> None:
    target = resolve_graph_target(
        _neutral(A, B, C, D),
        (A, B, C, D),
        (_edge("ab", A, B), _edge("cd", C, D)),
        {"ab": 1, "cd": -1},
    )
    weights = _weights(target)

    assert weights == {
        "AAA": Decimal("0.35"),
        "BBB": Decimal("0.15"),
        "CCC": Decimal("0.15"),
        "DDD": Decimal("0.35"),
    }
    assert exact_sum((weights["AAA"], weights["BBB"])) == Decimal("0.5")
    assert exact_sum((weights["CCC"], weights["DDD"])) == Decimal("0.5")


def test_declared_degree_counts_neutral_edges() -> None:
    with_neutral_edge = _weights(
        resolve_graph_target(
            _neutral(A, B, C),
            (A, B, C),
            (_edge("ab", A, B), _edge("bc", B, C)),
            {"ab": 1, "bc": 0},
        )
    )
    without_neutral_edge = _weights(
        resolve_graph_target(
            _neutral(A, B, C),
            (A, B, C),
            (_edge("ab", A, B),),
            {"ab": 1},
        )
    )

    assert with_neutral_edge != without_neutral_edge
    assert with_neutral_edge["BBB"] > without_neutral_edge["BBB"]


def test_two_asset_limit_reproduces_slice1_sixty_forty_target() -> None:
    target = resolve_graph_target(
        _neutral(A, B),
        (A, B),
        (_edge("ab", A, B),),
        {"ab": 1},
    )

    assert _weights(target) == {"AAA": Decimal("0.6"), "BBB": Decimal("0.4")}


@pytest.mark.parametrize(
    "assets",
    [
        (A, B, C),
        (A, B, C, D),
        (A, B, C, D, E),
        (A, B, C, D, E, F),
    ],
)
def test_supported_basket_sizes_stay_long_only_and_sum_to_one(
    assets: tuple[AssetId, ...],
) -> None:
    edges = tuple(
        _edge(f"edge-{index}", assets[index], assets[index + 1])
        for index in range(len(assets) - 1)
    )
    opinions = {edge.edge_id: 1 for edge in edges}

    target = resolve_graph_target(
        _neutral(*assets),
        assets,
        edges,
        opinions,
    )

    assert all(weight > 0 for weight in target.weights.values())
    assert (exact_sum(target.weights.values()) - Decimal("1")).copy_abs() <= Decimal(
        "1e-12"
    )


def test_resolver_rejects_duplicate_edges_invalid_opinions_and_non_neutral_target() -> (
    None
):
    first = _edge("ab-1", A, B)
    duplicate = _edge("ab-2", A, B)
    with pytest.raises(ValueError, match="one edge per pair"):
        resolve_graph_target(
            _neutral(A, B, C),
            (A, B, C),
            (first, duplicate),
            {"ab-1": 1, "ab-2": 1},
        )

    with pytest.raises(ValueError, match="-1, 0, or \\+1"):
        resolve_graph_target(
            _neutral(A, B, C),
            (A, B, C),
            (first,),
            {"ab-1": 2},
        )

    non_neutral = AllocationTarget.for_basket(
        {A: Decimal("0.4"), B: Decimal("0.3"), C: Decimal("0.3")},
        basket=(A, B, C),
    )
    with pytest.raises(ValueError, match="equal weight"):
        resolve_graph_target(
            non_neutral,
            (A, B, C),
            (first,),
            {"ab-1": 1},
        )
