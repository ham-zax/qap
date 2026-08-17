import json
from pathlib import Path

import pytest

from qap.experiment.integrity import ArtifactIntegrity, build_integrity_record
from qap.experiment.paper_operation import (
    read_paper_operation_artifact,
    run_paper_operation_to_artifact,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SPEC = REPOSITORY_ROOT / "tests/fixtures/paper/four_asset_forward_paper.json"


def _operation(tmp_path: Path) -> Path:
    paths = run_paper_operation_to_artifact(
        SPEC,
        repository_root=REPOSITORY_ROOT,
        output_root=tmp_path / "paper-operations",
    )
    return paths.operation_file


def _refresh_integrity(operation_file: Path) -> None:
    integrity_file = operation_file.parent / "integrity.json"
    current = ArtifactIntegrity.model_validate_json(
        integrity_file.read_text(encoding="utf-8")
    )
    refreshed = build_integrity_record(
        operation_file.parent,
        artifact_id=current.artifact_id,
        file_names=tuple(current.files),
    )
    integrity_file.write_text(
        refreshed.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )


def test_paper_reader_rejects_tampered_reconciliation_totals(tmp_path: Path) -> None:
    operation_file = _operation(tmp_path)
    record = json.loads(operation_file.read_text(encoding="utf-8"))
    record["total_fee_quote"] = "999999"
    record["reconciliation"]["reported_fee_total"] = "999999"
    record["reconciliation"]["recomputed_fee_total"] = "999999"
    record["reconciliation"]["matches"] = True
    operation_file.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="integrity"):
        read_paper_operation_artifact(operation_file)


def test_paper_reader_rejects_semantic_tamper_with_fresh_digest(tmp_path: Path) -> None:
    operation_file = _operation(tmp_path)
    record = json.loads(operation_file.read_text(encoding="utf-8"))
    record["total_fee_quote"] = "999999"
    record["reconciliation"]["reported_fee_total"] = "999999"
    record["reconciliation"]["recomputed_fee_total"] = "999999"
    record["reconciliation"]["matches"] = True
    operation_file.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    _refresh_integrity(operation_file)

    with pytest.raises(ValueError, match="semantic"):
        read_paper_operation_artifact(operation_file)
