"""Run critical browser flows against deterministic local QAP servers."""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast
from urllib.error import URLError
from urllib.request import urlopen

_ROOT = Path(__file__).resolve().parents[1]
_WEB_ROOT = _ROOT / "web"
_DEFAULT_SPECS = (
    "e2e/portfolio-workbench.spec.ts",
    "e2e/pair-anchor-lens.spec.ts",
    "e2e/slice4-discovery-basket.spec.ts",
    "e2e/slice4-prospective-operations.spec.ts",
)


def _available_loopback_ports(count: int) -> tuple[int, ...]:
    if count <= 0:
        raise ValueError("count must be positive")
    reservations: list[socket.socket] = []
    try:
        for _ in range(count):
            reservation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            reservation.bind(("127.0.0.1", 0))
            reservations.append(reservation)
        return tuple(
            cast(tuple[str, int], reservation.getsockname())[1]
            for reservation in reservations
        )
    finally:
        for reservation in reservations:
            reservation.close()


def _wait_for_http(
    *,
    name: str,
    url: str,
    process: subprocess.Popen[bytes],
    log_path: Path,
    timeout_seconds: float = 120.0,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        return_code = process.poll()
        if return_code is not None:
            log = log_path.read_text(encoding="utf-8", errors="replace")
            raise RuntimeError(
                f"{name} exited before readiness with code {return_code}:\n{log}"
            )
        try:
            with urlopen(url, timeout=0.5) as response:  # noqa: S310 - loopback only
                if 200 <= response.status < 500:
                    return
        except TimeoutError, URLError:
            time.sleep(0.1)
    log = log_path.read_text(encoding="utf-8", errors="replace")
    raise TimeoutError(f"{name} did not become ready at {url}:\n{log}")


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=3)
    except ProcessLookupError, subprocess.TimeoutExpired:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=3)


def main(argv: list[str]) -> int:
    normalized_argv = argv[1:] if argv[:1] == ["--"] else argv
    specs = normalized_argv or list(_DEFAULT_SPECS)
    api_port, web_port = _available_loopback_ports(2)
    api_base_url = f"http://127.0.0.1:{api_port}"
    web_base_url = f"http://127.0.0.1:{web_port}"

    with TemporaryDirectory(prefix="qap-playwright-runner-") as temporary:
        temp_root = Path(temporary)
        api_log_path = temp_root / "api.log"
        web_log_path = temp_root / "web.log"
        with (
            api_log_path.open("wb") as api_log,
            web_log_path.open("wb") as web_log,
        ):
            api = subprocess.Popen(
                [
                    "uv",
                    "run",
                    "python",
                    "scripts/serve_playwright_fixture_api.py",
                    "--api-port",
                    str(api_port),
                    "--frontend-port",
                    str(web_port),
                ],
                cwd=_ROOT,
                env={
                    **os.environ,
                    "QAP_BINANCE_PUBLIC_BASE_URL": f"{api_base_url}/__fixture/binance",
                },
                stdout=api_log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            web: subprocess.Popen[bytes] | None = None
            try:
                _wait_for_http(
                    name="fixture API",
                    url=f"{api_base_url}/api/health",
                    process=api,
                    log_path=api_log_path,
                )
                print(f"fixture API ready: {api_base_url}", flush=True)

                web_environment = os.environ.copy()
                web_environment["VITE_QAP_API_BASE_URL"] = api_base_url
                web = subprocess.Popen(
                    [
                        "pnpm",
                        "exec",
                        "vite",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(web_port),
                        "--strictPort",
                    ],
                    cwd=_WEB_ROOT,
                    env=web_environment,
                    stdout=web_log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                _wait_for_http(
                    name="Vite frontend",
                    url=web_base_url,
                    process=web,
                    log_path=web_log_path,
                )
                print(f"Vite frontend ready: {web_base_url}", flush=True)

                test_environment = os.environ.copy()
                test_environment["QAP_E2E_API_BASE_URL"] = api_base_url
                test_environment["QAP_E2E_WEB_BASE_URL"] = web_base_url
                completed = subprocess.run(
                    [
                        "pnpm",
                        "exec",
                        "playwright",
                        "test",
                        "--workers=1",
                        *specs,
                    ],
                    cwd=_WEB_ROOT,
                    env=test_environment,
                    check=False,
                )
                return completed.returncode
            finally:
                if web is not None:
                    _terminate_process_group(web)
                _terminate_process_group(api)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
