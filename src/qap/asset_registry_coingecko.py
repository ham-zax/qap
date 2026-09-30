"""Explicit bounded CoinGecko acquisition and provenance-preserving disk cache."""

import json
import os
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

import httpx

from qap.asset_registry import (
    RefreshFailure,
    RegistryCoin,
    RegistryRefreshResult,
    RegistrySnapshot,
    RegistrySource,
    RegistryTicker,
)
from qap.market.microstructure import public_payload_fingerprint
from qap.product_directory_models import Venue

BASE_URL = "https://api.coingecko.com/api/v3/"
DEMO_KEY_ENV = "COINGECKO_DEMO_API_KEY"
_PAGE_SIZE = 100
_EXCHANGES: tuple[tuple[Venue, str], ...] = (("binance", "binance"), ("gate", "gate"))
_RETRYABLE = frozenset({429, 500, 502, 503, 504})


class RegistryCacheError(ValueError):
    """The stored snapshot is unreadable; it is never accepted as evidence."""


class _Refusal(Exception):
    def __init__(self, failure: RefreshFailure) -> None:
        super().__init__(failure)
        self.failure: RefreshFailure = failure


def _mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise _Refusal("malformed_response")
    return cast(dict[str, object], value)


def _list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise _Refusal("malformed_response")
    return cast(list[object], value)


def _retry_after(response: httpx.Response) -> float:
    try:
        return max(0.0, float(response.headers.get("retry-after", "0")))
    except ValueError:
        return 0.0


class _PacedGet:
    """Sequential GETs sharing one pacing clock, request budget and provenance log."""

    def __init__(
        self,
        client: httpx.Client,
        *,
        pacing: float,
        timeout: float,
        budget: float,
        retries: int,
        backoff: float,
        clock: Callable[[], float],
        sleep: Callable[[float], None],
        now: Callable[[], datetime],
        last_request: float | None,
    ) -> None:
        self.client, self.pacing, self.timeout = client, pacing, timeout
        self.backoff = backoff
        self.retries, self.clock, self.sleep, self.now = retries, clock, sleep, now
        self.deadline = clock() + budget
        self.last_request = last_request
        self.sources: list[RegistrySource] = []

    def _wait(self, minimum: float) -> float:
        wait = minimum
        if self.last_request is not None:
            wait = max(wait, self.pacing - (self.clock() - self.last_request))
        remaining = self.deadline - self.clock() - max(wait, 0.0)
        if remaining <= 0:
            raise _Refusal("budget_exhausted")
        if wait > 0:
            self.sleep(wait)
        return remaining

    def get(self, path: str, params: dict[str, str] | None = None) -> object:
        params = params or {}
        minimum = 0.0
        for attempt in range(self.retries + 1):
            remaining = self._wait(minimum)
            self.last_request = self.clock()
            try:
                response = self.client.get(
                    path, params=params, timeout=min(self.timeout, remaining)
                )
            except httpx.TimeoutException as exc:
                raise _Refusal("timeout") from exc
            except httpx.TransportError as exc:
                raise _Refusal("network_error") from exc
            if response.status_code in _RETRYABLE and attempt < self.retries:
                minimum = max(_retry_after(response), self.backoff * 2**attempt)
                continue
            if response.status_code == 429:
                raise _Refusal("rate_limited")
            if response.is_error:
                raise _Refusal("http_error")
            try:
                payload = response.json()
            except ValueError as exc:
                raise _Refusal("malformed_response") from exc
            self.sources.append(
                RegistrySource(
                    url=BASE_URL + path,
                    request_fingerprint=public_payload_fingerprint(
                        {"method": "GET", "url": BASE_URL + path, "params": params}
                    ),
                    payload_fingerprint=public_payload_fingerprint(payload),
                    retrieved_at=self.now(),
                )
            )
            return payload
        raise _Refusal("rate_limited")


class CoinGeckoRegistry:
    """CoinGecko coin list, platforms and per-exchange tickers as snapshot evidence.

    Nothing is fetched at construction or import. `refresh` is the only network
    entry point; HTTP goes through the injectable `transport`.
    """

    def __init__(
        self,
        cache_path: Path,
        *,
        demo_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
        pacing_seconds: float = 2.1,
        timeout_seconds: float = 10.0,
        budget_seconds: float = 300.0,
        max_pages: int = 40,
        retries: int = 1,
        backoff_seconds: float = 5.0,
        min_age: timedelta = timedelta(hours=6),
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if (
            min(pacing_seconds, backoff_seconds) < 0
            or timeout_seconds <= 0
            or budget_seconds <= 0
        ):
            raise ValueError(
                "registry pacing/backoff must be nonnegative, budgets positive"
            )
        if not 1 <= max_pages <= 100 or not 0 <= retries <= 6:
            raise ValueError("registry pages/retries exceed bounded limits")
        self.cache_path = cache_path
        self.demo_key = (
            demo_key if demo_key is not None else os.environ.get(DEMO_KEY_ENV)
        )
        self.transport = transport
        self.pacing_seconds = pacing_seconds
        self.timeout_seconds = timeout_seconds
        self.budget_seconds = budget_seconds
        self.max_pages = max_pages
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        self.min_age = min_age
        self.clock, self.sleep, self.now = clock, sleep, now
        self._last_request: float | None = None

    def snapshot(self) -> RegistrySnapshot | None:
        if not self.cache_path.exists():
            return None
        try:
            envelope = json.loads(self.cache_path.read_text(encoding="utf-8"))
            snapshot = RegistrySnapshot.model_validate(envelope["snapshot"])
            if envelope["fingerprint"] != snapshot.fingerprint:
                raise RegistryCacheError("registry cache fingerprint mismatch")
        except RegistryCacheError:
            raise
        except (ValueError, KeyError, TypeError) as exc:
            raise RegistryCacheError("registry cache is unreadable") from exc
        return snapshot

    def refresh(self, *, force: bool = False) -> RegistryRefreshResult:
        try:
            previous = self.snapshot()
        except RegistryCacheError:
            previous = None
        if (
            previous is not None
            and not force
            and self.now() - previous.observed_at < self.min_age
        ):
            return RegistryRefreshResult(status="cached", snapshot=previous)
        try:
            snapshot = self._acquire()
        except _Refusal as refusal:
            # Only the typed cause escapes: response URLs and headers may hold keys.
            return RegistryRefreshResult(
                status="unavailable" if previous is None else "stale",
                snapshot=previous,
                failure=refusal.failure,
            )
        self._store(snapshot)
        return RegistryRefreshResult(status="refreshed", snapshot=snapshot)

    def _acquire(self) -> RegistrySnapshot:
        observed_at = self.now()
        headers = {"x-cg-demo-api-key": self.demo_key} if self.demo_key else {}
        with httpx.Client(
            base_url=BASE_URL, headers=headers, transport=self.transport
        ) as client:
            get = _PacedGet(
                client,
                pacing=self.pacing_seconds,
                timeout=self.timeout_seconds,
                budget=self.budget_seconds,
                retries=self.retries,
                backoff=self.backoff_seconds,
                clock=self.clock,
                sleep=self.sleep,
                now=self.now,
                last_request=self._last_request,
            )
            try:
                coins = self._coins(get)
                tickers = self._tickers(get, {coin.coin_id for coin in coins})
            finally:
                self._last_request = get.last_request
        try:
            return RegistrySnapshot(
                observed_at=observed_at,
                coins=coins,
                tickers=tickers,
                sources=tuple(get.sources),
            )
        except ValueError as exc:
            raise _Refusal("malformed_response") from exc

    def _coins(self, get: _PacedGet) -> tuple[RegistryCoin, ...]:
        rows = _list(get.get("coins/list", {"include_platform": "true"}))
        if not rows:
            raise _Refusal("malformed_response")
        try:
            return tuple(
                RegistryCoin.model_validate(
                    {
                        "coin_id": row["id"],
                        "symbol": row["symbol"],
                        "name": row["name"],
                        "platforms": sorted(
                            (chain, address)
                            for chain, address in _mapping(
                                row.get("platforms") or {}
                            ).items()
                            if chain and address
                        ),
                    }
                )
                for row in map(_mapping, rows)
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise _Refusal("malformed_response") from exc

    def _tickers(self, get: _PacedGet, known: set[str]) -> tuple[RegistryTicker, ...]:
        tickers: list[RegistryTicker] = []
        for venue, exchange in _EXCHANGES:
            for page in range(1, self.max_pages + 1):
                payload = _mapping(
                    get.get(
                        f"exchanges/{exchange}/tickers",
                        {"page": str(page), "order": "base_target"},
                    )
                )
                rows = _list(payload.get("tickers"))
                try:
                    tickers.extend(
                        RegistryTicker.model_validate(
                            {
                                "venue": venue,
                                "base": row["base"],
                                "target": row["target"],
                                "coin_id": row["coin_id"],
                                "stale": bool(row.get("is_stale")),
                                "anomalous": bool(row.get("is_anomaly")),
                            }
                        )
                        for row in map(_mapping, rows)
                        if row.get("coin_id") in known
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    raise _Refusal("malformed_response") from exc
                if len(rows) < _PAGE_SIZE:
                    break
            else:
                raise _Refusal("malformed_response")
        return tuple(tickers)

    def _store(self, snapshot: RegistrySnapshot) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.cache_path.with_suffix(self.cache_path.suffix + ".tmp")
        envelope = {
            "fingerprint": snapshot.fingerprint,
            "snapshot": snapshot.model_dump(mode="json"),
        }
        temporary.write_text(json.dumps(envelope, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.cache_path)
