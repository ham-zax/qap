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
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

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


def request(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode()
    headers = {} if data is None else {"Content-Type": "application/json"}
    with urlopen(Request(API_BASE + path, data=data, headers=headers)) as response:
        return json.load(response)


def prepare(trial: dict[str, Any]) -> None:
    operation = request(
        "/api/pair-rotation/open",
        {
            "coin_a": trial.get("coin_a"),
            "coin_b": trial.get("coin_b"),
            "include_execution": True,
        },
    )
    while True:
        operation = request(f"/api/operations/{operation['operation_id']}")
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


def run_trial(index: int, trial: dict[str, Any]) -> dict[str, Any]:
    start = time.monotonic()
    row: dict[str, Any] = {
        "trial": index,
        "coin_a": trial.get("coin_a"),
        "coin_b": trial.get("coin_b"),
        "method": trial.get("method"),
    }
    try:
        prepare(trial)
        payload = {
            "coin_a": trial.get("coin_a"),
            "coin_b": trial.get("coin_b"),
            "bar": trial.get("bar", "15m"),
            "days": trial.get("days", 180),
            "band_lookback": trial.get("band_lookback", 672),
            "anchor": None,
            "settings": {"method": trial.get("method")},
        }
        study = request("/api/pair-rotation/studies", payload)
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        print(f"Output already exists: {args.out}", file=sys.stderr)
        return 2
    plan_bytes = args.plan.read_bytes()
    plan = json.loads(plan_bytes)
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
                row = run_trial(index, trial)
            except RuntimeError as error:
                print(error, file=sys.stderr)
                return 1
            output.write(json.dumps(row) + "\n")
            output.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
