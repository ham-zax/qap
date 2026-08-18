# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Validated read models over Scanner-V1 discovery/prospective artifacts."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from qap.api.errors import ApiBoundaryError
from qap.api.scanner_schemas import (
    CandidateDetailDto,
    CandidateFreezeDto,
    CandidateListDto,
    CandidateSummaryDto,
    ForwardCheckpointDto,
    ForwardCohortDetailDto,
    ForwardCohortListDto,
    ForwardCohortSummaryDto,
    GraphScopeDto,
    MomentumGenerationDto,
    MomentumObservationDto,
    QualificationDto,
    ScanDetailDto,
    ScanListDto,
    ScannerHorizonDto,
    ScannerProtocolDto,
    ScanSummaryDto,
    UniverseAssetDto,
)
from qap.api.schemas import ErrorDetailDto
from qap.scanner.artifacts import ScanArtifactError, read_completed_scan
from qap.scanner.asset_momentum_artifacts import (
    AssetMomentumArtifactError,
    read_asset_momentum_generation,
)
from qap.scanner.basket_artifacts import BasketArtifactError, read_basket_generation
from qap.scanner.basket_protocol import (
    SCANNER_V1_BASKET,
    basket_protocol_identity,
)
from qap.scanner.prospective_artifact_schemas import CHECKPOINT_TABLE
from qap.scanner.prospective_artifacts import (
    ProspectiveArtifactError,
    read_completed_checkpoints,
    read_forward_cohort,
)
from qap.scanner.prospective_integrity import (
    read_outcome,
    validate_completed_generation,
)
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon, protocol_identity
from qap.scanner.qualification_artifacts import (
    QualificationArtifactError,
    read_qualifications,
)


def _identity(value: str, *, kind: str) -> str:
    normalized = value.strip().lower()
    invalid_character = any(char not in "0123456789abcdef" for char in normalized)
    if len(normalized) != 64 or invalid_character:
        raise ApiBoundaryError(
            code=f"{kind}_not_found",
            message=f"{kind.replace('_', ' ').title()} was not found.",
            status_code=404,
            context={f"{kind}_id": value},
        )
    return normalized


def _not_found(kind: str, identity: str) -> ApiBoundaryError:
    return ApiBoundaryError(
        code=f"{kind}_not_found",
        message=f"{kind.replace('_', ' ').title()} was not found.",
        status_code=404,
        context={f"{kind}_id": identity},
    )


def _invalid(kind: str, identity: str) -> ApiBoundaryError:
    return ApiBoundaryError(
        code=f"{kind}_artifact_invalid",
        message=f"{kind.replace('_', ' ').title()} artifact is invalid.",
        status_code=409,
        context={f"{kind}_id": identity},
    )


def _error_detail(error: ApiBoundaryError) -> ErrorDetailDto:
    return ErrorDetailDto(
        code=error.code,
        message=error.message,
        context=error.context,
    )


def _directories(root: Path) -> tuple[Path, ...]:
    if not root.is_dir():
        return ()
    return tuple(
        path
        for path in sorted(root.iterdir())
        if path.is_dir()
        and not path.name.endswith(".partial")
        and len(path.name) == 64
        and all(char in "0123456789abcdef" for char in path.name.lower())
    )


def _mapping(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    return cast(Mapping[str, object], value)


class ScannerArtifactReader:
    """Project scanner artifacts into stable HTTP DTOs without weakening validation."""

    def __init__(self, run_root: Path) -> None:
        self.run_root = run_root.resolve()
        self.scan_root = self.run_root / "scans"
        self.momentum_root = self.run_root / "asset-momentum"
        self.forward_root = self.run_root / "scanner-forward"
        self.basket_root = self.run_root / "baskets"

    def protocol(self) -> ScannerProtocolDto:
        horizons: list[ScannerHorizonDto] = []
        for horizon in ScannerHorizon:
            source = SCANNER_V1_SLICE1.horizon(horizon)
            momentum = SCANNER_V1_BASKET.momentum_rule(horizon)
            horizons.append(
                ScannerHorizonDto(
                    horizon=horizon.value,
                    graph_interval=source.graph_interval.label,
                    graph_window_seconds=int(source.graph_window.total_seconds()),
                    evaluation_window_seconds=int(
                        source.evaluation_window.total_seconds()
                    ),
                    model_resolutions=tuple(
                        interval.label for interval in source.model_resolutions
                    ),
                    momentum_resolution=momentum.resolution.label,
                    momentum_formation_seconds=int(momentum.formation.total_seconds()),
                )
            )
        return ScannerProtocolDto(
            protocol_id=SCANNER_V1_SLICE1.protocol_id,
            protocol_identity=protocol_identity(SCANNER_V1_SLICE1),
            basket_protocol_id=SCANNER_V1_BASKET.protocol_id,
            basket_protocol_identity=basket_protocol_identity(SCANNER_V1_BASKET),
            venues=SCANNER_V1_SLICE1.venues,
            quote_asset=SCANNER_V1_SLICE1.quote_asset,
            horizons=tuple(horizons),
        )

    def _scan(self, scan_id: str) -> tuple[object, dict[str, list[dict[str, Any]]]]:
        identity = _identity(scan_id, kind="scan")
        directory = self.scan_root / identity
        if not directory.is_dir():
            raise _not_found("scan", identity)
        try:
            return read_completed_scan(directory)
        except (OSError, ScanArtifactError, TypeError, ValueError) as exc:
            raise _invalid("scan", identity) from exc

    @staticmethod
    def _summary(
        scan_id: str,
        definition: object,
        tables: dict[str, list[dict[str, Any]]],
    ) -> ScanSummaryDto:
        declared = cast(Any, definition)
        scouts = tables["scout_trials.parquet"]
        promotions = tables["promotions.parquet"]
        return ScanSummaryDto(
            artifact_status="valid",
            scan_id=scan_id,
            as_of=declared.as_of,
            eligible_information_end=declared.eligible_information_end,
            created_at=declared.created_at,
            venues=declared.venues,
            horizons=tuple(item.value for item in declared.horizons),
            candidate_count=len(scouts),
            selected_replay_count=sum(
                bool(row["selected_for_replay"]) for row in promotions
            ),
            survivor_count=sum(
                row["economic_gate_status"] == "deep_replay_survivor"
                for row in promotions
            ),
        )

    def list_scans(self) -> ScanListDto:
        items: list[ScanSummaryDto] = []
        for directory in _directories(self.scan_root):
            try:
                definition, tables = read_completed_scan(directory)
                items.append(self._summary(directory.name, definition, tables))
            except OSError, ScanArtifactError, TypeError, ValueError:
                error = _invalid("scan", directory.name)
                items.append(
                    ScanSummaryDto(
                        artifact_status="invalid",
                        scan_id=directory.name,
                        error=_error_detail(error),
                    )
                )
        items.sort(
            key=lambda item: (item.as_of is not None, item.as_of, item.scan_id),
            reverse=True,
        )
        return ScanListDto(items=tuple(items))

    def _momentum_for_scan(self, scan_id: str) -> tuple[MomentumGenerationDto, ...]:
        items: list[MomentumGenerationDto] = []
        for directory in _directories(self.momentum_root):
            try:
                generation, _snapshot = read_asset_momentum_generation(directory)
            except (OSError, AssetMomentumArtifactError, TypeError, ValueError) as exc:
                raise _invalid("momentum", directory.name) from exc
            if generation.source_scan_id != scan_id:
                continue
            items.append(
                MomentumGenerationDto(
                    momentum_scan_id=generation.momentum_scan_id,
                    source_scan_id=generation.source_scan_id,
                    venue=generation.venue,
                    horizon=generation.horizon.value,
                    as_of=generation.as_of,
                    universe_snapshot_id=generation.universe_snapshot_id,
                    resolution=generation.resolution,
                    formation_seconds=generation.formation_seconds,
                    observations=tuple(
                        MomentumObservationDto(
                            asset_id=item.asset_id,
                            venue_symbol=item.venue_symbol,
                            status=item.status.value,
                            reason=item.reason,
                            bar_coverage=item.bar_coverage,
                            longest_missing_run=item.longest_missing_run,
                            own_momentum=item.own_momentum,
                            common_mode=item.common_mode,
                            relative_momentum=item.relative_momentum,
                            common_mode_member_count=item.common_mode_member_count,
                            rank=item.rank,
                        )
                        for item in generation.observations
                    ),
                )
            )
        items.sort(key=lambda item: (item.venue, item.horizon, item.momentum_scan_id))
        return tuple(items)

    def scan_detail(self, scan_id: str) -> ScanDetailDto:
        definition, tables = self._scan(scan_id)
        declared = cast(Any, definition)
        summary = self._summary(declared.scan_id, definition, tables)
        universe = tuple(
            UniverseAssetDto(
                venue=str(row["venue"]),
                horizon=str(row["horizon"]),
                asset_id=str(row["asset_id"]),
                venue_symbol=str(row["venue_symbol"]),
                eligibility_state=str(row["eligibility_state"]),
                eligibility_reason=str(row["eligibility_reason"]),
                bar_coverage=float(row["bar_coverage"]),
                longest_missing_run=int(row["longest_missing_run"]),
                automatic_eligible=bool(row["automatic_eligible"]),
                forensic_research_allowed=bool(row["forensic_research_allowed"]),
            )
            for row in tables["eligible_assets.parquet"]
        )
        scopes = tuple(
            GraphScopeDto(
                venue=str(row["venue"]),
                horizon=str(row["horizon"]),
                universe_snapshot_id=str(row["universe_snapshot_id"]),
                graph_interval=str(row["graph_interval"]),
                graph_window_seconds=int(row["graph_window_seconds"]),
                eligible_asset_count=int(row["eligible_asset_count"]),
                total_valid_pair_comparisons=int(row["total_valid_pair_comparisons"]),
            )
            for row in tables["graph_metadata.parquet"]
        )
        return ScanDetailDto(
            summary=summary,
            universe=universe,
            graph_scopes=scopes,
            momentum_generations=self._momentum_for_scan(declared.scan_id),
        )

    @staticmethod
    def _candidates(
        tables: dict[str, list[dict[str, Any]]],
    ) -> tuple[CandidateSummaryDto, ...]:
        promotions = {
            str(row["candidate_id"]): row for row in tables["promotions.parquet"]
        }
        attempts = {
            str(row["candidate_id"]): row for row in tables["replay_attempts.parquet"]
        }
        items: list[CandidateSummaryDto] = []
        for scout in tables["scout_trials.parquet"]:
            candidate_id = str(scout["candidate_id"])
            promotion = promotions.get(candidate_id)
            attempt = attempts.get(candidate_id)
            items.append(
                CandidateSummaryDto(
                    candidate_id=candidate_id,
                    scan_id=str(scout["scan_id"]),
                    venue=str(scout["venue"]),
                    horizon=str(scout["horizon"]),
                    pair_id=str(scout["pair_id"]),
                    orientation=str(scout["orientation"]),
                    resolution=str(scout["resolution"]),
                    model_family=str(scout["model_family"]),
                    template_id=str(scout["template_id"]),
                    trial_status=str(scout["trial_status"]),
                    failure_reason=(
                        None
                        if scout["failure_reason"] is None
                        else str(scout["failure_reason"])
                    ),
                    scout_relative_wealth_proxy=scout["scout_relative_wealth_proxy"],
                    scout_turnover_proxy=scout["scout_turnover_proxy"],
                    signal_count=int(scout["signal_count"]),
                    automatic_neighbor_selected=bool(
                        scout["automatic_neighbor_selected"]
                    ),
                    manual_pinned=bool(scout["manual_pinned"]),
                    promotion_rank=(
                        None
                        if promotion is None or promotion["promotion_rank"] is None
                        else int(promotion["promotion_rank"])
                    ),
                    promotion_status=(
                        None
                        if promotion is None
                        else str(promotion["promotion_status"])
                    ),
                    budget_reason=(
                        None
                        if promotion is None or promotion["budget_reason"] is None
                        else str(promotion["budget_reason"])
                    ),
                    automatic_selected=(
                        False
                        if promotion is None
                        else bool(promotion["automatic_selected"])
                    ),
                    manual_selected=(
                        False
                        if promotion is None
                        else bool(promotion["manual_selected"])
                    ),
                    selected_for_replay=(
                        False
                        if promotion is None
                        else bool(promotion["selected_for_replay"])
                    ),
                    deep_replay_status=(
                        None
                        if promotion is None or promotion["deep_replay_status"] is None
                        else str(promotion["deep_replay_status"])
                    ),
                    deep_replay_run_id=(
                        None
                        if promotion is None or promotion["deep_replay_run_id"] is None
                        else str(promotion["deep_replay_run_id"])
                    ),
                    economic_gate_status=(
                        None
                        if promotion is None
                        or promotion["economic_gate_status"] is None
                        else str(promotion["economic_gate_status"])
                    ),
                    replay_failure_stage=(
                        None
                        if attempt is None or attempt["failure_stage"] is None
                        else str(attempt["failure_stage"])
                    ),
                    replay_failure_reason=(
                        None
                        if attempt is None or attempt["failure_reason"] is None
                        else str(attempt["failure_reason"])
                    ),
                )
            )
        items.sort(key=lambda item: item.candidate_id)
        return tuple(items)

    def list_candidates(self, scan_id: str) -> CandidateListDto:
        definition, tables = self._scan(scan_id)
        declared = cast(Any, definition)
        return CandidateListDto(
            scan_id=declared.scan_id,
            items=self._candidates(tables),
        )

    def _valid_cohorts(self) -> tuple[tuple[Path, Any], ...]:
        values: list[tuple[Path, Any]] = []
        for directory in _directories(self.forward_root):
            try:
                values.append((directory, read_forward_cohort(directory)))
            except (OSError, ProspectiveArtifactError, TypeError, ValueError) as exc:
                raise _invalid("forward_cohort", directory.name) from exc
        return tuple(values)

    def _basket_memberships(self, candidate_id: str) -> tuple[str, ...]:
        memberships: list[str] = []
        for directory in _directories(self.basket_root):
            try:
                definition, _attempt, _manifest = read_basket_generation(directory)
            except (OSError, BasketArtifactError, TypeError, ValueError) as exc:
                raise _invalid("basket", directory.name) from exc
            if any(
                edge.candidate_id == candidate_id for edge in definition.selected_edges
            ):
                memberships.append(definition.basket_id)
        return tuple(sorted(memberships))

    def candidate_detail(self, scan_id: str, candidate_id: str) -> CandidateDetailDto:
        candidates = self.list_candidates(scan_id).items
        identity = _identity(candidate_id, kind="candidate")
        candidate = next(
            (item for item in candidates if item.candidate_id == identity),
            None,
        )
        if candidate is None:
            raise _not_found("candidate", identity)
        cohort_ids: list[str] = []
        qualification_ids: list[str] = []
        for cohort_root, cohort in self._valid_cohorts():
            if identity not in cohort.candidate_ids:
                continue
            cohort_ids.append(cohort.cohort_id)
            try:
                qualifications = read_qualifications(cohort_root)
            except (OSError, QualificationArtifactError, TypeError, ValueError) as exc:
                raise _invalid("forward_cohort", cohort.cohort_id) from exc
            for qualification in qualifications:
                request = _mapping(qualification.get("request"), field="request")
                if request.get("candidate_id") == identity:
                    qualification_ids.append(str(qualification["qualification_id"]))
        return CandidateDetailDto(
            candidate=candidate,
            forward_cohort_ids=tuple(sorted(cohort_ids)),
            qualification_ids=tuple(sorted(qualification_ids)),
            basket_ids=self._basket_memberships(identity),
        )

    def _cohort_summary(self, root: Path, cohort: Any) -> ForwardCohortSummaryDto:
        try:
            checkpoints = read_completed_checkpoints(root)
            qualifications = read_qualifications(root)
        except (
            OSError,
            ProspectiveArtifactError,
            QualificationArtifactError,
            TypeError,
            ValueError,
        ) as exc:
            raise _invalid("forward_cohort", cohort.cohort_id) from exc
        return ForwardCohortSummaryDto(
            artifact_status="valid",
            cohort_id=cohort.cohort_id,
            source_scan_id=cohort.source_scan_id,
            horizon=cohort.horizon.value,
            freeze_at=cohort.freeze_at,
            candidate_ids=cohort.candidate_ids,
            checkpoint_count=len(checkpoints),
            qualification_count=len(qualifications),
        )

    def list_forward_cohorts(self) -> ForwardCohortListDto:
        items: list[ForwardCohortSummaryDto] = []
        for directory in _directories(self.forward_root):
            try:
                cohort = read_forward_cohort(directory)
                items.append(self._cohort_summary(directory, cohort))
            except (
                OSError,
                ProspectiveArtifactError,
                QualificationArtifactError,
                TypeError,
                ValueError,
            ):
                error = _invalid("forward_cohort", directory.name)
                items.append(
                    ForwardCohortSummaryDto(
                        artifact_status="invalid",
                        cohort_id=directory.name,
                        error=_error_detail(error),
                    )
                )
        items.sort(
            key=lambda item: (
                item.freeze_at is not None,
                item.freeze_at,
                item.cohort_id,
            ),
            reverse=True,
        )
        return ForwardCohortListDto(items=tuple(items))

    @staticmethod
    def _freeze_dto(freeze: Any) -> CandidateFreezeDto:
        return CandidateFreezeDto(
            freeze_id=freeze.freeze_id,
            candidate_id=freeze.candidate_id,
            source_scan_id=freeze.scan_id,
            automatic_selected=freeze.automatic_selected,
            manual_selected=freeze.manual_selected,
            frozen_at=freeze.frozen_at,
            forward_start=freeze.forward_start,
            forward_end=freeze.forward_end,
            horizon=freeze.horizon.value,
            venue=freeze.venue,
            pair_id=freeze.pair_id,
            orientation=freeze.orientation,
            resolution=freeze.resolution,
            model_family=freeze.model_family,
            template_id=freeze.template_id,
            candidate_deep_replay_run_id=freeze.candidate_deep_replay_run_id,
        )

    @staticmethod
    def _checkpoint_dto(directory: Path) -> ForwardCheckpointDto:
        manifest, tables = validate_completed_generation(directory)
        checkpoint = tables[CHECKPOINT_TABLE].to_pylist()[0]
        outcome = read_outcome(directory)
        return ForwardCheckpointDto(
            checkpoint_id=outcome.checkpoint_id,
            cohort_id=str(manifest["cohort_id"]),
            candidate_id=outcome.candidate_id,
            freeze_id=outcome.freeze_id,
            checkpoint_index=int(cast(Any, manifest["checkpoint_index"])),
            information_end=checkpoint["information_end"],
            outcome_id=outcome.outcome_id,
            outcome_status=outcome.status.value,
            qap_run_id=outcome.qap_run_id,
            strategy_vs_hodl=(
                None
                if outcome.strategy_vs_hodl is None
                else str(outcome.strategy_vs_hodl)
            ),
            strategy_vs_primary_control=(
                None
                if outcome.strategy_vs_primary_control is None
                else str(outcome.strategy_vs_primary_control)
            ),
            baseline_economic_gates_passed=outcome.baseline_economic_gates_passed,
            adverse_economic_gates_passed=outcome.adverse_economic_gates_passed,
        )

    @staticmethod
    def _qualification_dto(document: Mapping[str, object]) -> QualificationDto:
        request = _mapping(document.get("request"), field="qualification.request")
        capacity = _mapping(
            document.get("directional_capacity"),
            field="qualification.directional_capacity",
        )
        return QualificationDto(
            qualification_id=str(document["qualification_id"]),
            checkpoint_id=str(document["checkpoint_id"]),
            candidate_id=str(request["candidate_id"]),
            freeze_id=str(request["freeze_id"]),
            as_of=cast(Any, request["as_of"]),
            requested_capital=str(request["requested_capital"]),
            state=str(document["state"]),
            reason=str(document["reason"]),
            candidate_capital_ceiling=(
                None
                if request.get("candidate_capital_ceiling") is None
                else str(request["candidate_capital_ceiling"])
            ),
            current_state_qap_run_id=(
                None
                if request.get("current_state_qap_run_id") is None
                else str(request["current_state_qap_run_id"])
            ),
            requested_capital_qap_run_id=(
                None
                if request.get("requested_capital_qap_run_id") is None
                else str(request["requested_capital_qap_run_id"])
            ),
            q_star_buy=(
                None
                if capacity.get("q_star_buy") is None
                else str(capacity["q_star_buy"])
            ),
            q_safe_buy=(
                None
                if capacity.get("q_safe_buy") is None
                else str(capacity["q_safe_buy"])
            ),
            q_star_sell=(
                None
                if capacity.get("q_star_sell") is None
                else str(capacity["q_star_sell"])
            ),
            q_safe_sell=(
                None
                if capacity.get("q_safe_sell") is None
                else str(capacity["q_safe_sell"])
            ),
        )

    def forward_cohort_detail(self, cohort_id: str) -> ForwardCohortDetailDto:
        identity = _identity(cohort_id, kind="forward_cohort")
        root = self.forward_root / identity
        if not root.is_dir():
            raise _not_found("forward_cohort", identity)
        try:
            cohort = read_forward_cohort(root)
            checkpoints = tuple(
                self._checkpoint_dto(directory)
                for directory in read_completed_checkpoints(root)
            )
            qualifications = tuple(
                self._qualification_dto(document)
                for document in read_qualifications(root)
            )
        except (
            OSError,
            ProspectiveArtifactError,
            QualificationArtifactError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise _invalid("forward_cohort", identity) from exc
        return ForwardCohortDetailDto(
            summary=self._cohort_summary(root, cohort),
            freezes=tuple(self._freeze_dto(item) for item in cohort.candidate_freezes),
            checkpoints=checkpoints,
            qualifications=qualifications,
        )


__all__ = ["ScannerArtifactReader"]
