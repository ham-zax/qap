"""Internal capability for executing a durably reserved final-OOS run."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from qap.experiment.data import ExperimentSetupError
from qap.experiment.manifest import DataRole, ExperimentManifest
from qap.experiment.provenance import RunProvenance


@dataclass(frozen=True, slots=True, init=False)
class FinalOosExecutionPermit:
    run_id: str
    manifest_sha256: str
    code_fingerprint: str
    token: object

    def __init__(self) -> None:
        raise TypeError(
            "final-OOS execution permits are issued by the reservation path"
        )


_FINAL_OOS_EXECUTION_TOKEN = object()


def issue_final_oos_execution_permit(
    *,
    manifest: ExperimentManifest,
    provenance: RunProvenance,
    commitment_path: Path,
) -> FinalOosExecutionPermit:
    if manifest.data_role is not DataRole.FINAL_OOS:
        raise ExperimentSetupError("final-OOS permit requires a final_oos experiment")
    try:
        raw = json.loads(commitment_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExperimentSetupError(
            "final-OOS reservation permit requires a readable commitment artifact"
        ) from exc
    if not isinstance(raw, dict):
        raise ExperimentSetupError("final-OOS commitment artifact must be an object")
    typed_raw = cast(dict[str, object], raw)
    expected = {
        "run_id": provenance.run_id,
        "research_family_id": manifest.research_family_id,
        "manifest_sha256": provenance.manifest_sha256,
        "code_fingerprint": provenance.code_fingerprint,
        "consumed": False,
        "execution_status": "committed",
    }
    if any(typed_raw.get(key) != value for key, value in expected.items()):
        raise ExperimentSetupError(
            "final-OOS reservation permit does not match the committed experiment"
        )
    permit = object.__new__(FinalOosExecutionPermit)
    object.__setattr__(permit, "run_id", provenance.run_id)
    object.__setattr__(permit, "manifest_sha256", provenance.manifest_sha256)
    object.__setattr__(permit, "code_fingerprint", provenance.code_fingerprint)
    object.__setattr__(permit, "token", _FINAL_OOS_EXECUTION_TOKEN)
    return permit


def valid_final_oos_execution_permit(
    *,
    provenance: RunProvenance,
    permit: FinalOosExecutionPermit | None,
) -> bool:
    return (
        permit is not None
        and permit.token is _FINAL_OOS_EXECUTION_TOKEN
        and permit.run_id == provenance.run_id
        and permit.manifest_sha256 == provenance.manifest_sha256
        and permit.code_fingerprint == provenance.code_fingerprint
    )


__all__ = [
    "FinalOosExecutionPermit",
    "issue_final_oos_execution_permit",
    "valid_final_oos_execution_permit",
]
