"""Read-only repository adapter over immutable Phase-07 run artifacts."""

import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from qap.api.errors import ApiBoundaryError, corrupt_artifact, run_not_found
from qap.api.portfolio_views import (
    portfolio_performance as project_portfolio_performance,
)
from qap.api.portfolio_views import portfolio_snapshot as project_portfolio_snapshot
from qap.api.relationship_views import anchor_lens as project_anchor_lens
from qap.api.relationship_views import pair_series as project_pair_series
from qap.api.schemas import (
    AnchorLensDto,
    ArtifactSeriesMetadataDto,
    ErrorDetailDto,
    ExperimentDetailDto,
    ExperimentListDto,
    ExperimentSummaryDto,
    PairSeriesDto,
    PortfolioPerformanceDto,
    PortfolioSnapshotDto,
)
from qap.experiment import LoadedRunArtifacts, read_run_artifacts

_RUN_ID = re.compile(r"run-[0-9a-f]{24}")
_MIN_UTC = datetime.min.replace(tzinfo=UTC)


class RunArtifactReader:
    """Validate immutable run directories and project them into HTTP DTOs."""

    def __init__(self, run_root: Path, market_data_root: Path | None = None) -> None:
        self.run_root = run_root.resolve()
        self.market_data_root = (
            None if market_data_root is None else market_data_root.resolve()
        )

    def _directory(self, run_id: str) -> Path:
        normalized = run_id.strip().lower()
        if _RUN_ID.fullmatch(normalized) is None:
            raise run_not_found(run_id)
        directory = self.run_root / normalized
        if not directory.is_dir() or not (directory / "result.json").is_file():
            raise run_not_found(normalized)
        return directory

    def read(self, run_id: str) -> LoadedRunArtifacts:
        directory = self._directory(run_id)
        try:
            return read_run_artifacts(directory)
        except (OSError, TypeError, ValueError, RuntimeError) as exc:
            raise corrupt_artifact(directory.name) from exc

    def _directories(self) -> tuple[Path, ...]:
        if not self.run_root.is_dir():
            return ()
        return tuple(
            path
            for path in sorted(self.run_root.iterdir())
            if path.is_dir() and _RUN_ID.fullmatch(path.name) is not None
        )

    def _valid_runs(self) -> dict[str, LoadedRunArtifacts]:
        valid: dict[str, LoadedRunArtifacts] = {}
        for directory in self._directories():
            try:
                valid[directory.name] = self.read(directory.name)
            except ApiBoundaryError:
                continue
        return valid

    def list_experiments(self) -> ExperimentListDto:
        valid = self._valid_runs()
        family_counts = Counter(
            item.result.research_family_id for item in valid.values()
        )
        items: list[ExperimentSummaryDto] = []
        for directory in self._directories():
            loaded = valid.get(directory.name)
            if loaded is None:
                error = corrupt_artifact(directory.name)
                items.append(
                    ExperimentSummaryDto(
                        artifact_status="invalid",
                        run_id=directory.name,
                        error=ErrorDetailDto(
                            code=error.code,
                            message=error.message,
                            context=error.context,
                        ),
                    )
                )
                continue
            result = loaded.result
            items.append(
                ExperimentSummaryDto(
                    artifact_status="valid",
                    run_id=loaded.provenance.run_id,
                    experiment_name=loaded.manifest.experiment_name,
                    research_family_id=result.research_family_id,
                    parent_run_id=result.parent_run_id,
                    universe_mode=loaded.manifest.universe_mode.value,
                    basket=loaded.manifest.basket,
                    analysis_anchor=loaded.manifest.analysis_anchor,
                    relationship_id=loaded.manifest.relationship.component_id,
                    policy_id=loaded.manifest.policy.component_id,
                    data_role=result.data_role.value,
                    final_oos_consumed=result.final_oos_consumed,
                    status=result.status.value,
                    primary_metric=result.primary_metric.value,
                    primary_metric_value=str(result.primary_metric_value),
                    primary_incremental_benchmark=result.primary_incremental_benchmark,
                    incremental_vs_primary_control=(
                        None
                        if result.strategy_vs_primary_control is None
                        else str(result.strategy_vs_primary_control)
                    ),
                    incremental_vs_matched_contribution=(
                        None
                        if result.strategy_vs_matched_contribution is None
                        else str(result.strategy_vs_matched_contribution)
                    ),
                    created_timestamp=loaded.provenance.run_timestamp_utc,
                    git_dirty=loaded.provenance.git_dirty,
                    sibling_trial_count=family_counts[result.research_family_id],
                )
            )
        items.sort(
            key=lambda item: (
                item.created_timestamp is not None,
                item.created_timestamp or _MIN_UTC,
                item.run_id,
            ),
            reverse=True,
        )
        return ExperimentListDto(items=tuple(items))

    def experiment_detail(self, run_id: str) -> ExperimentDetailDto:
        loaded = self.read(run_id)
        siblings = sum(
            item.result.research_family_id == loaded.result.research_family_id
            for item in self._valid_runs().values()
        )
        return ExperimentDetailDto(
            run_id=loaded.provenance.run_id,
            sibling_trial_count=siblings,
            manifest=loaded.manifest,
            provenance=loaded.provenance,
            result=loaded.result,
            final_oos_commitment=loaded.commitment,
            available_series=(
                _artifact_series_metadata("performance", loaded.performance),
                _artifact_series_metadata("inventory", loaded.inventory),
            ),
        )

    def portfolio_snapshot(self, run_id: str) -> PortfolioSnapshotDto:
        return project_portfolio_snapshot(self.read(run_id))

    def portfolio_performance(self, run_id: str) -> PortfolioPerformanceDto:
        return project_portfolio_performance(self.read(run_id))

    def pair_series(
        self,
        *,
        run_id: str,
        asset_x: str,
        asset_y: str,
        orientation: str | None,
    ) -> PairSeriesDto:
        return project_pair_series(
            self.read(run_id),
            market_data_root=self.market_data_root,
            asset_x=asset_x,
            asset_y=asset_y,
            orientation=orientation,
        )

    def anchor_lens(
        self,
        *,
        run_id: str,
        asset_x: str,
        asset_y: str,
        anchor: str,
        orientation: str | None,
    ) -> AnchorLensDto:
        return project_anchor_lens(
            self.read(run_id),
            market_data_root=self.market_data_root,
            asset_x=asset_x,
            asset_y=asset_y,
            anchor=anchor,
            orientation=orientation,
        )


def _artifact_series_metadata(
    name: str,
    table: Any,
) -> ArtifactSeriesMetadataDto:
    raw_metadata = cast(object, table.schema.metadata)
    if raw_metadata is None:
        metadata: dict[bytes, bytes] = {}
    elif isinstance(raw_metadata, dict):
        metadata = cast(dict[bytes, bytes], raw_metadata)
    else:
        raise ValueError(f"{name} artifact metadata must be a mapping")
    raw_schema = metadata.get(b"qap_schema")
    if not isinstance(raw_schema, bytes):
        raise ValueError(f"{name} artifact is missing qap_schema metadata")
    return ArtifactSeriesMetadataDto(
        name=name,
        schema_version=raw_schema.decode("utf-8"),
        columns=tuple(str(column) for column in table.schema.names),
        row_count=int(table.num_rows),
    )


__all__ = ["RunArtifactReader"]
