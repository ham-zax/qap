# pyright: reportPrivateUsage=false

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from qap.scanner.cli import _requested_horizons, _utc_timestamp, load_pins_file, main
from qap.scanner.protocol import ScannerHorizon
from qap.scanner.run import ScanRunResult


def test_scanner_cli_timestamp_requires_timezone_aware_utc() -> None:
    assert _utc_timestamp("2026-08-18T00:00:00Z") == datetime(2026, 8, 18, tzinfo=UTC)

    with pytest.raises(argparse.ArgumentTypeError, match="timezone-aware UTC"):
        _utc_timestamp("2026-08-18T00:00:00")
    with pytest.raises(argparse.ArgumentTypeError, match="timezone-aware UTC"):
        _utc_timestamp("2026-08-18T05:30:00+05:30")


def test_requested_horizons_expands_all_in_frozen_order() -> None:
    assert _requested_horizons("all") == (
        ScannerHorizon.SHORT,
        ScannerHorizon.MEDIUM,
        ScannerHorizon.SWING,
    )
    assert _requested_horizons("medium") == (ScannerHorizon.MEDIUM,)


def test_pins_file_normalizes_pair_venue_and_horizon_order(tmp_path: Path) -> None:
    path = tmp_path / "pins.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "qap.scanner.pins.v1",
                "pins": [
                    {
                        "venue": " BINANCE ",
                        "asset_a": "eth",
                        "asset_b": "btc",
                        "horizons": ["medium", "short"],
                        "forensic": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    pins = load_pins_file(path)

    assert len(pins) == 1
    pin = pins[0]
    assert pin.venue == "binance"
    assert (pin.asset_a, pin.asset_b) == ("BTC", "ETH")
    assert pin.horizons == (ScannerHorizon.SHORT, ScannerHorizon.MEDIUM)
    assert pin.forensic is False
    assert pin.semantic_tokens() == (
        "binance:BTC/ETH:short:official",
        "binance:BTC/ETH:medium:official",
    )


def test_pins_file_rejects_duplicate_normalized_pair_horizon(tmp_path: Path) -> None:
    path = tmp_path / "pins.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "qap.scanner.pins.v1",
                "pins": [
                    {
                        "venue": "binance",
                        "asset_a": "BTC",
                        "asset_b": "ETH",
                        "horizons": ["short"],
                        "forensic": False,
                    },
                    {
                        "venue": "BINANCE",
                        "asset_a": "eth",
                        "asset_b": "btc",
                        "horizons": ["short"],
                        "forensic": True,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate normalized pin"):
        load_pins_file(path)


def test_pins_file_rejects_unknown_venue_duplicate_horizon_and_extra_fields(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pins.json"
    base: dict[str, Any] = {
        "schema_version": "qap.scanner.pins.v1",
        "pins": [
            {
                "venue": "kraken",
                "asset_a": "BTC",
                "asset_b": "ETH",
                "horizons": ["short"],
                "forensic": False,
            }
        ],
    }
    path.write_text(json.dumps(base), encoding="utf-8")
    with pytest.raises(ValueError, match="venue"):
        load_pins_file(path)

    base["pins"][0]["venue"] = "binance"
    base["pins"][0]["horizons"] = ["short", "short"]
    path.write_text(json.dumps(base), encoding="utf-8")
    with pytest.raises(ValueError, match="horizons"):
        load_pins_file(path)

    base["pins"][0]["horizons"] = ["short"]
    base["pins"][0]["unexpected"] = True
    path.write_text(json.dumps(base), encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        load_pins_file(path)


def test_missing_pins_file_means_no_manual_inputs() -> None:
    assert load_pins_file(None) == ()


def test_cli_prints_bounded_json_summary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact = tmp_path / "runs" / "scans" / ("a" * 64)
    result = ScanRunResult(
        scan_id="a" * 64,
        artifact_directory=artifact,
        eligible_count=2,
        excluded_count=1,
        retained_edge_count=1,
        enumerated_trial_count=18,
        valid_trial_count=9,
        invalid_trial_count=9,
        automatic_promotion_count=2,
        budget_exclusion_count=7,
        replay_survivor_count=0,
        replay_failure_count=2,
    )

    import qap.scanner_entry as scanner_entry

    captured: dict[str, object] = {}

    def fake_run(**kwargs: object) -> ScanRunResult:
        captured.update(kwargs)
        return result

    monkeypatch.setattr(scanner_entry, "run_scan_with_qap", fake_run)
    status = main(
        [
            "--as-of",
            "2026-08-18T00:00:00Z",
            "--horizon",
            "short",
            "--data-root",
            str(tmp_path / "data"),
            "--run-root",
            str(tmp_path / "runs"),
            "--manual-replay-candidate-id",
            "b" * 64,
            "--manual-replay-candidate-id",
            "c" * 64,
        ]
    )

    assert status == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == result.summary_payload()
    assert captured["manual_replay_candidate_ids"] == ("b" * 64, "c" * 64)
    assert "success" not in payload
