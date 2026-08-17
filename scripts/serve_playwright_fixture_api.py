"""Serve a deterministic local fixture API for the two critical browser E2E flows."""

from argparse import ArgumentParser
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn

from qap.api import ApiSettings, create_app
from qap.experiment import load_manifest, run_experiment_to_artifacts

_ROOT = Path(__file__).resolve().parents[1]
_MANIFEST = _ROOT / "tests/fixtures/experiments/two_asset_dummy.json"
_RUN_TIMESTAMP = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--api-port", type=int, required=True)
    parser.add_argument("--frontend-port", type=int, required=True)
    args = parser.parse_args()

    with TemporaryDirectory(prefix="qap-playwright-") as temporary:
        run_root = Path(temporary) / "runs"
        run_experiment_to_artifacts(
            load_manifest(_MANIFEST),
            data_root=_ROOT,
            repository_root=_ROOT,
            run_root=run_root,
            run_timestamp=_RUN_TIMESTAMP,
        )
        app = create_app(
            ApiSettings(
                run_root=run_root,
                market_data_root=_ROOT,
                allowed_origins=(f"http://127.0.0.1:{args.frontend_port}",),
                host="127.0.0.1",
                port=args.api_port,
            )
        )
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=args.api_port,
            log_level="warning",
        )


if __name__ == "__main__":
    main()
