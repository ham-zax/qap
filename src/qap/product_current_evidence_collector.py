"""Long-lived Local Market collector for scheduled public Spot evidence."""

from __future__ import annotations

import signal
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from qap.market.adapters.binance_public import (
    BinancePublicAdapter,
    BinancePublicDataError,
)
from qap.market.adapters.gate_public import GatePublicAdapter, GatePublicDataError
from qap.market.microstructure import public_market_metadata_snapshot_from_metadata
from qap.product_current_evidence import (
    ProductCurrentEvidenceError,
    ProductCurrentEvidenceStore,
    ResolvedCollectorInstrument,
)
from qap.product_current_evidence_identity import frozen_market_codes
from qap.product_universe import ProductUniverse, ProductUniverseError

_POLL_SECONDS = 5.0
_stop_requested = False


def _stop(_signum: int, _frame: object) -> None:
    global _stop_requested
    _stop_requested = True


def _capture_binance(
    store: ProductCurrentEvidenceStore,
    target: ResolvedCollectorInstrument,
) -> None:
    with BinancePublicAdapter() as adapter:
        for kind in ("l1", "depth"):
            claim = store.reconcile_and_claim(
                instrument_id=target.collector_instrument_id,
                kind=kind,
            )
            if claim is None:
                continue
            try:
                snapshot = (
                    adapter.fetch_l1_book(instrument=target.instrument)
                    if kind == "l1"
                    else adapter.fetch_shallow_depth(
                        instrument=target.instrument,
                        limit=20,
                    )
                )
            except BinancePublicDataError:
                continue
            store.admit_book(claim, snapshot)
        if store.metadata_needed(target.collector_instrument_id):
            base_code, quote_code = frozen_market_codes(
                ProductUniverse(store.workspace_root),
                target.instrument,
            )
            try:
                metadata = adapter.fetch_market_metadata(
                    venue_symbol=target.instrument.venue_symbol,
                    base=target.instrument.base,
                    quote=target.instrument.quote,
                    venue_base_asset=base_code,
                    venue_quote_asset=quote_code,
                    require_trading=False,
                )
            except BinancePublicDataError:
                return
            store.admit_metadata(
                instrument_id=target.collector_instrument_id,
                snapshot=public_market_metadata_snapshot_from_metadata(
                    metadata=metadata,
                    observed_at=datetime.now(UTC),
                    source_id="binance:normalized-public-metadata",
                ),
            )


def _capture_gate(
    store: ProductCurrentEvidenceStore,
    target: ResolvedCollectorInstrument,
) -> None:
    with GatePublicAdapter() as adapter:
        for kind in ("l1", "depth"):
            claim = store.reconcile_and_claim(
                instrument_id=target.collector_instrument_id,
                kind=kind,
            )
            if claim is None:
                continue
            try:
                snapshot = (
                    adapter.fetch_l1_book(instrument=target.instrument)
                    if kind == "l1"
                    else adapter.fetch_shallow_depth(
                        instrument=target.instrument,
                        limit=20,
                    )
                )
            except GatePublicDataError:
                continue
            store.admit_book(claim, snapshot)
        if store.metadata_needed(target.collector_instrument_id):
            base_code, quote_code = frozen_market_codes(
                ProductUniverse(store.workspace_root),
                target.instrument,
            )
            try:
                metadata = adapter.fetch_market_metadata(
                    venue_symbol=target.instrument.venue_symbol,
                    base=target.instrument.base,
                    quote=target.instrument.quote,
                    venue_base_asset=base_code,
                    venue_quote_asset=quote_code,
                )
            except GatePublicDataError:
                return
            store.admit_metadata(
                instrument_id=target.collector_instrument_id,
                snapshot=public_market_metadata_snapshot_from_metadata(
                    metadata=metadata,
                    observed_at=datetime.now(UTC),
                    source_id="gate:normalized-public-metadata",
                ),
            )


def _capture_target(
    store: ProductCurrentEvidenceStore,
    target: ResolvedCollectorInstrument,
) -> None:
    if target.instrument.venue == "binance":
        _capture_binance(store, target)
        return
    if target.instrument.venue == "gate":
        _capture_gate(store, target)
        return
    raise ProductCurrentEvidenceError("Collector target venue is not supported.")


def _reconcile_known_slots(store: ProductCurrentEvidenceStore) -> None:
    active = {
        target.collector_instrument_id: target for target in store.active_targets()
    }
    for instrument_id in store.all_instrument_ids():
        target = active.get(instrument_id)
        if target is not None:
            _capture_target(store, target)
            continue
        for kind in ("l1", "depth"):
            store.reconcile_and_claim(
                instrument_id=instrument_id,
                kind=kind,
            )


def run(workspace_root: Path) -> int:
    """Run one sequential collector until termination or a fatal state error."""

    store = ProductCurrentEvidenceStore(workspace_root)
    store.acquire_lease()
    try:
        while not _stop_requested:
            _reconcile_known_slots(store)
            store.heartbeat()
            time.sleep(_POLL_SECONDS)
    except (
        ProductCurrentEvidenceError,
        ProductUniverseError,
        OSError,
        ValueError,
    ) as exc:
        store.fail_lease(f"{type(exc).__name__}: {exc}")
        return 1
    finally:
        if store.lease_state().status == "running":
            store.release_lease()
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "usage: python -m qap.product_current_evidence_collector WORKSPACE_ROOT",
            file=sys.stderr,
        )
        return 2
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    return run(Path(sys.argv[1]))


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["run"]
