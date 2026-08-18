"""Deterministic local performance benchmark for Scanner-V1 Slice 1."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import resource
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np

from qap.market import BarInterval
from qap.portfolio import AssetId, PairOrientation
from qap.scanner.graph import normalized_log_ssd
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon, TemplateId
from qap.scanner.scout import run_scout_trial
from qap.scanner.trials import ScannerModelFamily, ScannerTrial


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    assets: int
    bars: int
    source_slice_seconds: float
    ssd_seconds: float
    valid_pair_count: int
    retained_edge_count: int
    fixed_trial_count: int
    trial_enumeration_seconds: float
    scout_sample_count: int
    scout_sample_seconds: float
    projected_full_scout_seconds: float
    automatic_replay_ceiling_all_horizons: int
    peak_rss_kib: int
    digest: str

    def payload(self) -> dict[str, object]:
        return {
            "assets": self.assets,
            "bars": self.bars,
            "source_slice_seconds": self.source_slice_seconds,
            "ssd_seconds": self.ssd_seconds,
            "valid_pair_count": self.valid_pair_count,
            "retained_edge_count": self.retained_edge_count,
            "fixed_trial_count": self.fixed_trial_count,
            "trial_enumeration_seconds": self.trial_enumeration_seconds,
            "scout_sample_count": self.scout_sample_count,
            "scout_sample_seconds": self.scout_sample_seconds,
            "projected_full_scout_seconds": self.projected_full_scout_seconds,
            "automatic_replay_ceiling_all_horizons": (
                self.automatic_replay_ceiling_all_horizons
            ),
            "peak_rss_kib": self.peak_rss_kib,
            "digest": self.digest,
        }


def _paths(*, assets: int, bars: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    common = np.cumsum(rng.normal(0.0, 0.002, size=bars))
    idiosyncratic = np.cumsum(
        rng.normal(0.0, 0.001, size=(assets, bars)),
        axis=1,
    )
    levels = np.linspace(10.0, 1000.0, num=assets, dtype=np.float64)[:, None]
    return levels * np.exp(common[None, :] + idiosyncratic)


def _top_k_graph(
    selected: np.ndarray,
    *,
    k: int,
) -> tuple[int, int, str]:
    assets = selected.shape[0]
    peers: list[list[tuple[float, int]]] = [[] for _ in range(assets)]
    digest = hashlib.sha256()
    pair_count = 0
    for left in range(assets):
        left_values = selected[left]
        for right in range(left + 1, assets):
            distance = normalized_log_ssd(left_values, selected[right])
            peers[left].append((distance, right))
            peers[right].append((distance, left))
            digest.update(f"{left:05d}/{right:05d}:{distance.hex()}\n".encode("ascii"))
            pair_count += 1

    directed: set[tuple[int, int]] = set()
    for asset, ranked in enumerate(peers):
        ranked.sort(key=lambda item: (item[0], item[1]))
        for _distance, peer in ranked[:k]:
            directed.add((min(asset, peer), max(asset, peer)))
    return pair_count, len(directed), digest.hexdigest()


def _fixed_trials(edge_count: int) -> list[tuple[int, str, str, str]]:
    rows: list[tuple[int, str, str, str]] = []
    for edge in range(edge_count):
        for resolution in ("15m", "1h"):
            for template in ("fast", "base", "slow"):
                rows.append((edge, resolution, "log_ratio_mean_reversion", template))
                rows.append((edge, resolution, "residual_a_b", template))
                rows.append((edge, resolution, "residual_b_a", template))
    return rows


def _scout_trial() -> ScannerTrial:
    first = AssetId("ASSET00000")
    second = AssetId("ASSET00001")
    return ScannerTrial(
        candidate_id="a" * 64,
        scan_id="b" * 64,
        venue="binance",
        horizon=ScannerHorizon.SHORT,
        universe_snapshot_id="c" * 64,
        pair_id="ASSET00000/ASSET00001",
        asset_a=first,
        asset_b=second,
        orientation=PairOrientation(base=first, quote=second),
        resolution=BarInterval("1h"),
        model_family=ScannerModelFamily.LOG_RATIO_MEAN_REVERSION,
        template_id=TemplateId.FAST,
        window_bars=48,
        minimum_observations=46,
        source_artifact_fingerprints=("d" * 64, "e" * 64),
        selection_slice_fingerprints=("f" * 64, "1" * 64),
        evidence_dataset_ids=("asset0-1h", "asset1-1h"),
        automatic_neighbor_selected=True,
        manual_pinned=False,
    )


def _measure_scout(sample_count: int) -> float:
    trial = _scout_trial()
    start = datetime(2024, 1, 1, tzinfo=UTC)
    timestamps = tuple(start + timedelta(hours=index) for index in range(721))
    z_scores = tuple(2.0 * math.sin(index / 12.0) for index in range(721))
    prices = {
        trial.asset_a: tuple(100.0 + 0.01 * index for index in range(721)),
        trial.asset_b: tuple(50.0 + 0.008 * index for index in range(721)),
    }
    started = time.perf_counter()
    for _ in range(sample_count):
        run_scout_trial(
            trial,
            timestamps=timestamps,
            z_scores=z_scores,
            prices_by_asset=prices,
            evaluation_start=timestamps[0],
            evaluation_end=timestamps[-1],
            cost_policy=SCANNER_V1_SLICE1.cost_policy,
        )
    return time.perf_counter() - started


def benchmark_one(
    *,
    assets: int,
    bars: int,
    seed: int,
    scout_sample: int,
) -> BenchmarkResult:
    if assets < 2 or bars < 2:
        raise ValueError("assets and bars must both be at least two")
    generated = _paths(assets=assets, bars=bars + 48, seed=seed)

    slice_started = time.perf_counter()
    selected = np.ascontiguousarray(generated[:, -bars:])
    if not np.isfinite(selected).all() or np.any(selected <= 0):
        raise RuntimeError("synthetic benchmark produced invalid prices")
    slice_seconds = time.perf_counter() - slice_started

    ssd_started = time.perf_counter()
    pair_count, edge_count, digest = _top_k_graph(
        selected,
        k=SCANNER_V1_SLICE1.neighbors_per_asset,
    )
    ssd_seconds = time.perf_counter() - ssd_started

    enumeration_started = time.perf_counter()
    trials = _fixed_trials(edge_count)
    enumeration_seconds = time.perf_counter() - enumeration_started
    expected_trials = edge_count * 18
    if len(trials) != expected_trials:
        raise RuntimeError("fixed scanner trial count drifted")

    sample_count = min(max(1, scout_sample), len(trials))
    scout_seconds = _measure_scout(sample_count)
    projected = scout_seconds * len(trials) / sample_count
    replay_ceiling = SCANNER_V1_SLICE1.automatic_replay_cap_per_horizon * len(
        tuple(ScannerHorizon)
    )
    if replay_ceiling != 30:
        raise RuntimeError("automatic all-horizon replay ceiling drifted")
    return BenchmarkResult(
        assets=assets,
        bars=bars,
        source_slice_seconds=slice_seconds,
        ssd_seconds=ssd_seconds,
        valid_pair_count=pair_count,
        retained_edge_count=edge_count,
        fixed_trial_count=len(trials),
        trial_enumeration_seconds=enumeration_seconds,
        scout_sample_count=sample_count,
        scout_sample_seconds=scout_seconds,
        projected_full_scout_seconds=projected,
        automatic_replay_ceiling_all_horizons=replay_ceiling,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        digest=digest,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=int, nargs="+", default=[500, 1000])
    parser.add_argument("--bars", type=int, default=720)
    parser.add_argument("--seed", type=int, default=20260818)
    parser.add_argument("--scout-sample", type=int, default=200)
    parser.add_argument("--output", type=Path, default=None)
    return parser


def main() -> int:
    args = _parser().parse_args()
    results = [
        benchmark_one(
            assets=assets,
            bars=args.bars,
            seed=args.seed,
            scout_sample=args.scout_sample,
        )
        for assets in args.assets
    ]
    payload = {
        "schema_version": "qap.scanner.slice1-benchmark.v1",
        "results": [result.payload() for result in results],
    }
    rendered = json.dumps(payload, sort_keys=True, indent=2)
    if args.output is not None:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
