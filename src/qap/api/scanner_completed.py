"""Claim-aware completed scanner presentation read models."""

from typing import Any

from qap.api.scanner_schemas import (
    CompletedResearchScopeStagesDto,
    CompletedResearchStagesDto,
    ResearchClaimDto,
)
from qap.product_current_approved_policy import (
    CURRENT_APPROVED_RESEARCH_CLAIM_LABEL,
    current_approved_claim_identity,
)
from qap.scanner.models import ScanDefinition
from qap.scanner.protocol import SCANNER_V1_SLICE1, protocol_identity


def research_claim(definition: ScanDefinition) -> ResearchClaimDto:
    """Describe the immutable universe claim sealed by one completed scan."""

    claim_identity = definition.research_claim_identity
    if (
        claim_identity is None
        and definition.research_scope_identity is None
        and definition.scanner_protocol_version == SCANNER_V1_SLICE1.protocol_id
        and definition.protocol_identity == protocol_identity(SCANNER_V1_SLICE1)
        and definition.universe_policy_version
        == SCANNER_V1_SLICE1.universe_policy_version
    ):
        return ResearchClaimDto(
            kind="historical_pit",
            label="Historical Point-in-Time Research",
            claim_identity=None,
            scope_identity=None,
        )
    if claim_identity == current_approved_claim_identity():
        return ResearchClaimDto(
            kind="current_approved_retrospective",
            label=CURRENT_APPROVED_RESEARCH_CLAIM_LABEL,
            claim_identity=claim_identity,
            scope_identity=definition.research_scope_identity,
        )
    return ResearchClaimDto(
        kind="versioned_other",
        label="Versioned Research Claim",
        claim_identity=claim_identity,
        scope_identity=definition.research_scope_identity,
    )


def completed_research_stages(
    tables: dict[str, list[dict[str, Any]]],
) -> CompletedResearchStagesDto:
    """Compose truthful completed stage counts from immutable scanner tables."""

    scouts = tables["scout_trials.parquet"]
    neighbors = tables["neighbors.parquet"]
    promotions = tables["promotions.parquet"]
    attempts = tables["replay_attempts.parquet"]
    candidate_scope = {
        str(row["candidate_id"]): (str(row["venue"]), str(row["horizon"]))
        for row in scouts
    }

    scopes: list[CompletedResearchScopeStagesDto] = []
    for graph in sorted(
        tables["graph_metadata.parquet"],
        key=lambda row: (str(row["venue"]), str(row["horizon"])),
    ):
        venue = str(graph["venue"])
        horizon = str(graph["horizon"])
        key = (venue, horizon)
        scope_scouts = [
            row for row in scouts if (str(row["venue"]), str(row["horizon"])) == key
        ]
        scope_candidates = {str(row["candidate_id"]) for row in scope_scouts}
        scope_promotions = [
            row for row in promotions if str(row["candidate_id"]) in scope_candidates
        ]
        scope_attempts = [
            row
            for row in attempts
            if candidate_scope.get(str(row["candidate_id"])) == key
        ]
        scopes.append(
            CompletedResearchScopeStagesDto(
                venue=venue,
                horizon=horizon,
                scope_asset_count=int(graph["eligible_asset_count"]),
                relationship_comparison_count=int(
                    graph["total_valid_pair_comparisons"]
                ),
                retained_relationship_count=sum(
                    (str(row["venue"]), str(row["horizon"])) == key for row in neighbors
                ),
                enumerated_rule_count=len(scope_scouts),
                valid_rule_count=sum(
                    str(row["trial_status"]) == "valid" for row in scope_scouts
                ),
                invalid_rule_count=sum(
                    str(row["trial_status"]) == "invalid" for row in scope_scouts
                ),
                selected_for_replay_count=sum(
                    bool(row["selected_for_replay"]) for row in scope_promotions
                ),
                completed_replay_count=sum(
                    str(row["attempt_status"]) == "completed" for row in scope_attempts
                ),
                replay_unavailable_count=sum(
                    str(row["attempt_status"]) in {"setup_failed", "replay_failed"}
                    for row in scope_attempts
                ),
                rejected_replay_count=sum(
                    row["economic_gate_status"] == "deep_replay_rejected"
                    for row in scope_promotions
                ),
                research_idea_count=sum(
                    row["economic_gate_status"] == "deep_replay_survivor"
                    for row in scope_promotions
                ),
            )
        )
    return CompletedResearchStagesDto(scopes=tuple(scopes))


__all__ = ["completed_research_stages", "research_claim"]
