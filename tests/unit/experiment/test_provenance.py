import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from qap.experiment.manifest import ExperimentManifest
from qap.experiment.provenance import (
    DatasetFingerprint,
    canonical_manifest_bytes,
    capture_run_provenance,
    code_fingerprint,
    deterministic_run_id,
    manifest_sha256,
)


def _valid_manifest_data() -> dict[str, object]:
    value = json.loads(
        Path("tests/fixtures/experiments/two_asset_dummy.json").read_text(
            encoding="utf-8"
        )
    )
    if not isinstance(value, dict):
        raise TypeError("manifest fixture must contain one JSON object")
    return cast(dict[str, object], value)


def _write_code_tree(root: Path, *, source: str = "VALUE = 1\n") -> None:
    package = root / "src" / "qap"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(source, encoding="utf-8")
    (package / "__pycache__").mkdir()
    (package / "__pycache__" / "ignored.pyc").write_bytes(b"ignored")
    (root / "pyproject.toml").write_text("[project]\nname='qap'\n", encoding="utf-8")
    (root / "uv.lock").write_text("version = 1\n", encoding="utf-8")


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=QAP Test",
            "-c",
            "user.email=qap@example.invalid",
            "commit",
            "-q",
            "-m",
            "fixture",
        ],
        check=True,
    )


def test_manifest_hash_is_canonical_and_sensitive_to_authoritative_values() -> None:
    first_data = _valid_manifest_data()
    second_data = dict(reversed(tuple(first_data.items())))
    first = ExperimentManifest.model_validate(first_data)
    second = ExperimentManifest.model_validate(second_data)

    assert canonical_manifest_bytes(first) == canonical_manifest_bytes(second)
    assert manifest_sha256(first) == manifest_sha256(second)
    assert json.loads(canonical_manifest_bytes(first))["starting_quantities"] == {
        "BTC": "1",
        "USDT": "1000",
    }

    changed_data = _valid_manifest_data()
    changed_data["success_threshold"] = "0.0001"
    changed = ExperimentManifest.model_validate(changed_data)
    assert manifest_sha256(changed) != manifest_sha256(first)


def test_code_fingerprint_is_path_ordered_and_sensitive_to_source_bytes(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write_code_tree(first)
    _write_code_tree(second)

    assert code_fingerprint(first) == code_fingerprint(second)

    (second / "src" / "qap" / "__init__.py").write_text(
        "VALUE = 2\n",
        encoding="utf-8",
    )
    assert code_fingerprint(first) != code_fingerprint(second)


def test_run_id_depends_on_manifest_data_and_code_but_not_wall_clock() -> None:
    manifest_hash = "1" * 64
    data = (
        DatasetFingerprint(dataset_id="a", fingerprint="2" * 64),
        DatasetFingerprint(dataset_id="b", fingerprint="3" * 64),
    )

    first = deterministic_run_id(
        manifest_sha256=manifest_hash,
        data_fingerprints=data,
        code_fingerprint="4" * 64,
    )
    second = deterministic_run_id(
        manifest_sha256=manifest_hash,
        data_fingerprints=data,
        code_fingerprint="4" * 64,
    )

    assert first == second
    assert first.startswith("run-")
    assert first != deterministic_run_id(
        manifest_sha256=manifest_hash,
        data_fingerprints=data,
        code_fingerprint="5" * 64,
    )


def test_capture_provenance_records_git_state_without_using_it_in_run_id(
    tmp_path: Path,
) -> None:
    _write_code_tree(tmp_path)
    _init_git_repo(tmp_path)
    manifest = ExperimentManifest.model_validate(_valid_manifest_data())
    fingerprints = (
        DatasetFingerprint(
            dataset_id=manifest.data_sources[0].dataset_id,
            fingerprint=manifest.data_sources[0].expected_semantic_fingerprint,
        ),
    )
    timestamp = datetime(2026, 8, 17, 6, 0, tzinfo=UTC)

    clean = capture_run_provenance(
        manifest=manifest,
        data_fingerprints=fingerprints,
        repository_root=tmp_path,
        run_timestamp=timestamp,
    )
    (tmp_path / "src" / "qap" / "__init__.py").write_text(
        "VALUE = 99\n",
        encoding="utf-8",
    )
    dirty = capture_run_provenance(
        manifest=manifest,
        data_fingerprints=fingerprints,
        repository_root=tmp_path,
        run_timestamp=timestamp,
    )

    assert clean.git_dirty is False
    assert dirty.git_dirty is True
    assert clean.git_commit == dirty.git_commit
    assert clean.run_timestamp_utc == timestamp
    assert clean.data_role == manifest.data_role
    assert clean.research_family_id == manifest.research_family_id
    assert clean.code_fingerprint != dirty.code_fingerprint
    assert clean.run_id != dirty.run_id
