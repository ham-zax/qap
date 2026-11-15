"""Single Lab owner for trial counts, immutable results and pin metadata."""

import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from qap.artifact_integrity import build_integrity_record, read_and_validate_integrity
from qap.file_lock import FileLock


class LabStoreError(RuntimeError):
    """Saved Lab state is unavailable or invalid; never silently reset it."""


def canonical_json(value: Any) -> bytes:
    def encode(item: object) -> str:
        if isinstance(item, datetime):
            return item.isoformat()
        if isinstance(item, Decimal):
            return str(item)
        raise TypeError(f"Unsupported Lab value: {type(item).__name__}")

    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False, default=encode
    ).encode()


def content_id(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _read(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise LabStoreError(
            "Lab state is invalid. Existing files were preserved."
        ) from exc


def _atomic_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=".lab-", delete=False
    ) as file:
        temporary = Path(file.name)
        file.write(canonical_json(value))
        file.flush()
        os.fsync(file.fileno())
    os.replace(temporary, path)


def _validation_window(start: object, end: object) -> tuple[str, str]:
    if (
        not isinstance(start, str)
        or not isinstance(end, str)
        or not start
        or start >= end
    ):
        raise LabStoreError("Lab validation window is invalid.")
    return start, end


def _trial_history(
    value: object,
) -> tuple[dict[str, Any], dict[tuple[str, str], bool]]:
    if not isinstance(value, dict):
        raise LabStoreError("Lab trial records are invalid.")
    row = cast(dict[str, Any], value)
    original = _validation_window(
        row.get("validation_start"), row.get("validation_end")
    )
    history = row.get("validation_windows", [])
    if not isinstance(history, list):
        raise LabStoreError("Lab validation history is invalid.")
    windows = {original: False}
    for value in cast(list[object], history):
        if not isinstance(value, dict):
            raise LabStoreError("Lab validation history is invalid.")
        entry = cast(dict[str, Any], value)
        window = _validation_window(
            entry.get("validation_start"), entry.get("validation_end")
        )
        reused = entry.get("reused", False)
        if not isinstance(reused, bool):
            raise LabStoreError("Lab validation reuse flag is invalid.")
        windows[window] = windows.get(window, False) or reused
    return row, windows


class LabStudyStore:
    def __init__(self, run_root: Path) -> None:
        self.root = run_root / "product" / "pair-rotation-lab"

    @staticmethod
    def require_id(identifier: str) -> None:
        if len(identifier) != 64 or any(
            char not in "0123456789abcdef" for char in identifier
        ):
            raise LabStoreError("Saved result identifier is invalid.")

    def family_id(self, coin_a: str, coin_b: str) -> str:
        return content_id(sorted((coin_a, coin_b)))

    def family_lock(self, identifier: str) -> FileLock:
        self.require_id(identifier)
        return FileLock(self.root / "families" / identifier / ".lock")

    def register_trials(
        self,
        identifier: str,
        configurations: list[dict[str, Any]],
        *,
        validation_start: str,
        validation_end: str,
    ) -> tuple[int, bool]:
        """Caller holds the family lock through computation and publication."""
        self.require_id(identifier)
        current = _validation_window(validation_start, validation_end)
        path = self.root / "families" / identifier / "trials.json"
        raw = _read(path, {"schema_version": "qap.lab.trials.v1", "trials": {}})
        if not isinstance(raw, dict):
            raise LabStoreError("Lab trial registry has an invalid shape.")
        state = cast(dict[str, Any], raw)
        if state.get("schema_version") != "qap.lab.trials.v1" or not isinstance(
            state.get("trials"), dict
        ):
            raise LabStoreError("Lab trial registry has an invalid shape.")
        trials = cast(dict[str, Any], state["trials"])
        requested = {content_id(item) for item in configurations}
        histories = {key: _trial_history(row) for key, row in trials.items()}
        new_settings = not requested.issubset(trials)
        reused = any(
            start < validation_end
            and end > validation_start
            and (
                key not in requested
                or new_settings
                or (start, end) != current
                or prior_reuse
            )
            for key, (_, windows) in histories.items()
            for (start, end), prior_reuse in windows.items()
        )
        for configuration in configurations:
            key = content_id(configuration)
            row: dict[str, Any]
            windows: dict[tuple[str, str], bool]
            if key in histories:
                row, windows = histories[key]
            else:
                row = {
                    "configuration": configuration,
                    "validation_start": validation_start,
                    "validation_end": validation_end,
                    "first_seen": datetime.now(UTC).isoformat(),
                }
                windows = {}
                trials[key] = row
                histories[key] = row, windows
            windows[current] = windows.get(current, False) or reused
            row["validation_windows"] = [
                {"validation_start": start, "validation_end": end, "reused": seen}
                for (start, end), seen in windows.items()
            ]
        _atomic_write(path, state)
        return len(trials), reused

    def _pins(self) -> list[str]:
        value = _read(self.root / "pins.json", [])
        if not isinstance(value, list):
            raise LabStoreError("Lab pin metadata is invalid.")
        items = cast(list[object], value)
        if any(not isinstance(item, str) for item in items):
            raise LabStoreError("Lab pin metadata is invalid.")
        return cast(list[str], items)

    def save(self, result: dict[str, Any]) -> dict[str, Any]:
        identifier = content_id(result)
        destination = self.root / "studies" / identifier
        if destination.exists():
            return self.read(identifier)
        destination.parent.mkdir(parents=True, exist_ok=True)
        envelope = {
            "study_id": identifier,
            "created_at": datetime.now(UTC).isoformat(),
            "result": result,
        }
        with tempfile.TemporaryDirectory(
            dir=destination.parent, prefix=".study-"
        ) as temporary:
            staging = Path(temporary)
            (staging / "result.json").write_bytes(canonical_json(envelope))
            integrity = build_integrity_record(
                staging, artifact_id=identifier, file_names=("result.json",)
            )
            (staging / "integrity.json").write_text(integrity.model_dump_json())
            os.rename(staging, destination)
        return {**envelope, "pinned": False}

    def read(self, identifier: str) -> dict[str, Any]:
        self.require_id(identifier)
        directory = self.root / "studies" / identifier
        try:
            read_and_validate_integrity(
                directory,
                artifact_id=identifier,
                required_files=frozenset({"result.json"}),
                allowed_files=frozenset({"result.json"}),
            )
            raw = _read(directory / "result.json", None)
            if not isinstance(raw, dict):
                raise ValueError("Snapshot content identity does not match.")
            envelope = cast(dict[str, Any], raw)
            if (
                envelope.get("study_id") != identifier
                or content_id(envelope["result"]) != identifier
            ):
                raise ValueError("Snapshot content identity does not match.")
            return {**envelope, "pinned": identifier in self._pins()}
        except (OSError, ValueError, KeyError) as exc:
            raise LabStoreError(
                "Saved result is missing or changed. Files were preserved."
            ) from exc

    def set_pin(self, identifier: str, pinned: bool) -> dict[str, Any]:
        with FileLock(self.root / ".pins.lock"):
            envelope = self.read(identifier)
            pins = set(self._pins())
            pins.add(identifier) if pinned else pins.discard(identifier)
            _atomic_write(self.root / "pins.json", sorted(pins))
            return {**envelope, "pinned": pinned}

    def list(self, *, limit: int = 25, offset: int = 0) -> list[dict[str, Any]]:
        parent = self.root / "studies"
        if not parent.exists():
            return []
        directories = sorted(
            (path for path in parent.iterdir() if not path.name.startswith(".")),
            key=lambda path: path.stat().st_mtime_ns,
            reverse=True,
        )
        rows: list[dict[str, Any]] = []
        for path in directories[offset : offset + limit]:
            envelope = self.read(path.name)
            result = envelope["result"]
            analysis = result["analysis"]
            rows.append(
                {
                    "study_id": envelope["study_id"],
                    "created_at": envelope["created_at"],
                    "pinned": envelope["pinned"],
                    "coin_a": analysis["coin_a"],
                    "coin_b": analysis["coin_b"],
                    "method": result["requested_settings"]["method"],
                    "data_through": analysis["data_through"],
                    "headline": result["call"]["headline"],
                }
            )
        return rows
