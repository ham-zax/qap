"""Export the deterministic QAP OpenAPI contract for frontend type generation."""

import argparse
import json
from pathlib import Path

from qap.api import ApiSettings, create_app


def export_openapi(destination: Path) -> None:
    app = create_app(ApiSettings(run_root=Path("runs")))
    payload = json.dumps(
        app.openapi(),
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(payload + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(prog="export_openapi.py")
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    export_openapi(arguments.destination)


if __name__ == "__main__":
    main()
