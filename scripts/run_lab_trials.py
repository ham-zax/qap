"""Run a predeclared family of Lab studies in sequence."""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from qap.experiment.lab_proof import settings_candidates
from qap.experiment.lab_statistics import (
    DEFAULT_SPA_REPLICATES,
    FamilyResolutionError,
    require_family_resolution,
)
from qap.policy.lab_settings import LabSettings
from qap.product_lab_store import LabStoreError, LabStudyStore

API_BASE = os.environ.get("QAP_LAB_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
PROOF_FIELDS = (
    "passes",
    "vs_hodl_pct",
    "vs_control_pct",
    "folds_passing",
    "folds_total",
    "validation_trades",
    "raw_p_value",
    "corrected_p_value",
    "settings_tried",
)


def request(
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    actor_id: str = "local",
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode()
    headers: dict[str, str] = (
        {} if data is None else {"Content-Type": "application/json"}
    )
    if actor_id and actor_id != "local":
        headers["X-QAP-Actor-Id"] = actor_id
    with urlopen(Request(API_BASE + path, data=data, headers=headers)) as response:
        return json.load(response)


def _normalize_trial(
    raw_trial: dict[str, Any], idx: int
) -> tuple[dict[str, Any], LabSettings]:
    coin_a = str(raw_trial.get("coin_a") or "")
    coin_b = str(raw_trial.get("coin_b") or "")
    if not coin_a or not coin_b:
        raise ValueError(f"Trial {idx} must specify coin_a and coin_b.")
    settings_val = raw_trial.get("settings")
    if settings_val is not None and not isinstance(settings_val, dict):
        raise ValueError(f"Trial {idx} settings must be a JSON object.")
    raw_settings: dict[str, Any] = dict(cast(dict[str, Any], settings_val or {}))
    if "method" not in raw_settings and raw_trial.get("method") is not None:
        raw_settings["method"] = raw_trial["method"]
    cfg = LabSettings.model_validate(raw_settings)
    anchor_val = raw_trial.get("anchor")
    if anchor_val is not None and not isinstance(anchor_val, str):
        raise ValueError(f"Trial {idx} anchor must be a string or null.")
    payload = {
        "coin_a": coin_a,
        "coin_b": coin_b,
        "bar": raw_trial.get("bar", "15m"),
        "days": raw_trial.get("days", 180),
        "band_lookback": raw_trial.get("band_lookback", 672),
        "anchor": anchor_val,
        "settings": raw_settings,
    }
    return payload, cfg


def prepare(trial: dict[str, Any], *, actor_id: str = "local") -> None:
    operation = request(
        "/api/pair-rotation/open",
        {
            "coin_a": trial.get("coin_a"),
            "coin_b": trial.get("coin_b"),
            "include_execution": True,
        },
        actor_id=actor_id,
    )
    while True:
        operation = request(
            f"/api/operations/{operation['operation_id']}",
            actor_id=actor_id,
        )
        status = operation.get("status")
        if status == "completed":
            return
        if status in ("failed", "interrupted", "cancelled"):
            raise RuntimeError(f"Data preparation {status}: {json.dumps(operation)}")
        time.sleep(1)


def total(trades: Any, field: str) -> str | None:
    if trades is None or any(trade.get(field) is None for trade in trades):
        return None
    return str(sum((Decimal(trade[field]) for trade in trades), Decimal(0)))


def run_trial(
    index: int,
    trial: dict[str, Any],
    *,
    actor_id: str = "local",
    replicates: int = DEFAULT_SPA_REPLICATES,
) -> dict[str, Any]:
    start = time.monotonic()
    payload, cfg = _normalize_trial(trial, index)
    payload["bootstrap_replicates"] = replicates
    row: dict[str, Any] = {
        "trial": index,
        "coin_a": payload["coin_a"],
        "coin_b": payload["coin_b"],
        "method": trial.get("method") or cfg.method,
    }
    try:
        prepare(payload, actor_id=actor_id)
        study = request("/api/pair-rotation/studies", payload, actor_id=actor_id)
    except HTTPError as error:
        row["seconds"] = int(time.monotonic() - start)
        row["error"] = {"status": error.code, "body": error.read().decode("utf-8")}
        return row
    row["seconds"] = int(time.monotonic() - start)
    result: dict[str, Any] = study.get("result") or {}
    proof: dict[str, Any] = result.get("proof") or {}
    call: dict[str, Any] = result.get("call") or {}
    wealth: dict[str, Any] = result.get("wealth") or {}
    row["study_id"] = study.get("study_id")
    row["call"] = call.get("status")
    for field in PROOF_FIELDS:
        row[field] = proof.get(field)
    row["terminal_values"] = wealth.get("terminal_values")
    for field in ("fees_usdt", "slippage_usdt"):
        row[field] = total(result.get("trades"), field)
    return row


def _preflight_plan(
    plan: Any,
    *,
    replicates: int,
    alpha: float,
    run_root: Path | None,
    actor_id: str,
) -> None:
    if not isinstance(plan, list) or not plan:
        raise ValueError("Trial plan must be a non-empty JSON list.")
    entries = cast(list[object], plan)
    outer_family_size = len(entries)
    pair_counts: dict[tuple[str, str], int] = {}
    pair_alpha: dict[tuple[str, str], float] = {}
    for idx, item in enumerate(entries, 1):
        if not isinstance(item, dict):
            raise ValueError(f"Trial {idx} must be a JSON object.")
        raw_trial = cast(dict[str, Any], item)
        payload, cfg = _normalize_trial(raw_trial, idx)
        coin_a = str(payload["coin_a"])
        coin_b = str(payload["coin_b"])
        pair_key = (min(coin_a, coin_b), max(coin_a, coin_b))
        pair_counts[pair_key] = pair_counts.get(pair_key, 0) + len(
            settings_candidates(cfg)
        )
        pair_alpha[pair_key] = min(pair_alpha.get(pair_key, alpha), cfg.significance)
    store = None if run_root is None else LabStudyStore(run_root, actor_id=actor_id)
    for (pair_a, pair_b), proposed_count in pair_counts.items():
        existing = (
            0
            if store is None
            else store.existing_trial_count(store.family_id(pair_a, pair_b))
        )
        require_family_resolution(
            pair_label=f"{pair_a}/{pair_b}",
            outer_family_size=outer_family_size,
            pair_trial_count=existing + proposed_count,
            replicates=replicates,
            alpha=pair_alpha[(pair_a, pair_b)],
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--replicates", type=int, default=DEFAULT_SPA_REPLICATES)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument(
        "--run-root",
        type=Path,
        default=Path(os.environ["QAP_RUN_ROOT"])
        if os.environ.get("QAP_RUN_ROOT")
        else None,
    )
    parser.add_argument("--actor-id", type=str, default="local")
    args = parser.parse_args()
    if args.out.exists():
        print(f"Output already exists: {args.out}", file=sys.stderr)
        return 2
    plan_bytes = args.plan.read_bytes()
    plan = json.loads(plan_bytes)
    try:
        _preflight_plan(
            plan,
            replicates=args.replicates,
            alpha=args.alpha,
            run_root=args.run_root,
            actor_id=args.actor_id,
        )
    except (FamilyResolutionError, LabStoreError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 3
    try:
        output = args.out.open("x", encoding="utf-8")
    except FileExistsError:
        print(f"Output already exists: {args.out}", file=sys.stderr)
        return 2
    with output:
        header = {
            "family": hashlib.sha256(plan_bytes).hexdigest(),
            "trials": len(plan),
            "started_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
        output.write(json.dumps(header) + "\n")
        output.flush()
        for index, trial in enumerate(plan, 1):
            try:
                row = run_trial(
                    index,
                    trial,
                    actor_id=args.actor_id,
                    replicates=args.replicates,
                )
            except RuntimeError as error:
                print(error, file=sys.stderr)
                return 1
            output.write(json.dumps(row) + "\n")
            output.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
