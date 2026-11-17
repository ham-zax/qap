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

from qap.policy.lab_settings import LabSettings
from qap.product_lab_store import LabStudyStore

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/run_lab_trials.py"


class Handler(BaseHTTPRequestHandler):
    requests: list[tuple[str, dict[str, Any]]] = []
    actor_headers: list[str | None] = []

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
        self.actor_headers.append(self.headers.get("X-QAP-Actor-Id"))
        self.reply(200, {"operation_id": "operation", "status": "completed"})

    def do_POST(self) -> None:
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.requests.append((self.path, payload))
        self.actor_headers.append(self.headers.get("X-QAP-Actor-Id"))
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
            "bootstrap_replicates": 9999,
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


def test_runner_preflight_rejects_impossible_family_before_preparation(
    tmp_path: Path,
) -> None:
    Handler.requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        plan = tmp_path / "plan24.json"
        output = tmp_path / "out24.jsonl"
        trials = [
            {
                "coin_a": f"binance:C{i}",
                "coin_b": "binance:BTC",
                "method": "zscore",
                "settings": {"auto_tune": True},
            }
            for i in range(24)
        ]
        plan.write_text(json.dumps(trials), encoding="utf-8")
        env = {
            **os.environ,
            "QAP_LAB_API_BASE_URL": f"http://127.0.0.1:{server.server_port}",
        }
        # 499 replicates, multiplier 3, family 24 is rejected before any HTTP call.
        res = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--plan",
                str(plan),
                "--out",
                str(output),
                "--replicates",
                "499",
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert res.returncode == 3
        assert "requires at least 1439" in res.stderr
        assert not output.exists()
        assert Handler.requests == []

        # Existing actor registrations on a shared pair count conservatively too.
        run_root = tmp_path / "runs"
        store = LabStudyStore(run_root, actor_id="agent")
        fam = store.family_id("binance:C0", "binance:BTC")
        existing = [
            {
                "id": i,
                "settings": LabSettings(entry=1.0 + i * 0.1).model_dump(mode="json"),
            }
            for i in range(20)
        ]
        store.register_trials(
            fam,
            existing,
            validation_start="2026-01-01T00:00:00+00:00",
            validation_end="2026-06-01T00:00:00+00:00",
        )
        res_existing = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--plan",
                str(plan),
                "--out",
                str(output),
                "--run-root",
                str(run_root),
                "--actor-id",
                "agent",
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert res_existing.returncode == 3
        assert "pair_trial_count=23" in res_existing.stderr
        assert not output.exists()
        assert Handler.requests == []

        # Declared settings, anchor, and --actor-id reach HTTP study requests.
        Handler.requests = []
        Handler.actor_headers = []
        plan_custom = tmp_path / "plan_custom.json"
        out_custom = tmp_path / "out_custom.jsonl"
        plan_custom.write_text(
            json.dumps(
                [
                    {
                        "coin_a": "binance:SOL",
                        "coin_b": "binance:ETH",
                        "bar": "4h",
                        "days": 90,
                        "band_lookback": 180,
                        "anchor": "binance:BTC",
                        "settings": {
                            "method": "copula",
                            "lookback": 96,
                            "copula_probability": 0.02,
                            "auto_tune": False,
                        },
                    }
                ]
            ),
            encoding="utf-8",
        )
        res_ok = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--plan",
                str(plan_custom),
                "--out",
                str(out_custom),
                "--actor-id",
                "wave-s4b",
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert res_ok.returncode == 0, res_ok.stderr
        assert Handler.requests[1][1] == {
            "coin_a": "binance:SOL",
            "coin_b": "binance:ETH",
            "bar": "4h",
            "days": 90,
            "band_lookback": 180,
            "anchor": "binance:BTC",
            "bootstrap_replicates": 9999,
            "settings": {
                "method": "copula",
                "lookback": 96,
                "copula_probability": 0.02,
                "auto_tune": False,
            },
        }
        assert all(h == "wave-s4b" for h in Handler.actor_headers)

        Handler.requests = []
        out_rep = tmp_path / "out_rep.jsonl"
        res_rep = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--plan",
                str(plan_custom),
                "--out",
                str(out_rep),
                "--replicates",
                "19999",
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert res_rep.returncode == 0, res_rep.stderr
        assert Handler.requests[1][1]["bootstrap_replicates"] == 19999

        # Tighter trial-level settings.significance is enforced in preflight.
        Handler.requests = []
        plan_sig = tmp_path / "plan_sig.json"
        out_sig = tmp_path / "out_sig.jsonl"
        plan_sig.write_text(
            json.dumps(
                [
                    {
                        "coin_a": "binance:SOL",
                        "coin_b": "binance:ETH",
                        "method": "zscore",
                        "settings": {"auto_tune": True, "significance": 0.005},
                    }
                ]
            ),
            encoding="utf-8",
        )
        res_sig = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--plan",
                str(plan_sig),
                "--out",
                str(out_sig),
                "--replicates",
                "199",
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert res_sig.returncode == 3
        assert "alpha=0.005" in res_sig.stderr
        assert Handler.requests == []
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
