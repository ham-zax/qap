"""Compose directory, identity and immutable inputs through existing owners."""

from pathlib import Path

from pydantic import JsonValue

from qap.api.errors import ApiBoundaryError
from qap.api.operations import OperationKind, OperationRequestRecord, OperationStore
from qap.api.pair_rotation_schemas import PairRotationRequestDto
from qap.market import BarInterval
from qap.market.adapters.binance_public import BinancePublicDataError
from qap.market.microstructure_storage import MicrostructureStorageError
from qap.product_lab_metadata import capture_lab_metadata
from qap.product_market_data import ProductMarketData, ProductMarketDataError
from qap.product_market_data_prepare import (
    ProductMarketDataPreparationError,
    product_dataset_id,
)
from qap.product_pair_rotation_data import PairRotationData
from qap.product_pair_rotation_markets import direct_instrument
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
        if request.kind is OperationKind.REFRESH_COIN_DIRECTORY:
            progress("identity", 0, 1)
            registry = universe.refresh_identity_evidence()
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
        # Venue-local charts do not need an economic identity. Registry refresh
        # has its own operation and must not delay ordinary pair preparation.
        registry_status = (
            "unavailable" if universe.registry_snapshot() is None else "cached"
        )
        command = PairRotationRequestDto.model_validate(request.request_summary)
        scope = universe.research_scope((command.coin_a, command.coin_b))
        data_root = (
            None
            if request.settings.data_root is None
            else Path(request.settings.data_root)
        )
        data = ProductMarketData(root, data_root)
        preparer = PairRotationData(universe, data)
        if command.include_execution or command.base_interval != "15m":
            projection = preparer.prepare(
                scope,
                lookback_days=command.lookback_days,
                progress=progress,
                base_interval=command.base_interval,
                include_execution=command.include_execution,
            )
        else:
            projection = preparer.prepare(
                scope, lookback_days=command.lookback_days, progress=progress
            )
        extra = (
            direct_instrument(universe, scope) if command.include_execution else None
        )
        instruments = (
            scope.instruments if extra is None else (*scope.instruments, extra)
        )
        intervals = (
            ("1m",) if command.base_interval == "1m" else ("15m", "1h", "4h", "1d")
        )
        metadata_failure = None
        if command.include_execution and data_root is not None:
            progress("venue constraints", 0, len(instruments))
            try:
                capture_lab_metadata(universe, data_root, instruments)
            except (
                BinancePublicDataError,
                MicrostructureStorageError,
                OSError,
                ValueError,
            ) as exc:
                metadata_failure = str(exc)
        # Identify exact immutable generations by the requested evidence versions.
        ids = {
            product_dataset_id(item, BarInterval(interval))
            for item in instruments
            for interval in intervals
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
            "registry_status": registry_status,
            "registry_failure": None,
            "execution_metadata_failure": metadata_failure,
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
