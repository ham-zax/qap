from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from qap.scanner.artifacts import (
    ReplayAttemptStatus,
    enumerate_replay_attempt,
    publish_scan_generation,
    start_scan_generation,
    transition_replay_attempt,
    write_scan_tables,
)
from qap.scanner.basket import (
    BasketDefinition,
    BasketDefinitionError,
    BasketEdge,
    build_basket_definition_from_scan,
)
from qap.scanner.basket_artifacts import (
    BasketArtifactError,
    BasketReplayStatus,
    publish_basket_generation,
    read_basket_generation,
    start_basket_generation,
    transition_basket_attempt,
)
from qap.scanner.catalog import (
    ScannerCatalog,
    ScannerSourceSpec,
    catalog_semantic_identity,
)
from qap.scanner.graph import GraphMetadataRecord, NeighborRecord
from qap.scanner.models import ScanDefinition, ScanInputIdentity
from qap.scanner.promotion import PromotionRecord, PromotionStatus
from qap.scanner.protocol import (
    SCANNER_V1_SLICE1,
    ScannerHorizon,
    TemplateId,
    protocol_identity,
)
from qap.scanner.scout import ScoutTrialRecord, ScoutTrialStatus
from qap.scanner.trials import ScannerModelFamily
from qap.scanner.universe import EligibleAssetRecord, HistoricalEligibilityState

NOW = datetime(2026, 8, 19, tzinfo=UTC)
SCAN_ID = "a" * 64


def _edge(
    candidate: str,
    asset_a: str,
    asset_b: str,
    *,
    venue: str = "binance",
    horizon: ScannerHorizon = ScannerHorizon.SHORT,
    resolution: str = "1h",
    deep_replay_status: str | None = "completed",
    deep_replay_failure_reason: str | None = None,
    deep_replay_run_id: str | None = "run-1",
    economic_gate_status: str | None = "deep_replay_survivor",
) -> BasketEdge:
    first, second = sorted((asset_a, asset_b))
    return BasketEdge(
        candidate_id=candidate * 64,
        scan_id=SCAN_ID,
        venue=venue,
        horizon=horizon,
        pair_id=f"{first}/{second}",
        asset_a=first,
        asset_b=second,
        candidate_orientation=f"{asset_a}/{asset_b}",
        resolution=resolution,
        model_family=ScannerModelFamily.LOG_RATIO_MEAN_REVERSION,
        template_id=TemplateId.FAST,
        scout_status="valid",
        automatic_neighbor_selected=True,
        manual_pinned=False,
        automatic_selected=True,
        deep_replay_status=deep_replay_status,
        deep_replay_failure_reason=deep_replay_failure_reason,
        deep_replay_run_id=deep_replay_run_id,
        economic_gate_status=economic_gate_status,
    )


def _definition(
    *,
    assets: tuple[str, ...] = ("AAA", "BBB", "CCC"),
    edges: tuple[BasketEdge, ...] | None = None,
    venue: str = "binance",
    horizon: ScannerHorizon = ScannerHorizon.SHORT,
    resolution: str = "1h",
    forensic_assets: tuple[str, ...] = (),
    created_at: datetime = NOW,
) -> BasketDefinition:
    selected = edges or (_edge("b", "AAA", "BBB"),)
    return BasketDefinition(
        source_scan_id=SCAN_ID,
        source_as_of=NOW - timedelta(days=1),
        venue=venue,
        horizon=horizon,
        decision_resolution=resolution,
        economic_assets=assets,
        selected_edges=selected,
        execution_dataset_ids=tuple((asset, f"{asset}-usdt") for asset in assets),
        forensic_assets=forensic_assets,
        created_at=created_at,
    )


def _source_catalog() -> ScannerCatalog:
    return ScannerCatalog(
        schema_version="qap.scanner.catalog.v1",
        lifecycle_evidence_relative_path="lifecycle.jsonl",
        sources=tuple(
            ScannerSourceSpec(
                dataset_id=f"{asset.lower()}-1h",
                relative_path=f"{asset.lower()}-1h.parquet",
                venue="binance",
                venue_symbol=f"{asset}USDT",
                base_asset=asset,
                quote_asset="USDT",
                interval="1h",
                expected_semantic_fingerprint=fingerprint * 64,
            )
            for asset, fingerprint in (("AAA", "1"), ("BBB", "2"), ("CCC", "3"))
        ),
    )


def _source_scan(
    tmp_path: Path,
    *,
    forensic_asset: str | None = None,
) -> tuple[Path, ScannerCatalog, str]:
    catalog = _source_catalog()
    definition = ScanDefinition(
        scanner_protocol_version=SCANNER_V1_SLICE1.protocol_id,
        protocol_identity=protocol_identity(SCANNER_V1_SLICE1),
        catalog_identity=catalog_semantic_identity(catalog),
        universe_policy_version=SCANNER_V1_SLICE1.universe_policy_version,
        candidate_generator_version=SCANNER_V1_SLICE1.candidate_generator_version,
        template_set_version=SCANNER_V1_SLICE1.template_set_version,
        promotion_policy_version=SCANNER_V1_SLICE1.promotion_policy_version,
        cost_policy_reference=SCANNER_V1_SLICE1.cost_policy.policy_id,
        as_of=NOW - timedelta(days=1),
        eligible_information_end=NOW - timedelta(days=1),
        venues=("binance",),
        horizons=(ScannerHorizon.SHORT,),
        input_slices=tuple(
            ScanInputIdentity(
                dataset_id=f"{asset.lower()}-1h",
                source_artifact_fingerprint=source * 64,
                selection_slice_fingerprint=selected * 64,
            )
            for asset, source, selected in (
                ("AAA", "1", "4"),
                ("BBB", "2", "5"),
                ("CCC", "3", "6"),
            )
        ),
        created_at=NOW - timedelta(days=1),
    )
    generation = start_scan_generation(tmp_path, definition)
    eligible: list[EligibleAssetRecord] = []
    for asset, source, selected in (
        ("AAA", "1", "4"),
        ("BBB", "2", "5"),
        ("CCC", "3", "6"),
    ):
        forensic = asset == forensic_asset
        eligible.append(
            EligibleAssetRecord(
                scan_id=definition.scan_id,
                venue="binance",
                horizon=ScannerHorizon.SHORT,
                asset_id=asset,
                venue_symbol=f"{asset}USDT",
                eligibility_state=(
                    HistoricalEligibilityState.HISTORICAL_ELIGIBILITY_UNKNOWN
                    if forensic
                    else HistoricalEligibilityState.KNOWN_ELIGIBLE
                ),
                eligibility_reason=(
                    "insufficient_historical_state_evidence"
                    if forensic
                    else "eligible_through_required_window"
                ),
                lifecycle_evidence_refs=(f"{asset}-listing",),
                source_artifact_fingerprint=source * 64,
                selection_slice_fingerprint=selected * 64,
                bar_coverage=1.0,
                longest_missing_run=0,
                automatic_eligible=not forensic,
                forensic_research_allowed=forensic,
            )
        )
    candidate_id = "b" * 64
    neighbor = NeighborRecord(
        scan_id=definition.scan_id,
        venue="binance",
        horizon="short",
        pair_id="AAA/BBB",
        asset_a="AAA",
        asset_b="BBB",
        ssd_distance=0.01,
        rank_from_a=1,
        rank_from_b=1,
        selected_by_a=True,
        selected_by_b=True,
        automatic_neighbor_selected=True,
        manual_pinned=False,
    )
    scout = ScoutTrialRecord(
        candidate_id=candidate_id,
        scan_id=definition.scan_id,
        venue="binance",
        horizon="short",
        pair_id="AAA/BBB",
        orientation="AAA/BBB",
        resolution="1h",
        model_family="log_ratio_mean_reversion",
        template_id="fast",
        trial_status=ScoutTrialStatus.VALID,
        failure_reason=None,
        scout_relative_wealth_proxy=0.01,
        scout_turnover_proxy=0.1,
        signal_count=2,
        automatic_neighbor_selected=True,
        manual_pinned=False,
    )
    promotion = PromotionRecord(
        candidate_id=candidate_id,
        promotion_rank=1,
        promotion_status=PromotionStatus.AUTOMATIC_PROMOTED,
        budget_reason=None,
        automatic_selected=True,
        manual_selected=False,
        selected_for_replay=True,
        deep_replay_status="setup_failed",
    )
    horizon_protocol = SCANNER_V1_SLICE1.horizon(ScannerHorizon.SHORT)
    graph_metadata = GraphMetadataRecord(
        scan_id=definition.scan_id,
        venue="binance",
        horizon="short",
        universe_snapshot_id="7" * 64,
        generator_version=definition.candidate_generator_version,
        graph_interval=horizon_protocol.graph_interval.label,
        graph_window_seconds=int(horizon_protocol.graph_window.total_seconds()),
        neighbors_per_asset=SCANNER_V1_SLICE1.neighbors_per_asset,
        minimum_pair_coverage=SCANNER_V1_SLICE1.minimum_pair_coverage,
        maximum_missing_generator_bars=SCANNER_V1_SLICE1.maximum_missing_generator_bars,
        eligible_asset_count=sum(item.automatic_eligible for item in eligible),
        total_valid_pair_comparisons=1,
        input_selection_slice_fingerprints=tuple(
            item.selection_slice_fingerprint
            for item in eligible
            if item.automatic_eligible
        ),
        distance_digest="8" * 64,
    )
    write_scan_tables(
        generation,
        eligible_assets=tuple(eligible),
        graph_metadata=(graph_metadata,),
        neighbors=(neighbor,),
        scout_trials=(scout,),
        promotions=(promotion,),
    )
    attempt = enumerate_replay_attempt(generation, promotion)
    transition_replay_attempt(
        generation,
        attempt.attempt_id,
        status=ReplayAttemptStatus.SETUP_FAILED,
        failure_stage="direct_market_resolution",
        failure_reason="unsupported_direct_market",
    )
    return publish_scan_generation(generation), catalog, candidate_id


def test_basket_definition_enforces_asset_and_edge_scope() -> None:
    with pytest.raises(ValidationError, match="3-6"):
        _definition(assets=("AAA", "BBB"))
    with pytest.raises(ValidationError, match="3-6"):
        _definition(assets=("AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG"))
    with pytest.raises(ValidationError, match="venue/horizon"):
        _definition(edges=(_edge("b", "AAA", "BBB", venue="gate"),))
    with pytest.raises(ValidationError, match="resolution"):
        _definition(edges=(_edge("b", "AAA", "BBB", resolution="15m"),))
    with pytest.raises(ValidationError, match="belong to basket"):
        _definition(edges=(_edge("b", "AAA", "DDD"),))
    with pytest.raises(ValidationError, match="one candidate"):
        _definition(
            edges=(
                _edge("b", "AAA", "BBB"),
                _edge("c", "BBB", "AAA"),
            )
        )


def test_basket_definition_accepts_scout_only_indirect_and_rejects_failures() -> None:
    indirect = _edge(
        "b",
        "AAA",
        "BBB",
        deep_replay_status="setup_failed",
        deep_replay_failure_reason="unsupported_direct_market",
        deep_replay_run_id=None,
        economic_gate_status=None,
    )
    assert _definition(edges=(indirect,)).selected_edges == (indirect,)

    with pytest.raises(ValidationError, match="unsupported_direct_market"):
        _edge(
            "c",
            "AAA",
            "BBB",
            deep_replay_status="setup_failed",
            deep_replay_failure_reason="source_fingerprint_mismatch",
            deep_replay_run_id=None,
            economic_gate_status=None,
        )
    with pytest.raises(ValidationError, match="not basket evidence"):
        _edge(
            "d",
            "AAA",
            "BBB",
            deep_replay_status="replay_failed",
            deep_replay_failure_reason="data_admission_failed",
            deep_replay_run_id=None,
            economic_gate_status=None,
        )


def test_build_basket_from_completed_scan_accepts_indirect_and_propagates_forensic(
    tmp_path: Path,
) -> None:
    source_scan, catalog, candidate_id = _source_scan(
        tmp_path / "source",
        forensic_asset="CCC",
    )

    basket = build_basket_definition_from_scan(
        source_scan,
        catalog,
        venue="binance",
        horizon=ScannerHorizon.SHORT,
        decision_resolution="1h",
        economic_assets=("AAA", "BBB", "CCC"),
        candidate_ids=(candidate_id,),
        created_at=NOW,
    )

    assert basket.forensic
    assert basket.forensic_assets == ("CCC",)
    assert dict(basket.execution_dataset_ids) == {
        "AAA": "aaa-1h",
        "BBB": "bbb-1h",
        "CCC": "ccc-1h",
    }
    assert basket.selected_edges[0].deep_replay_status == "setup_failed"
    assert (
        basket.selected_edges[0].deep_replay_failure_reason
        == "unsupported_direct_market"
    )


def test_build_basket_rejects_tampered_source_scan(tmp_path: Path) -> None:
    source_scan, catalog, candidate_id = _source_scan(tmp_path / "source")
    (source_scan / "scout_trials.parquet").write_bytes(b"tampered")

    with pytest.raises(BasketDefinitionError, match="integrity/provenance"):
        build_basket_definition_from_scan(
            source_scan,
            catalog,
            venue="binance",
            horizon=ScannerHorizon.SHORT,
            decision_resolution="1h",
            economic_assets=("AAA", "BBB", "CCC"),
            candidate_ids=(candidate_id,),
            created_at=NOW,
        )


def test_basket_identity_excludes_creation_time_and_groups_manual_siblings() -> None:
    first = _definition(created_at=NOW)
    later = _definition(created_at=NOW + timedelta(hours=1))
    sibling = _definition(
        assets=("AAA", "BBB", "DDD"),
        edges=(_edge("c", "AAA", "BBB"),),
    )

    assert first.basket_id == later.basket_id
    assert first.research_family_id == later.research_family_id
    assert first.basket_id != sibling.basket_id
    assert first.research_family_id == sibling.research_family_id


def test_forensic_assets_make_basket_forensic() -> None:
    basket = _definition(forensic_assets=("AAA",))

    assert basket.forensic is True
    assert basket.forensic_assets == ("AAA",)


def test_basket_setup_failure_is_durably_attributable_before_qap(
    tmp_path: Path,
) -> None:
    definition = _definition()
    generation = start_basket_generation(tmp_path, definition)

    attempt = transition_basket_attempt(
        generation,
        status=BasketReplayStatus.SETUP_FAILED,
        failure_stage="experiment_preparation",
        failure_reason="missing_execution_route",
    )
    directory = publish_basket_generation(generation)
    stored, stored_attempt, manifest = read_basket_generation(directory)

    assert stored == definition
    assert stored_attempt == attempt
    assert stored_attempt.status is BasketReplayStatus.SETUP_FAILED
    assert manifest["qap_run_id"] is None


def test_basket_artifact_is_immutable_and_integrity_protected(tmp_path: Path) -> None:
    definition = _definition()
    generation = start_basket_generation(tmp_path, definition)
    transition_basket_attempt(
        generation,
        status=BasketReplayStatus.REPLAY_FAILED,
        failure_stage="qap_replay",
        failure_reason="candidate_specific_failure",
    )
    directory = publish_basket_generation(generation)
    (directory / "unexpected.txt").write_text("x", encoding="utf-8")

    with pytest.raises(BasketArtifactError, match="file set mismatch"):
        read_basket_generation(directory)
