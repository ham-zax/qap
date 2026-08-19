"""Longitudinal History composition over existing immutable evidence readers."""

from qap.api.basket_schemas import BasketSummaryDto
from qap.api.basket_views import BasketArtifactReader
from qap.api.history_schemas import (
    HistoryDto,
    HistoryResearchGenerationDto,
    HistoryResearchIdeaDto,
)
from qap.api.paper_operation_views import PaperOperationReader
from qap.api.readers import RunArtifactReader
from qap.api.scanner_views import ScannerArtifactReader


class HistoryReader:
    """Compose normal-user History without creating another evidence authority."""

    def __init__(
        self,
        *,
        scanner: ScannerArtifactReader,
        baskets: BasketArtifactReader,
        runs: RunArtifactReader,
        paper: PaperOperationReader,
    ) -> None:
        self._scanner = scanner
        self._baskets = baskets
        self._runs = runs
        self._paper = paper

    def read(self) -> HistoryDto:
        baskets = self._baskets.list_baskets().items
        baskets_by_id: dict[str, BasketSummaryDto] = {
            basket.basket_id: basket for basket in baskets
        }
        owned_run_ids = {
            basket.qap_run_id for basket in baskets if basket.qap_run_id is not None
        }
        owned_forward_ids: set[str] = set()
        generations: list[HistoryResearchGenerationDto] = []

        for scan in self._scanner.list_scans().items:
            ideas: list[HistoryResearchIdeaDto] = []
            if scan.artifact_status == "valid":
                candidates = self._scanner.list_candidates(scan.scan_id).items
                for candidate in candidates:
                    if candidate.economic_gate_status != "deep_replay_survivor":
                        continue
                    detail = self._scanner.candidate_detail(
                        scan.scan_id,
                        candidate.candidate_id,
                    )
                    longitudinal = detail.longitudinal
                    if candidate.deep_replay_run_id is not None:
                        owned_run_ids.add(candidate.deep_replay_run_id)
                    for membership in longitudinal.memberships:
                        owned_forward_ids.add(membership.selection_cohort_id)
                        owned_forward_ids.add(membership.active_cohort_id)
                        owned_run_ids.update(
                            checkpoint.qap_run_id
                            for checkpoint in membership.checkpoints
                            if checkpoint.qap_run_id is not None
                        )
                    forward_ids = tuple(
                        sorted(
                            {
                                cohort_id
                                for membership in longitudinal.memberships
                                for cohort_id in (
                                    membership.selection_cohort_id,
                                    membership.active_cohort_id,
                                )
                            }
                        )
                    )
                    memberships = tuple(
                        baskets_by_id[basket_id]
                        for basket_id in detail.basket_ids
                        if basket_id in baskets_by_id
                    )
                    assessments = longitudinal.current_assessments
                    ideas.append(
                        HistoryResearchIdeaDto(
                            candidate=detail.candidate,
                            longitudinal=longitudinal,
                            latest_current_assessment=(
                                None if not assessments else assessments[-1]
                            ),
                            forward_cohort_ids=forward_ids,
                            basket_memberships=memberships,
                        )
                    )
            generations.append(
                HistoryResearchGenerationDto(
                    summary=scan,
                    research_ideas=tuple(ideas),
                )
            )

        forward = self._scanner.list_forward_cohorts().items
        specialist_forward = tuple(
            cohort for cohort in forward if cohort.cohort_id not in owned_forward_ids
        )
        other_runs = tuple(
            run
            for run in self._runs.list_experiments().items
            if run.run_id not in owned_run_ids
        )
        return HistoryDto(
            research_generations=tuple(generations),
            specialist_forward_evidence=specialist_forward,
            portfolio_research=baskets,
            other_research_runs=other_runs,
            paper_operations=self._paper.list(),
        )


__all__ = ["HistoryReader"]
