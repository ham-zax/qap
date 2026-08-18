"""Reusable cross-sectional relative-return replay policy composition."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from qap.experiment.data import LoadedExperimentData
from qap.market import PriceSnapshot
from qap.policy import PolicyDecision
from qap.policy.evidence_tilt import CrossSectionalTiltPolicy
from qap.portfolio import (
    AllocationTarget,
    AssetId,
    ExternalInventoryFlow,
    PortfolioState,
)
from qap.relationship.models import (
    CrossSectionalRelativeStatus,
    cross_sectional_relative_observation,
)


def _evidence_id(model_id: str, model_version: str, input_fingerprint: str) -> str:
    return f"{model_id}:v{model_version}:{input_fingerprint}"


@dataclass(slots=True)
class CrossSectionalReplayPolicy:
    """Convert pair-blind cross-sectional returns into one long-only tilt target."""

    policy_id: str
    loaded: LoadedExperimentData
    basket: tuple[AssetId, ...]
    window_returns: int
    tilt: CrossSectionalTiltPolicy

    def decide(
        self,
        *,
        as_of: datetime,
        current_state: PortfolioState,
        price_snapshot: PriceSnapshot,
        applied_flows: tuple[ExternalInventoryFlow, ...],
        evidence_ids: Iterable[str] = (),
    ) -> PolicyDecision:
        del price_snapshot, applied_flows, evidence_ids
        observation = cross_sectional_relative_observation(
            self.loaded.aligned,
            basket=self.basket,
            window_returns=self.window_returns,
            as_of=as_of,
        )
        scores = (
            observation.scores
            if observation.status is CrossSectionalRelativeStatus.VALID
            else None
        )
        return self.tilt.decide(
            as_of=as_of,
            current_state=current_state,
            scores=scores,
            evidence_id=_evidence_id(
                observation.model_id,
                observation.model_version,
                observation.input_fingerprint,
            ),
        )


def cross_sectional_replay_policy(
    *,
    policy_id: str,
    loaded: LoadedExperimentData,
    basket: tuple[AssetId, ...],
    window_returns: int,
    neutral_target: AllocationTarget,
    maximum_tilt: Decimal,
) -> CrossSectionalReplayPolicy:
    """Build the shared pair-blind cross-sectional replay policy."""

    return CrossSectionalReplayPolicy(
        policy_id=policy_id,
        loaded=loaded,
        basket=basket,
        window_returns=window_returns,
        tilt=CrossSectionalTiltPolicy(
            policy_id=policy_id,
            neutral_target=neutral_target,
            maximum_tilt=maximum_tilt,
        ),
    )


__all__ = ["CrossSectionalReplayPolicy", "cross_sectional_replay_policy"]
