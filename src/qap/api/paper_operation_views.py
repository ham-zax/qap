"""Read-only projections over immutable forward-paper operation artifacts."""

from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from qap.api.errors import ApiBoundaryError
from qap.api.paper_operation_schemas import (
    PaperMarketMetadataDto,
    PaperOperationDetailDto,
    PaperOperationFillDto,
    PaperOperationOrderDto,
    PaperOperationSummaryDto,
    PaperResearchBoundaryDto,
)
from qap.experiment.paper_operation import read_paper_operation_artifact


class PaperOperationReader:
    """Read immutable paper-operation files from one configured root."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _operation_file(self, operation_id: str) -> Path:
        if not operation_id or "/" in operation_id or "\\" in operation_id:
            raise _not_found(operation_id)
        path = self.root / operation_id / "paper_operation.json"
        if not path.is_file():
            raise _not_found(operation_id)
        return path

    def detail(self, operation_id: str) -> PaperOperationDetailDto:
        try:
            raw = read_paper_operation_artifact(self._operation_file(operation_id))
            orders = tuple(
                PaperOperationOrderDto.model_validate(item)
                for item in _object_array(raw.get("orders"), field="orders")
            )
            fills = tuple(
                PaperOperationFillDto.model_validate(item)
                for item in _object_array(raw.get("fills"), field="fills")
            )
            metadata = {
                symbol: PaperMarketMetadataDto.model_validate(item)
                for symbol, item in _object_mapping(
                    raw.get("market_metadata"), field="market_metadata"
                ).items()
            }
            research_boundary = PaperResearchBoundaryDto.model_validate(
                _object(raw.get("research_boundary"), field="research_boundary")
            )
            reconciliation = _object(raw.get("reconciliation"), field="reconciliation")
            return PaperOperationDetailDto(
                operation_id=_text(raw, "operation_id"),
                data_role="forward_paper",
                execution_timestamp=datetime.fromisoformat(
                    _text(raw, "execution_timestamp")
                ),
                input_fingerprint=_text(raw, "input_fingerprint"),
                source_note=_text(raw, "source_note"),
                bridge=_text(raw, "bridge"),
                starting_holdings=_string_mapping(raw, "starting_holdings"),
                target_weights=_string_mapping(raw, "target_weights"),
                valuation_prices=_string_mapping(raw, "valuation_prices"),
                reference_prices=_string_mapping(raw, "reference_prices"),
                market_metadata=metadata,
                orders=orders,
                fills=fills,
                ending_holdings=_string_mapping(raw, "ending_holdings"),
                bridge_target_quantity=_text(raw, "bridge_target_quantity"),
                bridge_residual=_text(raw, "bridge_residual"),
                total_fee_quote=_text(raw, "total_fee_quote"),
                total_slippage_quote=_text(raw, "total_slippage_quote"),
                reconciliation_matches=_bool(reconciliation, "matches"),
                research_boundary=research_boundary,
            )
        except ApiBoundaryError:
            raise
        except (OSError, TypeError, ValueError) as exc:
            raise ApiBoundaryError(
                status_code=500,
                code="corrupt_paper_operation",
                message="Paper operation artifact is corrupt.",
                context={"operation_id": operation_id},
            ) from exc

    def list(self) -> tuple[PaperOperationSummaryDto, ...]:
        if not self.root.exists():
            return ()
        summaries: list[PaperOperationSummaryDto] = []
        for directory in sorted(self.root.iterdir(), key=lambda path: path.name):
            if not directory.is_dir():
                continue
            operation_file = directory / "paper_operation.json"
            if not operation_file.is_file():
                continue
            detail = self.detail(directory.name)
            summaries.append(
                PaperOperationSummaryDto(
                    operation_id=detail.operation_id,
                    data_role="forward_paper",
                    execution_timestamp=detail.execution_timestamp,
                    reconciliation_matches=detail.reconciliation_matches,
                    fill_count=len(detail.fills),
                    total_fee_quote=detail.total_fee_quote,
                    total_slippage_quote=detail.total_slippage_quote,
                    bridge_residual=detail.bridge_residual,
                    route_ids=tuple(order.route_id for order in detail.orders),
                )
            )
        return tuple(summaries)


def _not_found(operation_id: str) -> ApiBoundaryError:
    return ApiBoundaryError(
        status_code=404,
        code="paper_operation_not_found",
        message="Paper operation was not found.",
        context={"operation_id": operation_id},
    )


def _object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return cast(dict[str, Any], value)


def _object_array(value: object, *, field: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    result: list[dict[str, Any]] = []
    for index, item in enumerate(cast(list[object], value)):
        result.append(_object(item, field=f"{field}[{index}]"))
    return tuple(result)


def _object_mapping(value: object, *, field: str) -> dict[str, dict[str, Any]]:
    raw = _object(value, field=field)
    return {key: _object(item, field=f"{field}.{key}") for key, item in raw.items()}


def _text(source: Mapping[str, Any], field: str) -> str:
    value = source.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _bool(source: Mapping[str, Any], field: str) -> bool:
    value = source.get(field)
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


def _string_mapping(source: Mapping[str, Any], field: str) -> dict[str, str]:
    raw = _object(source.get(field), field=field)
    result: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(value, str):
            raise ValueError(f"{field}.{key} must be a string")
        result[key] = value
    return result


__all__ = ["PaperOperationReader"]
