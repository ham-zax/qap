"""Detached worker for one durable local research operation."""

import sys
import traceback
from pathlib import Path

from qap.api.errors import ApiBoundaryError
from qap.api.operations import (
    OperationKind,
    OperationStatus,
    OperationStore,
)
from qap.api.pair_rotation_worker import execute_pair_rotation


def run(run_root: Path, operation_id: str) -> int:
    try:
        store = OperationStore(run_root)
        request = store.read_request(operation_id)
        if request.kind not in {
            OperationKind.REFRESH_COIN_DIRECTORY,
            OperationKind.PREPARE_PAIR_ROTATION_DATA,
        }:
            raise RuntimeError(f"unsupported operation kind: {request.kind.value}")
        result = execute_pair_rotation(request, store)
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
