"""Detached worker for one durable local research operation."""

import sys
import traceback
from decimal import Decimal
from pathlib import Path

from pydantic import JsonValue

from qap.api.errors import ApiBoundaryError
from qap.api.operations import (
    OperationKind,
    OperationStatus,
    OperationStore,
)
from qap.api.pair_rotation_worker import execute_pair_rotation
from qap.api.scanner_schemas import (
    AdvanceForwardCohortRequestDto,
    CapturePublicEvidenceRequestDto,
    FreezeForwardCohortRequestDto,
    MomentumGenerationRequestDto,
    QualificationRequestDto,
    RunScanRequestDto,
)
from qap.market.microstructure_storage import (
    read_public_book_snapshots,
    read_public_market_metadata_snapshots,
)
from qap.market.public_capture import CaptureKind, capture_public_spot
from qap.portfolio import AssetId
from qap.scanner.catalog import load_scanner_catalog
from qap.scanner.models import ScannerPinSpec
from qap.scanner.prospective_integrity import validate_completed_generation
from qap.scanner.protocol import ScannerHorizon
from qap.scanner.qualification_artifacts import read_qualification
from qap.scanner_entry import (
    advance_forward_with_qap,
    freeze_scan_with_qap,
    generate_asset_momentum,
    qualify_forward_with_qap,
    run_scan_with_qap,
)


def _path(value: str | None, *, field: str) -> Path:
    if value is None:
        raise RuntimeError(f"{field} is not configured")
    return Path(value).resolve()


def _run_scan(request: RunScanRequestDto, settings: object) -> dict[str, JsonValue]:
    roots = settings
    data_root = _path(getattr(roots, "data_root"), field="data_root")
    run_root = _path(getattr(roots, "run_root"), field="run_root")
    repository_root = _path(
        getattr(roots, "repository_root"),
        field="repository_root",
    )
    pins = tuple(
        ScannerPinSpec(
            venue=pin.venue,
            asset_a=pin.asset_a,
            asset_b=pin.asset_b,
            horizons=tuple(ScannerHorizon(item) for item in pin.horizons),
            forensic=pin.forensic,
        )
        for pin in request.pins
    )
    result = run_scan_with_qap(
        as_of=request.as_of,
        horizons=tuple(ScannerHorizon(item) for item in request.horizons),
        data_root=data_root,
        run_root=run_root,
        pins=pins,
        manual_replay_candidate_ids=request.manual_replay_candidate_ids,
        repository_root=repository_root,
    )
    return {"scan_id": result.scan_id}


def _generate_momentum(
    request: MomentumGenerationRequestDto,
    settings: object,
    *,
    scan_id: str,
) -> dict[str, JsonValue]:
    path = generate_asset_momentum(
        scan_id=scan_id,
        venue=request.venue,
        horizon=ScannerHorizon(request.horizon),
        data_root=_path(getattr(settings, "data_root"), field="data_root"),
        run_root=_path(getattr(settings, "run_root"), field="run_root"),
    )
    return {"momentum_scan_id": path.name, "source_scan_id": scan_id}


def _freeze(
    request: FreezeForwardCohortRequestDto,
    settings: object,
) -> dict[str, JsonValue]:
    run_root = _path(getattr(settings, "run_root"), field="run_root")
    path = freeze_scan_with_qap(
        run_root=run_root,
        data_root=_path(getattr(settings, "data_root"), field="data_root"),
        prospective_root=run_root,
        scan_id=request.scan_id,
        horizon=ScannerHorizon(request.horizon),
        freeze_at=request.freeze_at,
    )
    return {"cohort_id": path.name}


def _advance(
    request: AdvanceForwardCohortRequestDto,
    settings: object,
    *,
    cohort_id: str,
) -> dict[str, JsonValue]:
    run_root = _path(getattr(settings, "run_root"), field="run_root")
    data_root = _path(getattr(settings, "data_root"), field="data_root")
    paths = advance_forward_with_qap(
        cohort_root=run_root / "scanner-forward" / cohort_id,
        catalog=load_scanner_catalog(data_root),
        data_root=data_root,
        run_root=run_root,
        through=request.through,
        repository_root=_path(
            getattr(settings, "repository_root"), field="repository_root"
        ),
    )
    checkpoint_ids: list[JsonValue] = []
    for path in paths:
        manifest, _tables = validate_completed_generation(path)
        checkpoint_ids.append(str(manifest["checkpoint_id"]))
    return {"cohort_id": cohort_id, "checkpoint_ids": checkpoint_ids}


def _capture(
    request: CapturePublicEvidenceRequestDto,
    settings: object,
) -> dict[str, JsonValue]:
    kind = CaptureKind(request.kind)
    path = capture_public_spot(
        venue=request.venue,
        venue_symbol=request.venue_symbol,
        base=AssetId(request.base_asset),
        quote_asset=AssetId(request.quote_asset),
        capture_root=_path(getattr(settings, "capture_root"), field="capture_root"),
        kind=kind,
    )
    if kind is CaptureKind.METADATA:
        snapshots = read_public_market_metadata_snapshots(path)
    else:
        snapshots = read_public_book_snapshots(path)
    if not snapshots:
        raise RuntimeError("capture did not persist an observation")
    snapshot = snapshots[-1]
    return {
        "capture_snapshot_id": snapshot.snapshot_id,
        "venue": request.venue,
        "venue_symbol": request.venue_symbol,
        "kind": request.kind,
    }


def _qualify(
    request: QualificationRequestDto,
    settings: object,
) -> dict[str, JsonValue]:
    run_root = _path(getattr(settings, "run_root"), field="run_root")
    data_root = _path(getattr(settings, "data_root"), field="data_root")
    path = qualify_forward_with_qap(
        cohort_root=run_root / "scanner-forward" / request.cohort_id,
        checkpoint_id=request.checkpoint_id,
        as_of=request.as_of,
        requested_capital=Decimal(request.requested_capital),
        catalog=load_scanner_catalog(data_root),
        data_root=data_root,
        capture_root=_path(getattr(settings, "capture_root"), field="capture_root"),
        run_root=run_root,
        repository_root=_path(
            getattr(settings, "repository_root"), field="repository_root"
        ),
    )
    document = read_qualification(path)
    return {
        "qualification_id": str(document["qualification_id"]),
        "checkpoint_id": request.checkpoint_id,
        "cohort_id": request.cohort_id,
    }


def _execute(
    kind: OperationKind,
    payload: dict[str, JsonValue],
    settings: object,
) -> dict[str, JsonValue]:
    if kind is OperationKind.RUN_SCAN:
        return _run_scan(RunScanRequestDto.model_validate(payload), settings)
    if kind is OperationKind.GENERATE_ASSET_MOMENTUM:
        scan_id = str(payload["scan_id"])
        command = dict(payload)
        command.pop("scan_id")
        return _generate_momentum(
            MomentumGenerationRequestDto.model_validate(command),
            settings,
            scan_id=scan_id,
        )
    if kind is OperationKind.FREEZE_FORWARD_COHORT:
        return _freeze(FreezeForwardCohortRequestDto.model_validate(payload), settings)
    if kind is OperationKind.ADVANCE_FORWARD_COHORT:
        cohort_id = str(payload["cohort_id"])
        command = dict(payload)
        command.pop("cohort_id")
        return _advance(
            AdvanceForwardCohortRequestDto.model_validate(command),
            settings,
            cohort_id=cohort_id,
        )
    if kind is OperationKind.CAPTURE_PUBLIC_EVIDENCE:
        return _capture(
            CapturePublicEvidenceRequestDto.model_validate(payload),
            settings,
        )
    if kind is OperationKind.QUALIFY_CANDIDATE:
        return _qualify(QualificationRequestDto.model_validate(payload), settings)
    raise RuntimeError(f"unsupported operation kind: {kind.value}")


def run(run_root: Path, operation_id: str) -> int:
    try:
        store = OperationStore(run_root)
        request = store.read_request(operation_id)
        result = (
            execute_pair_rotation(request, store)
            if request.kind
            in {
                OperationKind.REFRESH_COIN_DIRECTORY,
                OperationKind.PREPARE_PAIR_ROTATION_DATA,
            }
            else _execute(request.kind, request.request_summary, request.settings)
        )
        store.finish(
            operation_id,
            status=OperationStatus.COMPLETED,
            result=result,
        )
        return 0
    except BaseException as exc:
        traceback.print_exc()
        try:
            OperationStore(run_root).finish(
                operation_id,
                status=OperationStatus.FAILED,
                failure_code=exc.code
                if isinstance(exc, ApiBoundaryError)
                else type(exc).__name__,
                failure_message=exc.message
                if isinstance(exc, ApiBoundaryError)
                else "Operation failed. See local worker log for details.",
            )
        except BaseException:
            traceback.print_exc()
        return 1


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 2:
        print(
            "usage: python -m qap.api.operation_worker <run_root> <operation_id>",
            file=sys.stderr,
        )
        return 2
    return run(Path(arguments[0]).resolve(), arguments[1])


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
