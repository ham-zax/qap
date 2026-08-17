import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from qap.experiment import (
    ExperimentManifest,
    load_manifest,
    run_experiment_to_artifacts,
)

REPOSITORY_ROOT = Path(__file__).parents[3]
BASE_MANIFEST = REPOSITORY_ROOT / "tests/fixtures/experiments/two_asset_dummy.json"
ETH_FINGERPRINT = "6b8937160dfe5d523e06937cb2c175934487b59fd77605b439e8bad7b1a79426"
RUN_TIMESTAMP = datetime(2026, 8, 17, 6, 0, tzinfo=UTC)


@pytest.fixture
def populated_run_root(tmp_path: Path) -> tuple[Path, str]:
    run_root = tmp_path / "runs"
    manifest = load_manifest(BASE_MANIFEST)
    paths = run_experiment_to_artifacts(
        manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_root=run_root,
        run_timestamp=RUN_TIMESTAMP,
    )
    return run_root, paths.run_id


@pytest.fixture
def model_evidence_run_root(tmp_path: Path) -> tuple[Path, str]:
    raw = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
    raw.update(
        {
            "experiment_name": "rolling evidence API fixture",
            "research_family_id": "family-api-model-evidence-v1",
            "relationship": {
                "component_id": "rolling_log_ratio_zscore",
                "config": {
                    "base_asset": "BTC",
                    "quote_asset": "USDT",
                    "window_bars": 3,
                    "min_observations": 3,
                },
            },
            "policy": {
                "component_id": "evidence_tilt",
                "config": {
                    "base_asset": "BTC",
                    "quote_asset": "USDT",
                    "neutral_weights": {"BTC": "0.5", "USDT": "0.5"},
                    "neutral_threshold": "0",
                    "enter_threshold": "0.000001",
                    "maximum_tilt": "0.1",
                    "neutral_mode": "neutral_target",
                },
            },
        }
    )
    manifest = ExperimentManifest.model_validate(raw)
    run_root = tmp_path / "model-evidence-runs"
    paths = run_experiment_to_artifacts(
        manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_root=run_root,
        run_timestamp=RUN_TIMESTAMP,
    )
    return run_root, paths.run_id


@pytest.fixture
def final_oos_run_root(tmp_path: Path) -> tuple[Path, str]:
    raw = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
    raw.update(
        {
            "experiment_name": "final OOS API fixture",
            "research_family_id": "family-api-final-oos-v1",
            "data_role": "final_oos",
        }
    )
    manifest = ExperimentManifest.model_validate(raw)
    run_root = tmp_path / "final-oos-runs"
    paths = run_experiment_to_artifacts(
        manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_root=run_root,
        run_timestamp=RUN_TIMESTAMP,
    )
    return run_root, paths.run_id


@pytest.fixture
def pair_run_root(tmp_path: Path) -> tuple[Path, str]:
    raw = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
    raw.update(
        {
            "experiment_name": "three-asset API fixture",
            "research_family_id": "family-api-pairs-v1",
            "basket": ["BTC", "ETH", "USDT"],
            "starting_quantities": {"BTC": "1", "ETH": "10", "USDT": "1000"},
            "external_flows": [],
            "policy": {"component_id": "scheduled_target", "config": {"schedule": []}},
            "benchmarks": {
                "relationship_alpha_claim": False,
                "primary_incremental_benchmark": None,
                "controls": [],
            },
            "primary_metric": "hodl_relative_terminal_wealth",
            "analysis_anchor": "USDT",
        }
    )
    raw["instruments"] = [
        raw["instruments"][0],
        {
            "instrument_id": "eth-usdt",
            "venue": "fixture",
            "venue_symbol": "ETHUSDT",
            "base_asset": "ETH",
            "quote_asset": "USDT",
        },
    ]
    raw["data_sources"] = [
        raw["data_sources"][0],
        {
            "dataset_id": "fixture-ethusdt-1h",
            "instrument_id": "eth-usdt",
            "relative_path": "tests/fixtures/market/ETHUSDT_1h.csv",
            "expected_semantic_fingerprint": ETH_FINGERPRINT,
        },
    ]
    manifest = ExperimentManifest.model_validate(raw)
    run_root = tmp_path / "pair-runs"
    paths = run_experiment_to_artifacts(
        manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_root=run_root,
        run_timestamp=RUN_TIMESTAMP,
    )
    return run_root, paths.run_id
