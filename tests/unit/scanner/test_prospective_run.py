# pyright: reportPrivateUsage=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
"""Direct regressions for prospective orchestration identity and cohort semantics."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import cast

import pytest

import qap.scanner.prospective_run as prospective_run
from qap.market import (
    BarInterval,
    MarketBar,
    ValidatedBarSeries,
    VenueInstrument,
    fingerprint_bar_series,
    validate_bar_series,
    write_parquet_bar_series,
)
from qap.portfolio import AssetId
from qap.scanner.catalog import ScannerCatalog
from qap.scanner.models import ScanInputIdentity
from qap.scanner.prospective import (
    CandidateFreeze,
    ForwardCheckpoint,
    ForwardOutcome,
    ForwardOutcomeStatus,
    enroll_forward_cohort,
)
from qap.scanner.prospective_artifacts import start_forward_cohort
from qap.scanner.prospective_protocol import (
    PROSPECTIVE_V1,
    prospective_protocol_identity,
)
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon, protocol_identity

FREEZE_AT = datetime(2026, 8, 18, 0, 10, tzinfo=UTC)
INTERVAL = BarInterval("1h")
INSTRUMENT = VenueInstrument(
    venue="binance",
    venue_symbol="BTCETH",
    base=AssetId("BTC"),
    quote=AssetId("ETH"),
)


def _freeze(
    candidate: str,
    *,
    forward_start: datetime,
    resolution: str,
    automatic: bool,
    manual: bool,
) -> CandidateFreeze:
    return CandidateFreeze(
        candidate_id=candidate * 64,
        scan_id="a" * 64,
        scanner_protocol_version=SCANNER_V1_SLICE1.protocol_id,
        scanner_protocol_identity=protocol_identity(SCANNER_V1_SLICE1),
        prospective_protocol_version=PROSPECTIVE_V1.protocol_id,
        prospective_protocol_identity=prospective_protocol_identity(PROSPECTIVE_V1),
        automatic_selected=automatic,
        manual_selected=manual,
        frozen_at=FREEZE_AT,
        eligible_information_end=FREEZE_AT,
        forward_start=forward_start,
        forward_end=forward_start + timedelta(hours=48),
        horizon=ScannerHorizon.SHORT,
        venue="binance",
        pair_id="BTC/ETH",
        orientation="BTC/ETH",
        resolution=resolution,
        model_family="log_ratio_mean_reversion",
        template_id=f"template-{candidate}",
        model_parameters=(("window_bars", "48"),),
        source_artifact_fingerprints=(candidate * 64,),
        selection_slice_fingerprints=(
            candidate.upper().replace("A", "1").replace("B", "2") * 64,
        ),
        universe_snapshot_id="e" * 64,
        cost_policy_reference=PROSPECTIVE_V1.adverse_cost_reference,
        primary_control_reference=PROSPECTIVE_V1.primary_control_reference,
        candidate_deep_replay_run_id=f"historical-{candidate}",
        candidate_deep_replay_gate_status="deep_replay_survivor",
    )


def _dummy_catalog() -> ScannerCatalog:
    return ScannerCatalog.model_validate(
        {
            "schema_version": "qap.scanner.catalog.v1",
            "lifecycle_evidence_relative_path": "lifecycle.json",
            "sources": (
                {
                    "dataset_id": "dummy",
                    "relative_path": "dummy.parquet",
                    "venue": "binance",
                    "venue_symbol": "BTCETH",
                    "base_asset": "BTC",
                    "quote_asset": "ETH",
                    "interval": "1h",
                    "expected_semantic_fingerprint": "f" * 64,
                },
            ),
        }
    )


def _outcome(freeze: CandidateFreeze, checkpoint: ForwardCheckpoint) -> ForwardOutcome:
    passed = freeze.manual_selected and not freeze.automatic_selected
    return ForwardOutcome(
        freeze_id=freeze.freeze_id,
        candidate_id=freeze.candidate_id,
        checkpoint_id=checkpoint.checkpoint_id,
        prospective_protocol_version=freeze.prospective_protocol_version,
        prospective_protocol_identity=freeze.prospective_protocol_identity,
        status=(
            ForwardOutcomeStatus.MATURED
            if checkpoint.information_end == freeze.forward_end
            else ForwardOutcomeStatus.PARTIAL
        ),
        through=checkpoint.information_end,
        matured_at=(
            freeze.forward_end
            if checkpoint.information_end == freeze.forward_end
            else None
        ),
        qap_run_id=f"qap-{freeze.candidate_id[:8]}-{checkpoint.checkpoint_index}",
        primary_control_reference=freeze.primary_control_reference,
        cost_policy_reference=freeze.cost_policy_reference,
        strategy_vs_hodl=Decimal("1") if passed else Decimal("-1"),
        strategy_vs_primary_control=Decimal("1") if passed else Decimal("-1"),
        baseline_economic_gates_passed=passed,
        adverse_economic_gates_passed=passed,
    )


def test_mixed_resolution_maturity_is_per_freeze_and_scoreboard_excludes_manual(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    automatic = _freeze(
        "a",
        forward_start=datetime(2026, 8, 18, 0, 15, tzinfo=UTC),
        resolution="15m",
        automatic=True,
        manual=False,
    )
    manual = _freeze(
        "b",
        forward_start=datetime(2026, 8, 18, 1, 0, tzinfo=UTC),
        resolution="1h",
        automatic=False,
        manual=True,
    )
    cohort = enroll_forward_cohort(
        source_scan_id="a" * 64,
        horizon=ScannerHorizon.SHORT,
        freeze_at=FREEZE_AT,
        selected_freezes=(automatic, manual),
    )
    root = start_forward_cohort(tmp_path / "runs", cohort)
    calls: list[str] = []

    def slices(
        freeze: CandidateFreeze,
        **kwargs: object,
    ) -> tuple[tuple[ScanInputIdentity, ...], datetime, datetime]:
        through = cast(datetime, kwargs["through"])
        selection = sha256(
            f"{freeze.freeze_id}:{through.isoformat()}".encode()
        ).hexdigest()
        return (
            (
                ScanInputIdentity(
                    dataset_id=f"{freeze.candidate_id[:1]}-forward",
                    source_artifact_fingerprint="f" * 64,
                    selection_slice_fingerprint=selection,
                ),
            ),
            freeze.forward_start + timedelta(minutes=15),
            through,
        )

    def run_checkpoint(
        freeze: CandidateFreeze,
        checkpoint: ForwardCheckpoint,
        *_args: object,
    ) -> ForwardOutcome:
        calls.append(freeze.freeze_id)
        return _outcome(freeze, checkpoint)

    monkeypatch.setattr(prospective_run, "_forward_slices", slices)
    through = manual.forward_end
    first = prospective_run.advance_forward_cohort(
        cohort_root=root,
        catalog=_dummy_catalog(),
        data_root=tmp_path,
        run_root=tmp_path,
        through=through,
        load_historical_template=lambda *_args: raise_not_called(),
        run_checkpoint=run_checkpoint,
        run_timestamp=through + timedelta(hours=1),
    )
    second = prospective_run.advance_forward_cohort(
        cohort_root=root,
        catalog=_dummy_catalog(),
        data_root=tmp_path,
        run_root=tmp_path,
        through=through,
        load_historical_template=lambda *_args: raise_not_called(),
        run_checkpoint=run_checkpoint,
        run_timestamp=through + timedelta(hours=1),
    )

    assert len(first) == len(second) == 2
    assert len(calls) == 2
    scoreboard = prospective_run.cohort_scoreboard(root)
    assert scoreboard["outcome_state_counts"] == {"matured": 1}
    assert scoreboard["matured_pass_fraction"] == "0"
    assert scoreboard["manual_only_outcome_state_counts"] == {"matured": 1}
    assert scoreboard["manual_only_matured_pass_fraction"] == "1"
    assert scoreboard["all_selection_matured_pass_fraction"] == "0.5"


def raise_not_called() -> prospective_run.HistoricalReplayTemplate:
    raise AssertionError("historical template loader should not be called")


def test_same_cutoff_reuse_rejects_changed_information_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    freeze = _freeze(
        "a",
        forward_start=datetime(2026, 8, 18, 1, 0, tzinfo=UTC),
        resolution="1h",
        automatic=True,
        manual=False,
    )
    cohort = enroll_forward_cohort(
        source_scan_id="a" * 64,
        horizon=ScannerHorizon.SHORT,
        freeze_at=FREEZE_AT,
        selected_freezes=(freeze,),
    )
    root = start_forward_cohort(tmp_path / "runs", cohort)
    selection = ["1" * 64]

    def slices(
        candidate: CandidateFreeze,
        **kwargs: object,
    ) -> tuple[tuple[ScanInputIdentity, ...], datetime, datetime]:
        through = cast(datetime, kwargs["through"])
        return (
            (
                ScanInputIdentity(
                    dataset_id="candidate-forward",
                    source_artifact_fingerprint="f" * 64,
                    selection_slice_fingerprint=selection[0],
                ),
            ),
            candidate.forward_start + timedelta(hours=1),
            through,
        )

    monkeypatch.setattr(prospective_run, "_forward_slices", slices)
    through = freeze.forward_start + timedelta(hours=4)
    prospective_run.advance_forward_cohort(
        cohort_root=root,
        catalog=_dummy_catalog(),
        data_root=tmp_path,
        run_root=tmp_path,
        through=through,
        load_historical_template=lambda *_args: raise_not_called(),
        run_checkpoint=lambda candidate, checkpoint, *_args: _outcome(
            candidate, checkpoint
        ),
    )
    selection[0] = "2" * 64

    with pytest.raises(
        prospective_run.ProspectiveRunError,
        match="existing checkpoint information state mismatch",
    ):
        prospective_run.advance_forward_cohort(
            cohort_root=root,
            catalog=_dummy_catalog(),
            data_root=tmp_path,
            run_root=tmp_path,
            through=through,
            load_historical_template=lambda *_args: raise_not_called(),
            run_checkpoint=lambda candidate, checkpoint, *_args: _outcome(
                candidate, checkpoint
            ),
        )


def _series(*, changed_open_index: int | None = None) -> ValidatedBarSeries:
    bars: list[MarketBar] = []
    start = datetime(2026, 8, 17, 23, 0, tzinfo=UTC)
    for index in range(7):
        close = 100.0 + index
        if changed_open_index == index:
            close += 0.5
        bars.append(
            MarketBar(
                instrument=INSTRUMENT,
                interval=INTERVAL,
                candle_open_time=start + index * timedelta(hours=1),
                open=close,
                high=close,
                low=close,
                close=close,
                volume=1.0,
            )
        )
    return validate_bar_series(tuple(bars))


def _catalog_for_series(path: Path, series: ValidatedBarSeries) -> ScannerCatalog:
    fingerprint = fingerprint_bar_series(series)
    return ScannerCatalog.model_validate(
        {
            "schema_version": "qap.scanner.catalog.v1",
            "lifecycle_evidence_relative_path": "lifecycle.json",
            "sources": (
                {
                    "dataset_id": "btc-eth-1h",
                    "relative_path": path.name,
                    "venue": "binance",
                    "venue_symbol": "BTCETH",
                    "base_asset": "BTC",
                    "quote_asset": "ETH",
                    "interval": "1h",
                    "expected_semantic_fingerprint": fingerprint,
                },
            ),
        }
    )


@pytest.mark.parametrize("changed_index", [2, 3])
def test_forward_slice_fingerprint_includes_qap_warmup_and_starting_boundary(
    tmp_path: Path,
    changed_index: int,
) -> None:
    path = tmp_path / "btceth.parquet"
    original = _series()
    write_parquet_bar_series(path, original)
    freeze = _freeze(
        "a",
        forward_start=datetime(2026, 8, 18, 3, 0, tzinfo=UTC),
        resolution="1h",
        automatic=True,
        manual=False,
    )
    template = prospective_run.HistoricalReplayTemplate(
        evidence_sources=(("btc-eth-1h", fingerprint_bar_series(original)),),
        data_source_dataset_ids=("btc-eth-1h",),
        model_parameters=(("window_bars", "48"),),
        warmup=timedelta(hours=2),
    )
    first, _, _ = prospective_run._forward_slices(
        freeze,
        catalog=_catalog_for_series(path, original),
        data_root=tmp_path,
        run_root=tmp_path,
        through=datetime(2026, 8, 18, 5, 0, tzinfo=UTC),
        load_historical_template=lambda *_args: template,
    )

    changed = _series(changed_open_index=changed_index)
    changed_path = tmp_path / "btceth-corrected.parquet"
    write_parquet_bar_series(changed_path, changed)
    second, _, _ = prospective_run._forward_slices(
        freeze,
        catalog=_catalog_for_series(changed_path, changed),
        data_root=tmp_path,
        run_root=tmp_path,
        through=datetime(2026, 8, 18, 5, 0, tzinfo=UTC),
        load_historical_template=lambda *_args: template,
    )

    assert first[0].selection_slice_fingerprint != second[0].selection_slice_fingerprint
