# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
"""Thin wiring checks for the bounded prospective scanner CLI."""

import json
from pathlib import Path

import pytest

from qap.scanner import forward_cli


def _output(capsys: pytest.CaptureFixture[str]) -> dict[str, object]:
    return json.loads(capsys.readouterr().out)


def test_forward_cli_freeze_dispatches_and_emits_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        forward_cli,
        "freeze_scan_with_qap",
        lambda **_kwargs: Path("/tmp/cohort"),
    )
    assert (
        forward_cli.main(
            [
                "freeze",
                "--scan-id",
                "a" * 64,
                "--horizon",
                "short",
                "--freeze-at",
                "2026-08-18T00:00:00Z",
                "--data-root",
                "/tmp/data",
                "--run-root",
                "/tmp/runs",
                "--prospective-root",
                "/tmp/runs",
            ]
        )
        == 0
    )
    assert _output(capsys) == {"cohort_root": "/tmp/cohort"}


def test_forward_cli_advance_dispatches_and_emits_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(forward_cli, "load_scanner_catalog", lambda _path: object())
    monkeypatch.setattr(
        forward_cli,
        "advance_forward_with_qap",
        lambda **_kwargs: (Path("/tmp/cp"),),
    )
    assert (
        forward_cli.main(
            [
                "advance",
                "--cohort-root",
                "/tmp/cohort",
                "--through",
                "2026-08-18T01:00:00Z",
                "--data-root",
                "/tmp/data",
                "--run-root",
                "/tmp/runs",
                "--repository-root",
                "/tmp/repo",
            ]
        )
        == 0
    )
    assert _output(capsys) == {"checkpoint_directories": ["/tmp/cp"]}


def test_forward_cli_capture_dispatches_and_emits_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        forward_cli,
        "capture_public_spot",
        lambda **_kwargs: Path("/tmp/book.parquet"),
    )
    assert (
        forward_cli.main(
            [
                "capture",
                "--venue",
                "binance",
                "--symbol",
                "BTCETH",
                "--base",
                "BTC",
                "--quote",
                "ETH",
                "--kind",
                "depth",
                "--capture-root",
                "/tmp/capture",
            ]
        )
        == 0
    )
    assert _output(capsys) == {"capture_file": "/tmp/book.parquet"}


def test_forward_cli_qualify_dispatches_and_emits_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(forward_cli, "load_scanner_catalog", lambda _path: object())
    monkeypatch.setattr(
        forward_cli,
        "qualify_forward_with_qap",
        lambda **_kwargs: Path("/tmp/qualification"),
    )
    assert (
        forward_cli.main(
            [
                "qualify",
                "--cohort-root",
                "/tmp/cohort",
                "--checkpoint-id",
                "b" * 64,
                "--requested-capital",
                "100",
                "--data-root",
                "/tmp/data",
                "--capture-root",
                "/tmp/capture",
                "--run-root",
                "/tmp/runs",
                "--repository-root",
                "/tmp/repo",
            ]
        )
        == 0
    )
    assert _output(capsys) == {"qualification_directory": "/tmp/qualification"}


def test_forward_cli_show_dispatches_and_emits_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        forward_cli,
        "cohort_scoreboard",
        lambda _root: {"cohort_id": "c" * 64, "qualification_count": 0},
    )
    assert forward_cli.main(["show", "--cohort-root", "/tmp/cohort"]) == 0
    assert _output(capsys) == {
        "cohort_id": "c" * 64,
        "qualification_count": 0,
    }
