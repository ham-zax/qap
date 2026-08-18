"""Validated read models over terminal Scanner-V1 basket artifacts."""

from pathlib import Path

from qap.api.basket_schemas import (
    BasketDetailDto,
    BasketEdgeDto,
    BasketListDto,
    BasketSummaryDto,
)
from qap.api.errors import ApiBoundaryError
from qap.api.schemas import ErrorDetailDto
from qap.scanner.basket_artifacts import BasketArtifactError, read_basket_generation


def _identity(value: str) -> str:
    normalized = value.strip().lower()
    invalid_character = any(char not in "0123456789abcdef" for char in normalized)
    if len(normalized) != 64 or invalid_character:
        raise _not_found(value)
    return normalized


def _not_found(basket_id: str) -> ApiBoundaryError:
    return ApiBoundaryError(
        code="basket_not_found",
        message="Basket was not found.",
        status_code=404,
        context={"basket_id": basket_id},
    )


def _invalid(basket_id: str) -> ApiBoundaryError:
    return ApiBoundaryError(
        code="basket_artifact_invalid",
        message="Basket artifact is invalid.",
        status_code=409,
        context={"basket_id": basket_id},
    )


def _error_detail(error: ApiBoundaryError) -> ErrorDetailDto:
    return ErrorDetailDto(
        code=error.code,
        message=error.message,
        context=error.context,
    )


class BasketArtifactReader:
    """Project completed immutable basket generations into HTTP DTOs."""

    def __init__(self, run_root: Path) -> None:
        self.root = run_root.resolve() / "baskets"

    def _directories(self) -> tuple[Path, ...]:
        if not self.root.is_dir():
            return ()
        return tuple(
            path
            for path in sorted(self.root.iterdir())
            if path.is_dir()
            and not path.name.endswith(".partial")
            and len(path.name) == 64
            and all(char in "0123456789abcdef" for char in path.name.lower())
        )

    @staticmethod
    def _summary(definition: object, attempt: object) -> BasketSummaryDto:
        basket = definition
        replay = attempt
        return BasketSummaryDto.model_validate(
            {
                "artifact_status": "valid",
                "basket_id": getattr(basket, "basket_id"),
                "source_scan_id": getattr(basket, "source_scan_id"),
                "source_momentum_scan_id": getattr(basket, "source_momentum_scan_id"),
                "source_as_of": getattr(basket, "source_as_of"),
                "venue": getattr(basket, "venue"),
                "horizon": getattr(basket, "horizon").value,
                "decision_resolution": getattr(basket, "decision_resolution"),
                "economic_assets": getattr(basket, "economic_assets"),
                "forensic": getattr(basket, "forensic"),
                "attempt_status": getattr(replay, "status").value,
                "economic_gate_status": (
                    None
                    if getattr(replay, "economic_gate_status") is None
                    else getattr(replay, "economic_gate_status").value
                ),
                "qap_run_id": getattr(replay, "qap_run_id"),
            }
        )

    def list_baskets(self) -> BasketListDto:
        items: list[BasketSummaryDto] = []
        for directory in self._directories():
            try:
                definition, attempt, _manifest = read_basket_generation(directory)
                items.append(self._summary(definition, attempt))
            except OSError, BasketArtifactError, TypeError, ValueError:
                error = _invalid(directory.name)
                items.append(
                    BasketSummaryDto(
                        artifact_status="invalid",
                        basket_id=directory.name,
                        error=_error_detail(error),
                    )
                )
        items.sort(
            key=lambda item: (
                item.source_as_of is not None,
                item.source_as_of,
                item.basket_id,
            ),
            reverse=True,
        )
        return BasketListDto(items=tuple(items))

    def basket_detail(self, basket_id: str) -> BasketDetailDto:
        identity = _identity(basket_id)
        directory = self.root / identity
        if not directory.is_dir():
            raise _not_found(identity)
        try:
            definition, attempt, _manifest = read_basket_generation(directory)
        except (OSError, BasketArtifactError, TypeError, ValueError) as exc:
            raise _invalid(identity) from exc
        edges = tuple(
            BasketEdgeDto(
                candidate_id=edge.candidate_id,
                pair_id=edge.pair_id,
                asset_a=edge.asset_a,
                asset_b=edge.asset_b,
                candidate_orientation=edge.candidate_orientation,
                resolution=edge.resolution,
                model_family=edge.model_family.value,
                template_id=edge.template_id.value,
                automatic_neighbor_selected=edge.automatic_neighbor_selected,
                manual_pinned=edge.manual_pinned,
                automatic_selected=edge.automatic_selected,
                manual_selected=edge.manual_selected,
                deep_replay_status=edge.deep_replay_status,
                deep_replay_failure_reason=edge.deep_replay_failure_reason,
                deep_replay_run_id=edge.deep_replay_run_id,
                economic_gate_status=edge.economic_gate_status,
            )
            for edge in definition.selected_edges
        )
        qap_run_id = attempt.qap_run_id
        return BasketDetailDto(
            summary=self._summary(definition, attempt),
            selected_edges=edges,
            qap_experiment_run_id=qap_run_id,
            qap_portfolio_run_id=qap_run_id,
            resolver_audit_available=qap_run_id is not None,
        )


__all__ = ["BasketArtifactReader"]
