import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/exercise_paper_operation_window.py"


def test_window_exercise_emits_its_own_repository_provenance() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--paper-days",
            "1",
            "--experiment-runs",
            "1",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    payload = json.loads(completed.stdout)

    provenance = payload["provenance"]
    assert len(provenance["git_commit"]) == 40
    assert isinstance(provenance["git_dirty"], bool)
    assert len(provenance["code_fingerprint"]) == 64
