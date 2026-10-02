"""Compose directory, identity and immutable inputs through existing owners."""

from pathlib import Path

from pydantic import JsonValue

from qap.api.errors import ApiBoundaryError
from qap.api.operations import OperationKind, OperationRequestRecord, OperationStore
from qap.api.pair_rotation_schemas import PairRotationRequestDto
from qap.market import BarInterval
from qap.product_market_data import ProductMarketData, ProductMarketDataError
from qap.product_market_data_prepare import (
    ProductMarketDataPreparationError,
    product_dataset_id,
)
from qap.product_pair_rotation_data import PairRotationData
from qap.product_universe import ProductUniverse, ProductUniverseError


def execute_pair_rotation(
    request: OperationRequestRecord,
    store: OperationStore,
) -> dict[str, JsonValue]:
    root = Path(request.settings.run_root)
    universe = ProductUniverse(root)

    def progress(stage: str, done: int, total: int) -> None:
        store.update_progress(request.operation_id, stage, done, total)

    try:
        progress("directory", 0, 1)
        if (
            request.kind is OperationKind.REFRESH_COIN_DIRECTORY
            or universe.read_directory() is None
        ):
            universe.refresh_directory()
        progress("identity", 0, 1)
        registry = universe.refresh_identity_evidence()
        if request.kind is OperationKind.REFRESH_COIN_DIRECTORY:
            progress("directory ready", 1, 1)
            directory = universe.read_directory()
            assert directory is not None
            return {
                "directory_id": directory.directory_id,
                "registry_status": registry.status,
                "registry_failure": registry.failure,
                "pending_admission_asset_ids": list(
                    universe.read_state().pending_admission_asset_ids
                ),
            }
        command = PairRotationRequestDto.model_validate(request.request_summary)
        scope = universe.research_scope((command.coin_a, command.coin_b))
        data_root = (
            None
            if request.settings.data_root is None
            else Path(request.settings.data_root)
        )
        data = ProductMarketData(root, data_root)
        projection = PairRotationData(universe, data).prepare(
            scope,
            lookback_days=command.lookback_days,
            progress=progress,
        )
        # Identify exact immutable generations by the requested evidence versions.
        ids = {
            product_dataset_id(item, BarInterval(interval))
            for item in scope.instruments
            for interval in ("15m", "1h", "4h", "1d")
        }
        datasets: list[JsonValue] = [
            {
                "dataset_id": item.dataset_id,
                "semantic_fingerprint": item.semantic_fingerprint,
                "venue_symbol": item.venue_symbol,
                "interval": item.interval,
                "coverage_start": None
                if item.coverage_start is None
                else item.coverage_start.isoformat(),
                "cutoff": None
                if item.coverage_end_exclusive is None
                else item.coverage_end_exclusive.isoformat(),
            }
            for item in projection.generations
            if item.dataset_id in ids
        ]
        if len(datasets) != len(ids):
            raise ProductMarketDataPreparationError("Pair data is incomplete.")
        progress("data ready", len(ids), len(ids))
        return {
            "coin_a": command.coin_a,
            "coin_b": command.coin_b,
            "datasets": datasets,
            "identity_confirmed": scope.economic_identity_confirmed,
            "admission_required": False,
            "registry_status": registry.status,
            "registry_failure": registry.failure,
        }
    except ProductUniverseError as exc:
        raise ApiBoundaryError(
            code="pair_rotation_scope_unavailable",
            message=str(exc),
            status_code=409,
            context={},
        ) from exc
    except (ProductMarketDataError, ProductMarketDataPreparationError) as exc:
        raise ApiBoundaryError(
            code="pair_rotation_data_unavailable",
            message=str(exc),
            status_code=502,
            context={},
        ) from exc
