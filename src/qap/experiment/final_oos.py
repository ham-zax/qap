"""Internal capability for executing a durably reserved final-OOS run."""

import hashlib
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
_FINAL_OOS_REGISTRY = ".final-oos-commitments"


def _authoritative_registry_path(
    *,
    commitment_path: Path,
    research_family_id: str,
    holdout_id: str,
) -> Path:
    resolved_commitment = commitment_path.resolve()
    if (
        resolved_commitment.name != "commitment.json"
        or resolved_commitment.parent.name == ""
    ):
        raise ExperimentSetupError(
            "final-OOS permit requires the authoritative run commitment path"
        )
    identity = f"{research_family_id}\0{holdout_id}".encode("utf-8")
    filename = f"{hashlib.sha256(identity).hexdigest()}.json"
    return resolved_commitment.parent.parent / _FINAL_OOS_REGISTRY / filename


def _load_json_object(path: Path, *, description: str) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExperimentSetupError(
            f"final-OOS permit requires a readable {description}"
        ) from exc
    if not isinstance(raw, dict):
        raise ExperimentSetupError(f"final-OOS {description} must be an object")
    return cast(dict[str, object], raw)


def issue_final_oos_execution_permit(
    *,
    manifest: ExperimentManifest,
    provenance: RunProvenance,
    commitment_path: Path,
) -> FinalOosExecutionPermit:
    if manifest.data_role is not DataRole.FINAL_OOS:
        raise ExperimentSetupError("final-OOS permit requires a final_oos experiment")
    typed_raw = _load_json_object(
        commitment_path,
        description="commitment artifact",
    )
    if commitment_path.resolve().parent.name != provenance.run_id:
        raise ExperimentSetupError(
            "final-OOS permit requires the authoritative run commitment path"
        )
    holdout_id = typed_raw.get("holdout_id")
    if not isinstance(holdout_id, str) or not holdout_id:
        raise ExperimentSetupError("final-OOS commitment must declare a holdout_id")
    registry_path = _authoritative_registry_path(
        commitment_path=commitment_path,
        research_family_id=manifest.research_family_id,
        holdout_id=holdout_id,
    )
    registry_raw = _load_json_object(
        registry_path,
        description="authoritative holdout registry entry",
    )
    if registry_raw != typed_raw:
        raise ExperimentSetupError(
            "final-OOS commitment does not match the authoritative holdout "
            "registry entry"
        )
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
