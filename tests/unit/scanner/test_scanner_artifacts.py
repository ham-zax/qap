# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from qap.scanner.artifacts import (
    ReplayAttemptStatus,
    ScanArtifactError,
    ScanArtifactGeneration,
    discover_completed_scans,
    enumerate_replay_attempt,
    publish_scan_generation,
    start_scan_generation,
    transition_replay_attempt,
    write_scan_tables,
)
from qap.scanner.graph import GraphMetadataRecord, NeighborRecord
from qap.scanner.models import ScanDefinition, ScanInputIdentity
from qap.scanner.promotion import PromotionRecord, PromotionStatus
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon, protocol_identity
from qap.scanner.scout import ScoutTrialRecord, ScoutTrialStatus
from qap.scanner.universe import EligibleAssetRecord, HistoricalEligibilityState

NOW = datetime(2026, 8, 18, tzinfo=UTC)


def _definition(
    *,
    source_fingerprint: str = "1" * 64,
    slice_fingerprint: str = "2" * 64,
    created_at: datetime = NOW,
) -> ScanDefinition:
    return ScanDefinition(
        scanner_protocol_version=SCANNER_V1_SLICE1.protocol_id,
        protocol_identity=protocol_identity(SCANNER_V1_SLICE1),
        catalog_identity="c" * 64,
        universe_policy_version=SCANNER_V1_SLICE1.universe_policy_version,
        candidate_generator_version=SCANNER_V1_SLICE1.candidate_generator_version,
        template_set_version=SCANNER_V1_SLICE1.template_set_version,
        promotion_policy_version=SCANNER_V1_SLICE1.promotion_policy_version,
        cost_policy_reference=SCANNER_V1_SLICE1.cost_policy.policy_id,
        as_of=NOW,
        eligible_information_end=NOW,
        venues=("binance",),
        horizons=(ScannerHorizon.SHORT,),
        input_slices=(
            ScanInputIdentity(
                dataset_id="btc-1h",
                source_artifact_fingerprint=source_fingerprint,
                selection_slice_fingerprint=slice_fingerprint,
            ),
        ),
        created_at=created_at,
    )


def _eligible(definition: ScanDefinition) -> EligibleAssetRecord:
    return EligibleAssetRecord(
        scan_id=definition.scan_id,
        venue="binance",
        horizon=ScannerHorizon.SHORT,
        asset_id="BTC",
        venue_symbol="BTCUSDT",
        eligibility_state=HistoricalEligibilityState.KNOWN_ELIGIBLE,
        eligibility_reason="covered_active_window",
        lifecycle_evidence_refs=("event-1",),
        source_artifact_fingerprint="1" * 64,
        selection_slice_fingerprint="2" * 64,
        bar_coverage=1.0,
        longest_missing_run=0,
        automatic_eligible=True,
        forensic_research_allowed=False,
    )


def _graph_metadata(definition: ScanDefinition) -> GraphMetadataRecord:
    horizon = SCANNER_V1_SLICE1.horizon(ScannerHorizon.SHORT)
    return GraphMetadataRecord(
        scan_id=definition.scan_id,
        venue="binance",
        horizon="short",
        universe_snapshot_id="b" * 64,
        generator_version=definition.candidate_generator_version,
        graph_interval=horizon.graph_interval.label,
        graph_window_seconds=int(horizon.graph_window.total_seconds()),
        neighbors_per_asset=SCANNER_V1_SLICE1.neighbors_per_asset,
        minimum_pair_coverage=SCANNER_V1_SLICE1.minimum_pair_coverage,
        maximum_missing_generator_bars=(
            SCANNER_V1_SLICE1.maximum_missing_generator_bars
        ),
        eligible_asset_count=1,
        total_valid_pair_comparisons=0,
        input_selection_slice_fingerprints=("2" * 64,),
        distance_digest="d" * 64,
    )


def _neighbor(definition: ScanDefinition) -> NeighborRecord:
    return NeighborRecord(
        scan_id=definition.scan_id,
        venue="binance",
        horizon="short",
        pair_id="BTC/ETH",
        asset_a="BTC",
        asset_b="ETH",
        ssd_distance=0.01,
        rank_from_a=1,
        rank_from_b=1,
        selected_by_a=True,
        selected_by_b=True,
        automatic_neighbor_selected=True,
        manual_pinned=False,
    )


def _scout(
    definition: ScanDefinition, candidate_id: str = "c" * 64
) -> ScoutTrialRecord:
    return ScoutTrialRecord(
        candidate_id=candidate_id,
        scan_id=definition.scan_id,
        venue="binance",
        horizon="short",
        pair_id="BTC/ETH",
        orientation="ETH/BTC",
        resolution="1h",
        model_family="residual_mean_reversion",
        template_id="fast",
        trial_status=ScoutTrialStatus.VALID,
        failure_reason=None,
        scout_relative_wealth_proxy=-0.01,
        scout_turnover_proxy=0.2,
        signal_count=3,
        automatic_neighbor_selected=True,
        manual_pinned=False,
    )


def _promotion(candidate_id: str = "c" * 64) -> PromotionRecord:
    return PromotionRecord(
        candidate_id=candidate_id,
        promotion_rank=1,
        promotion_status=PromotionStatus.AUTOMATIC_PROMOTED,
        budget_reason=None,
        automatic_selected=True,
        manual_selected=False,
        selected_for_replay=True,
    )


def _write_required_tables(
    generation: ScanArtifactGeneration, definition: ScanDefinition
) -> None:
    write_scan_tables(
        generation,
        eligible_assets=(_eligible(definition),),
        graph_metadata=(_graph_metadata(definition),),
        neighbors=(_neighbor(definition),),
        scout_trials=(_scout(definition),),
        promotions=(_promotion(),),
    )


def test_scanner_start_writes_immutable_definition_first_and_partial_is_not_complete(
    tmp_path: Path,
) -> None:
    definition = _definition()
    generation = start_scan_generation(tmp_path, definition)

    assert generation.staging_directory.name == f"{definition.scan_id}.partial"
    assert generation.definition_path.is_file()
    assert json.loads(generation.definition_path.read_text())[
        "scanner_protocol_version"
    ] == ("scanner-v1-s1")
    assert discover_completed_scans(tmp_path) == ()


def test_scan_tables_use_explicit_schemas_and_replay_attempts_starts_empty(
    tmp_path: Path,
) -> None:
    definition = _definition()
    generation = start_scan_generation(tmp_path, definition)
    _write_required_tables(generation, definition)

    expected = {
        "eligible_assets.parquet",
        "graph_metadata.parquet",
        "neighbors.parquet",
        "scout_trials.parquet",
        "promotions.parquet",
        "replay_attempts.parquet",
    }
    assert {
        path.name for path in generation.staging_directory.glob("*.parquet")
    } == expected
    replay = pq.read_table(generation.replay_attempts_path)
    assert replay.num_rows == 0
    assert replay.schema.names == [
        "attempt_id",
        "scan_id",
        "candidate_id",
        "promotion_rank",
        "attempt_status",
        "failure_stage",
        "failure_reason",
        "deep_replay_run_id",
    ]


def test_replay_attempt_requires_persisted_selected_promotion(tmp_path: Path) -> None:
    definition = _definition()
    generation = start_scan_generation(tmp_path, definition)
    write_scan_tables(
        generation,
        eligible_assets=(_eligible(definition),),
        graph_metadata=(_graph_metadata(definition),),
        neighbors=(_neighbor(definition),),
        scout_trials=(_scout(definition),),
        promotions=(),
    )

    with pytest.raises(ScanArtifactError, match="persisted selected promotion"):
        enumerate_replay_attempt(generation, _promotion())


def test_replay_attempt_is_durable_before_transition_and_updates_same_row(
    tmp_path: Path,
) -> None:
    definition = _definition()
    generation = start_scan_generation(tmp_path, definition)
    _write_required_tables(generation, definition)
    promotion = _promotion()

    enumerated = enumerate_replay_attempt(generation, promotion)
    first = pq.read_table(generation.replay_attempts_path).to_pylist()
    assert first == [
        {
            "attempt_id": enumerated.attempt_id,
            "scan_id": definition.scan_id,
            "candidate_id": promotion.candidate_id,
            "promotion_rank": 1,
            "attempt_status": "enumerated",
            "failure_stage": None,
            "failure_reason": None,
            "deep_replay_run_id": None,
        }
    ]

    completed = transition_replay_attempt(
        generation,
        enumerated.attempt_id,
        status=ReplayAttemptStatus.SETUP_FAILED,
        failure_stage="direct_market_resolution",
        failure_reason="unsupported_direct_market",
    )
    second = pq.read_table(generation.replay_attempts_path).to_pylist()
    assert completed.attempt_id == enumerated.attempt_id
    assert len(second) == 1
    assert second[0]["attempt_status"] == "setup_failed"
    assert second[0]["failure_reason"] == "unsupported_direct_market"


def test_publish_reconciles_completed_promotion_outcome_with_attempt(
    tmp_path: Path,
) -> None:
    definition = _definition()
    generation = start_scan_generation(tmp_path, definition)
    promotion = replace(
        _promotion(),
        direct_execution_instrument_id="btc-eth-1h",
        deep_replay_run_id="run-123",
        deep_replay_status="completed",
        economic_gate_status="deep_replay_rejected",
    )
    write_scan_tables(
        generation,
        eligible_assets=(_eligible(definition),),
        graph_metadata=(_graph_metadata(definition),),
        neighbors=(_neighbor(definition),),
        scout_trials=(_scout(definition),),
        promotions=(promotion,),
    )
    attempt = enumerate_replay_attempt(generation, promotion)
    transition_replay_attempt(
        generation,
        attempt.attempt_id,
        status=ReplayAttemptStatus.COMPLETED,
        deep_replay_run_id="run-123",
    )

    final_directory = publish_scan_generation(generation)

    row = pq.read_table(final_directory / "promotions.parquet").to_pylist()[0]
    assert row["direct_execution_instrument_id"] == "btc-eth-1h"
    assert row["deep_replay_run_id"] == "run-123"
    assert row["deep_replay_status"] == "completed"
    assert row["economic_gate_status"] == "deep_replay_rejected"


def test_publish_rejects_promotion_attempt_run_id_mismatch(tmp_path: Path) -> None:
    definition = _definition()
    generation = start_scan_generation(tmp_path, definition)
    promotion = replace(
        _promotion(),
        direct_execution_instrument_id="btc-eth-1h",
        deep_replay_run_id="promotion-run",
        deep_replay_status="completed",
        economic_gate_status="deep_replay_survivor",
    )
    write_scan_tables(
        generation,
        eligible_assets=(_eligible(definition),),
        graph_metadata=(_graph_metadata(definition),),
        neighbors=(_neighbor(definition),),
        scout_trials=(_scout(definition),),
        promotions=(promotion,),
    )
    attempt = enumerate_replay_attempt(generation, promotion)
    transition_replay_attempt(
        generation,
        attempt.attempt_id,
        status=ReplayAttemptStatus.COMPLETED,
        deep_replay_run_id="attempt-run",
    )

    with pytest.raises(ScanArtifactError, match="promotion replay outcome"):
        publish_scan_generation(generation)


def test_publish_rejects_frozen_source_or_slice_identity_not_bound_in_definition(
    tmp_path: Path,
) -> None:
    definition = _definition()
    generation = start_scan_generation(tmp_path, definition)
    mismatched = replace(
        _eligible(definition),
        source_artifact_fingerprint="f" * 64,
    )
    write_scan_tables(
        generation,
        eligible_assets=(mismatched,),
        graph_metadata=(_graph_metadata(definition),),
        neighbors=(_neighbor(definition),),
        scout_trials=(_scout(definition),),
        promotions=(),
    )

    with pytest.raises(ScanArtifactError, match="frozen source/slice identity"):
        publish_scan_generation(generation)


def test_publish_reconciles_promotions_against_attempts_before_atomic_rename(
    tmp_path: Path,
) -> None:
    definition = _definition()
    generation = start_scan_generation(tmp_path, definition)
    _write_required_tables(generation, definition)

    with pytest.raises(ScanArtifactError, match="selected promotion.*replay attempt"):
        publish_scan_generation(generation)

    attempt = enumerate_replay_attempt(generation, _promotion())
    transition_replay_attempt(
        generation,
        attempt.attempt_id,
        status=ReplayAttemptStatus.SETUP_FAILED,
        failure_stage="direct_market_resolution",
        failure_reason="unsupported_direct_market",
    )
    write_scan_tables(
        generation,
        eligible_assets=(_eligible(definition),),
        graph_metadata=(_graph_metadata(definition),),
        neighbors=(_neighbor(definition),),
        scout_trials=(_scout(definition),),
        promotions=(replace(_promotion(), deep_replay_status="setup_failed"),),
    )
    final_directory = publish_scan_generation(generation)

    assert final_directory.name == definition.scan_id
    assert not generation.staging_directory.exists()
    manifest = json.loads((final_directory / "manifest.json").read_text())
    assert manifest["scan_id"] == definition.scan_id
    assert manifest["table_counts"]["promotions.parquet"] == 1
    assert manifest["table_counts"]["replay_attempts.parquet"] == 1
    assert manifest["replay_attempt_status_counts"] == {"setup_failed": 1}
    assert discover_completed_scans(tmp_path) == (final_directory,)


def test_resume_accepts_created_at_change_but_rejects_tampered_frozen_definition(
    tmp_path: Path,
) -> None:
    definition = _definition()
    generation = start_scan_generation(tmp_path, definition)
    resumed = start_scan_generation(
        tmp_path,
        _definition(created_at=datetime(2026, 8, 18, 1, tzinfo=UTC)),
    )
    assert resumed.staging_directory == generation.staging_directory
    assert resumed.definition.created_at == definition.created_at

    payload = json.loads(generation.definition_path.read_text())
    payload["input_slices"][0]["source_artifact_fingerprint"] = "f" * 64
    generation.definition_path.write_text(json.dumps(payload, sort_keys=True))
    with pytest.raises(ScanArtifactError, match="partial scan definition mismatch"):
        start_scan_generation(tmp_path, definition)


def test_completed_scan_is_immutable_and_duplicate_publication_is_rejected(
    tmp_path: Path,
) -> None:
    definition = _definition()
    generation = start_scan_generation(tmp_path, definition)
    _write_required_tables(generation, definition)
    attempt = enumerate_replay_attempt(generation, _promotion())
    transition_replay_attempt(
        generation,
        attempt.attempt_id,
        status=ReplayAttemptStatus.REPLAY_FAILED,
        failure_stage="authoritative_replay",
        failure_reason="fixture_failure",
    )
    write_scan_tables(
        generation,
        eligible_assets=(_eligible(definition),),
        graph_metadata=(_graph_metadata(definition),),
        neighbors=(_neighbor(definition),),
        scout_trials=(_scout(definition),),
        promotions=(
            replace(
                _promotion(),
                direct_execution_instrument_id="btc-eth-1h",
                deep_replay_status="replay_failed",
            ),
        ),
    )
    final_directory = publish_scan_generation(generation)

    with pytest.raises(ScanArtifactError, match="completed scan already exists"):
        start_scan_generation(tmp_path, definition)
    assert final_directory.is_dir()


def test_publish_rejects_undeclared_physical_artifact(tmp_path: Path) -> None:
    definition = _definition()
    generation = start_scan_generation(tmp_path, definition)
    write_scan_tables(
        generation,
        eligible_assets=(_eligible(definition),),
        graph_metadata=(_graph_metadata(definition),),
        neighbors=(_neighbor(definition),),
        scout_trials=(_scout(definition),),
        promotions=(),
    )
    (generation.staging_directory / "undeclared-authoritative.parquet").write_bytes(
        b"not-authoritative"
    )

    with pytest.raises(ScanArtifactError, match="file set"):
        publish_scan_generation(generation)


def test_completed_scan_discovery_rejects_missing_or_tampered_files(
    tmp_path: Path,
) -> None:
    definition = _definition()
    generation = start_scan_generation(tmp_path, definition)
    write_scan_tables(
        generation,
        eligible_assets=(_eligible(definition),),
        graph_metadata=(_graph_metadata(definition),),
        neighbors=(_neighbor(definition),),
        scout_trials=(_scout(definition),),
        promotions=(),
    )
    final_directory = publish_scan_generation(generation)
    assert (final_directory / "integrity.json").is_file()

    scout_path = final_directory / "scout_trials.parquet"
    original = scout_path.read_bytes()
    scout_path.write_bytes(original + b"tamper")
    with pytest.raises(ScanArtifactError, match="digest"):
        discover_completed_scans(tmp_path)

    scout_path.write_bytes(original)
    scout_path.unlink()
    with pytest.raises(ScanArtifactError, match="file set"):
        discover_completed_scans(tmp_path)
