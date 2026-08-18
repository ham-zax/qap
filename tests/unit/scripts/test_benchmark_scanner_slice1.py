"""Regression coverage for the Scanner-V1 Slice-1 benchmark CLI contract."""

import json
import subprocess
import sys


def test_scanner_slice1_benchmark_tracks_current_frozen_protocol() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/benchmark_scanner_slice1.py",
            "--assets",
            "8",
            "--bars",
            "40",
            "--scout-sample",
            "4",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    [result] = payload["results"]

    assert result["assets"] == 8
    assert result["valid_pair_count"] == 28
    assert 0 < result["retained_edge_count"] <= result["valid_pair_count"]
    assert result["fixed_trial_count"] == result["retained_edge_count"] * 18
    assert result["scout_sample_count"] == 4
    assert result["automatic_replay_ceiling_all_horizons"] == 30
    assert result["peak_rss_kib"] > 0
    assert len(result["digest"]) == 64
