"""Exercise the trial runner against a local fake API."""

import hashlib
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/run_lab_trials.py"


class Handler(BaseHTTPRequestHandler):
    requests: list[tuple[str, dict[str, Any]]] = []

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def reply(self, status: int, value: Any) -> None:
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        self.reply(200, {"operation_id": "operation", "status": "completed"})

    def do_POST(self) -> None:
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.requests.append((self.path, payload))
        if self.path.endswith("/open"):
            self.reply(202, {"operation_id": "operation"})
        elif payload["coin_a"] == "binance:BNB":
            self.reply(409, {"detail": "unavailable"})
        else:
            self.reply(
                200,
                {
                    "study_id": "study-1",
                    "result": {
                        "call": {"status": "no_edge"},
                        "proof": {"passes": False, "vs_hodl_pct": -4.29},
                        "wealth": None,
                        "trades": [
                            {"fees_usdt": "0.10", "slippage_usdt": "0.02"},
                            {"fees_usdt": "0.20", "slippage_usdt": "0.03"},
                        ],
                    },
                },
            )


def test_runner(tmp_path: Path) -> None:
    Handler.requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        plan = tmp_path / "plan.json"
        output = tmp_path / "output.jsonl"
        trials = [
            {"coin_a": "binance:SOL", "coin_b": "binance:ETH", "method": "zscore"},
            {"coin_a": "binance:BNB", "coin_b": "binance:ETH", "method": "zscore"},
        ]
        plan.write_text(json.dumps(trials), encoding="utf-8")
        env = {
            **os.environ,
            "QAP_LAB_API_BASE_URL": f"http://127.0.0.1:{server.server_port}",
        }
        command = [
            sys.executable,
            str(SCRIPT),
            "--plan",
            str(plan),
            "--out",
            str(output),
        ]
        result = subprocess.run(
            command, env=env, capture_output=True, text=True, check=False
        )
        assert result.returncode == 0, result.stderr
        lines = [json.loads(line) for line in output.read_text().splitlines()]
        assert list(lines[0]) == ["family", "trials", "started_at"]
        assert lines[0]["family"] == hashlib.sha256(plan.read_bytes()).hexdigest()
        assert lines[0]["trials"] == 2
        assert lines[0]["started_at"].endswith("Z")
        assert list(lines[1]) == [
            "trial",
            "coin_a",
            "coin_b",
            "method",
            "seconds",
            "study_id",
            "call",
            "passes",
            "vs_hodl_pct",
            "vs_control_pct",
            "folds_passing",
            "folds_total",
            "validation_trades",
            "raw_p_value",
            "corrected_p_value",
            "settings_tried",
            "terminal_values",
            "fees_usdt",
            "slippage_usdt",
        ]
        assert lines[1]["study_id"] == "study-1"
        assert lines[1]["call"] == "no_edge"
        assert lines[1]["passes"] is False
        assert lines[1]["vs_hodl_pct"] == -4.29
        assert lines[1]["vs_control_pct"] is None
        assert lines[1]["terminal_values"] is None
        assert lines[1]["fees_usdt"] == "0.30"
        assert lines[1]["slippage_usdt"] == "0.05"
        assert lines[2]["trial"] == 2
        assert lines[2]["error"] == {"status": 409, "body": '{"detail": "unavailable"}'}
        assert [path for path, _ in Handler.requests] == [
            "/api/pair-rotation/open",
            "/api/pair-rotation/studies",
            "/api/pair-rotation/open",
            "/api/pair-rotation/studies",
        ]
        assert Handler.requests[1][1] == {
            "coin_a": "binance:SOL",
            "coin_b": "binance:ETH",
            "bar": "15m",
            "days": 180,
            "band_lookback": 672,
            "anchor": None,
            "settings": {"method": "zscore"},
        }
        original = output.read_bytes()
        refused = subprocess.run(
            command, env=env, capture_output=True, text=True, check=False
        )
        assert refused.returncode == 2
        assert "already exists" in refused.stderr
        assert output.read_bytes() == original
        assert len(Handler.requests) == 4
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
