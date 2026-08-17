# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false

import json
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from qap.experiment import load_manifest
from qap.experiment.artifacts import (
    ArtifactError,
    read_run_artifacts,
    run_experiment_to_artifacts,
)
from qap.experiment.integrity import ArtifactIntegrity, build_integrity_record

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPOSITORY_ROOT / "tests/fixtures/experiments/two_asset_dummy.json"
RUN_AT = datetime(2026, 8, 17, 6, 0, tzinfo=UTC)


def _completed_run(tmp_path: Path) -> Path:
    paths = run_experiment_to_artifacts(
        load_manifest(MANIFEST_PATH),
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_root=tmp_path,
        run_timestamp=RUN_AT,
    )
    return paths.run_directory


def test_reader_rejects_tampered_result_content(tmp_path: Path) -> None:
    run_directory = _completed_run(tmp_path)
    result_path = run_directory / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["strategy_vs_hodl"] = "999"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(ArtifactError, match="integrity"):
        read_run_artifacts(run_directory)


def _rewrite_integrity(run_directory: Path) -> None:
    integrity_path = run_directory / "integrity.json"
    current = ArtifactIntegrity.model_validate_json(
        integrity_path.read_text(encoding="utf-8")
    )
    rewritten = build_integrity_record(
        run_directory,
        artifact_id=current.artifact_id,
        file_names=tuple(current.files),
    )
    integrity_path.write_text(
        rewritten.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )


def _tamper_performance(run_directory: Path) -> None:
    performance_path = run_directory / "performance.parquet"
    table = pq.read_table(performance_path)
    column_name = "relative::strategy_vs_hodl"
    values = table.column(column_name).to_pylist()
    values[-1] = "999"
    column_index = table.schema.get_field_index(column_name)
    tampered = table.set_column(
        column_index,
        column_name,
        pa.array(values, type=pa.string()),
    )
    pq.write_table(tampered, performance_path, compression="zstd", version="2.6")


def test_reader_rejects_tampered_performance_content(tmp_path: Path) -> None:
    run_directory = _completed_run(tmp_path)
    _tamper_performance(run_directory)

    with pytest.raises(ArtifactError, match="integrity"):
        read_run_artifacts(run_directory)


def test_reader_rejects_semantically_inconsistent_result_with_fresh_digests(
    tmp_path: Path,
) -> None:
    run_directory = _completed_run(tmp_path)
    result_path = run_directory / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["strategy_vs_hodl"] = "999"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    _rewrite_integrity(run_directory)

    with pytest.raises(ArtifactError, match="semantic"):
        read_run_artifacts(run_directory)


def test_reader_rejects_semantically_inconsistent_performance_with_fresh_digests(
    tmp_path: Path,
) -> None:
    run_directory = _completed_run(tmp_path)
    _tamper_performance(run_directory)
    _rewrite_integrity(run_directory)

    with pytest.raises(ArtifactError, match="semantic"):
        read_run_artifacts(run_directory)
