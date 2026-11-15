"""Snapshots retain their exact original evidence while pins remain reversible."""

import json
from pathlib import Path

import pytest

from qap.product_lab_store import LabStoreError, LabStudyStore, content_id


def result(value: int) -> dict[str, object]:
    return {
        "analysis": {
            "coin_a": {"code": "A"},
            "coin_b": {"code": "B"},
            "data_through": "2026-10-01T00:00:00Z",
        },
        "requested_settings": {"method": "zscore"},
        "call": {"headline": "No reliable edge"},
        "value": value,
    }


def test_saved_result_and_pins_preserve_original_bytes(tmp_path: Path) -> None:
    store = LabStudyStore(tmp_path)
    first = store.save(result(1))
    identifier = first["study_id"]
    original = (store.root / "studies" / identifier / "result.json").read_bytes()
    assert store.save(result(1))["study_id"] == identifier
    second = store.save(result(2))
    assert second["study_id"] != identifier
    assert store.set_pin(identifier, True)["pinned"]
    assert store.read(identifier)["result"]["value"] == 1
    assert not store.set_pin(identifier, False)["pinned"]
    assert (
        store.root / "studies" / identifier / "result.json"
    ).read_bytes() == original
    assert len(store.list()) == 2


def test_trials_count_unique_settings_and_expose_validation_reuse(
    tmp_path: Path,
) -> None:
    store = LabStudyStore(tmp_path)
    family = store.family_id("binance:A", "binance:B")
    assert family == store.family_id("binance:B", "binance:A")
    with store.family_lock(family):
        assert store.register_trials(
            family,
            [{"entry": 2}],
            validation_start="2026-01-01",
            validation_end="2026-03-01",
        ) == (1, False)
        assert store.register_trials(
            family,
            [{"entry": 2}],
            validation_start="2026-01-01",
            validation_end="2026-03-01",
        ) == (1, False)
        assert store.register_trials(
            family,
            [{"entry": 3}],
            validation_start="2026-01-01",
            validation_end="2026-03-01",
        ) == (2, True)


def test_snapshot_tampering_and_bad_identifiers_fail_closed(tmp_path: Path) -> None:
    store = LabStudyStore(tmp_path)
    identifier = store.save(result(1))["study_id"]
    path = store.root / "studies" / identifier / "result.json"
    value = json.loads(path.read_bytes())
    value["result"]["value"] = 100
    path.write_text(json.dumps(value))
    with pytest.raises(LabStoreError):
        store.read(identifier)
    with pytest.raises(LabStoreError):
        store.read("../outside")


def test_shifted_windows_retain_reuse_without_counting_settings_again(
    tmp_path: Path,
) -> None:
    store = LabStudyStore(tmp_path)
    family = store.family_id("binance:A", "binance:B")
    configuration = {"entry": 2}
    with store.family_lock(family):
        for start, end, reused in (
            ("2026-01-01", "2026-03-01", False),
            ("2026-01-02", "2026-03-02", True),
            # This window overlaps the second window but not the first.
            ("2026-03-01", "2026-04-01", True),
            ("2026-03-01", "2026-04-01", True),
            ("2026-05-01", "2026-06-01", False),
            ("2026-06-01", "2026-07-01", False),
        ):
            assert store.register_trials(
                family,
                [configuration],
                validation_start=start,
                validation_end=end,
            ) == (1, reused)
    state = json.loads((store.root / "families" / family / "trials.json").read_text())
    row = state["trials"][content_id(configuration)]
    assert row["validation_start"] == "2026-01-01"
    assert row["validation_end"] == "2026-03-01"
    assert len(row["validation_windows"]) == 5


def test_adding_settings_to_a_batch_preserves_reuse_on_exact_retry(
    tmp_path: Path,
) -> None:
    store = LabStudyStore(tmp_path)
    family = store.family_id("binance:A", "binance:B")
    window = {"validation_start": "2026-01-01", "validation_end": "2026-03-01"}
    with store.family_lock(family):
        assert store.register_trials(family, [{"entry": 2}], **window) == (1, False)
        for _ in range(2):
            assert store.register_trials(
                family, [{"entry": 2}, {"entry": 3}], **window
            ) == (2, True)


def test_legacy_trial_retains_original_evidence_when_history_is_added(
    tmp_path: Path,
) -> None:
    store = LabStudyStore(tmp_path)
    family = store.family_id("binance:A", "binance:B")
    configuration = {"entry": 2}
    original = {
        "configuration": configuration,
        "validation_start": "2026-01-01",
        "validation_end": "2026-03-01",
        "first_seen": "2026-03-01T00:00:00+00:00",
    }
    path = store.root / "families" / family / "trials.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "qap.lab.trials.v1",
                "trials": {content_id(configuration): original},
            }
        )
    )
    with store.family_lock(family):
        assert store.register_trials(
            family,
            [configuration],
            validation_start="2026-01-02",
            validation_end="2026-03-02",
        ) == (1, True)
    row = json.loads(path.read_text())["trials"][content_id(configuration)]
    assert {key: row[key] for key in original} == original
    assert len(row["validation_windows"]) == 2


@pytest.mark.parametrize(
    "history",
    [
        None,
        {},
        [None],
        [{"validation_start": "2026-01-01"}],
        [{"validation_start": 1, "validation_end": 2}],
        [{"validation_start": "2026-03-01", "validation_end": "2026-02-01"}],
        [
            {
                "validation_start": "2026-01-01",
                "validation_end": "2026-03-01",
                "reused": "false",
            }
        ],
    ],
)
def test_invalid_window_history_is_preserved_and_rejected(
    tmp_path: Path, history: object
) -> None:
    store = LabStudyStore(tmp_path)
    family = store.family_id("binance:A", "binance:B")
    configuration = {"entry": 2}
    path = store.root / "families" / family / "trials.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "qap.lab.trials.v1",
                "trials": {
                    content_id(configuration): {
                        "configuration": configuration,
                        "validation_start": "2026-01-01",
                        "validation_end": "2026-03-01",
                        "first_seen": "2026-03-01T00:00:00+00:00",
                        "validation_windows": history,
                    }
                },
            }
        )
    )
    original = path.read_bytes()
    with store.family_lock(family), pytest.raises(LabStoreError):
        store.register_trials(
            family,
            [configuration],
            validation_start="2026-01-02",
            validation_end="2026-03-02",
        )
    assert path.read_bytes() == original
