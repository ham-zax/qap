from decimal import Decimal

from qap.policy.graph_basket import (
    BasketGraphEdge,
    resolve_graph_target,
    update_edge_opinions,
)
from qap.portfolio import AssetId, PairOrientation
from qap.portfolio._decimal import divide, exact_add, exact_sum

A = AssetId("AAA")
B = AssetId("BBB")
C = AssetId("CCC")
D = AssetId("DDD")


def _edge(edge_id: str, left: AssetId, right: AssetId) -> BasketGraphEdge:
    asset_a, asset_b = sorted((left, right))
    return BasketGraphEdge(
        edge_id=edge_id,
        asset_a=asset_a,
        asset_b=asset_b,
        candidate_orientation=PairOrientation(base=left, quote=right),
    )


def _weights(target: object) -> dict[str, Decimal]:
    return {asset.key: weight for asset, weight in target.weights.items()}  # type: ignore[attr-defined]


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
            (A, B, C),
            (_edge("ab", A, B), _edge("bc", B, C)),
            {"ab": 1, "bc": 0},
        )
    )
    without_neutral_edge = _weights(
        resolve_graph_target(
            (A, B, C),
            (_edge("ab", A, B),),
            {"ab": 1},
        )
    )

    assert with_neutral_edge != without_neutral_edge
    assert with_neutral_edge["BBB"] > without_neutral_edge["BBB"]


def test_two_asset_limit_reproduces_slice1_sixty_forty_target() -> None:
    target = resolve_graph_target(
        (A, B),
        (_edge("ab", A, B),),
        {"ab": 1},
    )

    assert _weights(target) == {"AAA": Decimal("0.6"), "BBB": Decimal("0.4")}
