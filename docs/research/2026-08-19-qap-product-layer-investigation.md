# QAP Product Layer Investigation

**Date:** 2026-08-19

**Purpose:** Preserve the repository and public-source evidence that triggered the Phase-17 Product Layer design freeze.

**Canonical design produced from this investigation:** `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`

**Implementation plan:** `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`

## 1. Investigation question

After Phase 16, the rendered workbench was easier to understand, but a clean local workspace still could not honestly perform the complete user journey without expert/manual setup.

The investigation therefore asked:

> What operational/product ownership is still missing between a clean QAP install and the already-authoritative scanner/prospective/basket research engine?

The answer was not another frontend-only redesign. The missing layer is market/universe/data/longitudinal product state.

## 2. Repository evidence

### 2.1 Explicit asset admission is already a protected product boundary

QAP's governing system design states that the executable action space is Spot-only, long-only, no leverage/borrowing/derivatives/interest and that asset-level suitability remains an explicit operator decision.

Relevant sources:

- `docs/superpowers/specs/2026-08-17-qap-system-design.md`
- `docs/superpowers/plans/2026-08-17-qap-master-implementation-plan.md`
- `docs/plans/12-live-readiness-gate.md`

Therefore a real Product Layer may not equate "currently listed on an exchange" with "approved for QAP ownership/research".

### 2.2 Scanner-V1 historical universe semantics are stricter than current-market discovery

The scanner design permits official automatic historical point-in-time graphs only when historical eligibility is known. Unknown historical eligibility fails closed for official PIT claims.

Relevant source:

- `docs/superpowers/specs/2026-08-18-qap-scanner-slice1-design.md`

This rules out using today's exchange market list or CCXT market list as a historical-universe oracle.

### 2.3 Current scan definition is protocol-owned

`ScanDefinition` seals protocol identity, catalog identity, universe policy, venues, horizons, input slices, and manual inputs. `_prepare_inputs(...)` currently binds `venues=protocol.venues`.

Relevant code:

- `src/qap/scanner/models.py`
- `src/qap/scanner/preparation.py`
- `src/qap/scanner/protocol.py`

Therefore a user-facing venue selector cannot silently mutate existing Scanner-V1 semantics. A default Product current-approved scope needs an explicit separately-versioned claim/policy.

### 2.4 Current scanner input catalog is prepared outside the normal product journey

The completed application can launch scanner research only after a compatible scanner catalog/data root already exists. The deterministic fixture supplies that state; the normal product does not yet own production acquisition/catalog preparation.

Relevant code/docs:

- `src/qap/scanner/catalog.py`
- `src/qap/scanner/preparation.py`
- Slice-4 deterministic browser fixture/scenario setup

### 2.5 Prospective/current evidence requires real elapsed collection

The frozen prospective protocol requires:

```text
L1 cadence                 60 seconds
shallow depth cadence       5 minutes
minimum window             14 days
overall coverage           >=95%
per-UTC-day coverage       >=90%
```

Relevant sources:

- `src/qap/scanner/prospective_protocol.py`
- `src/qap/scanner/liquidity_policy.py`
- `docs/superpowers/specs/2026-08-18-qap-scanner-slice2-prospective-evidence-liquidity-design.md`

Therefore one manual "Update current market evidence" click cannot make a fresh real workspace ready for capacity assessment.

### 2.6 Current public-capture storage is bounded/manual, not a long-lived collector store

`append_public_book_snapshot(...)` reads the existing Parquet stream, appends one observation in memory, and rewrites the file.

Relevant code:

- `src/qap/market/microstructure_storage.py`
- `src/qap/market/public_capture.py`

That is valid for bounded one-shot capture but is not the right persistence pattern for tens of thousands of scheduled observations per instrument over a 14-day qualification window.

### 2.7 Prospective scenario proves immutable later source generations, but exposes a product refresh seam

The Slice-2 scenario freezes a historical survivor, then creates newer immutable physical market-data files under the same logical dataset IDs and updates the catalog before forward advancement.

Relevant source:

- `tests/scenarios/test_scanner_slice2.py` (`_append_forward_data`)
- `docs/research/2026-08-18-qap-scanner-slice2-results.md`

The product implication is that ongoing market refresh must use immutable generations. It also exposes a real ownership seam: freezing an older completed scan must resolve the historical sources sealed by its authoritative run/scan lineage rather than requiring the current catalog generation to retain the older whole-source fingerprint.

### 2.8 Direct pair markets remain required for authoritative Slice-1 replay

Relationship discovery may compare two USDT-denominated asset paths, but authoritative historical pair replay requires a real same-venue direct Spot instrument between the candidate assets plus admitted historical bars.

Relevant source:

- `docs/superpowers/specs/2026-08-18-qap-scanner-slice1-design.md`

The Product Layer therefore needs to prepare relevant direct pair-market data where it exists and preserve `unsupported_direct_market` when it does not. It must not synthesize a USDT bridge for Slice-1 pair replay.

### 2.9 Canonical asset identity is richer than ticker text

QAP already models canonical economic asset identity, asset-identity versions, lifecycle events, renames/migrations, and explicit continuity.

Relevant code:

- `src/qap/market/lifecycle.py`
- `src/qap/portfolio/assets.py`

Therefore cross-venue/current directory ingestion must fail closed on ambiguous identity rather than merge assets by ticker equality.

## 3. Public-source investigation

### 3.1 CCXT

CCXT is a strong public-exchange transport/normalization library, but its own documentation makes clear that historical OHLCV availability, defaults, pagination, and exchange support differ by venue.

Investigated sources:

- `https://github.com/ccxt/ccxt`
- `https://github.com/ccxt/ccxt/wiki/Manual`

Conclusion:

CCXT can later reduce duplicated exchange transport code, but it does not solve QAP's canonical asset identity, source provenance, historical-universe admission, lifecycle evidence, or scientific claim ownership. Product V1 therefore keeps the already-existing explicit Binance/Gate adapters and defers CCXT until a concrete third-venue or duplicated-adapter need earns it.

### 3.2 Binance public data

Binance provides official public Spot historical data archives/checksums and public REST market-data endpoints.

Investigated sources:

- `https://github.com/binance/binance-public-data`
- Binance Spot REST public market-data documentation

Important boundary:

The official archive/current metadata surfaces do not by themselves provide a complete historical point-in-time symbol eligibility manifest suitable for QAP's strict historical PIT claim. Current market state therefore cannot be retroactively promoted into historical eligibility truth.

### 3.3 Gate public data

Gate public Spot metadata exposes useful current/lifecycle-oriented fields and its official historical quotation service publishes Spot candlestick and order-book archive files.

Investigated sources:

- Gate API v4 Spot documentation
- `https://testnet.gate.com/developer/historical_quotes`

Observed during the investigation:

- public Spot market breadth is large enough that "download and scan everything" is not a trivial onboarding operation;
- Gate historical depth archives contain frequent top-book snapshots;
- Gate bulk candlestick interval availability does not exactly match every QAP-required interval, so any lower-interval aggregation requires explicit derivation provenance.

The existence of historical depth archives does **not** authorize retroactive certification under QAP's existing current/prospective capture contract.

## 4. Current-market breadth snapshot

A live public directory check during the investigation showed current supported-market breadth substantially larger than the deterministic QA fixture.

The exact counts are intentionally not frozen as a product contract because they change over time. The important product conclusion is that a normal QAP user should not unknowingly trigger an all-exchange universe download/scan.

The default Product scope is therefore the **operator-approved research universe**.

## 5. Scanner scale measurement

The repository already includes a deterministic Scanner-V1 performance benchmark. During this investigation it was run at 2,079 synthetic assets and 720 bars to approximate a current large-venue scale.

Command shape:

```bash
uv run python scripts/benchmark_scanner_slice1.py \
  --assets 2079 \
  --bars 720 \
  --scout-sample 200
```

Observed result:

```text
assets                              2,079
valid SSD pairs                 2,160,081
retained edges                     11,869
fixed trials                      213,642
SSD time                          697.263 s
projected full scout time         199.743 s
peak RSS                          550,364 KiB
automatic replay ceiling               30
```

This is deterministic synthetic sizing evidence, not an exchange SLA or a production latency promise.

It reinforces two design choices:

1. Product default research should scan the explicit approved universe, not every current ticker.
2. If later latency requirements demand optimization, the measured quadratic SSD/search kernel is the first justified target; do not weaken scientific selection semantics merely to make a broad scan look faster.

## 6. Product-layer conclusions

The investigation froze the following conclusions:

1. The missing layer is operational/product state, not another React-only rewording pass.
2. Asset admission must be explicit and separate from exchange listing state.
3. Default product research needs an honest current-approved/current-survivor retrospective claim separate from strict historical PIT discovery.
4. Historical market data must be prepared/refreshed as immutable physical generations under stable logical dataset identities.
5. Automated acquisition needs exact upstream/derivation provenance.
6. Old research must keep resolving its original immutable sources after current catalog refreshes.
7. Real direct pair-market data must be prepared where authoritative pair replay needs it.
8. Readiness and safe research cutoff are backend-owned facts.
9. Forward validation belongs to the longitudinal Research Idea mental model, while its exact evidence classes remain distinct underneath.
10. Prospective follow-up must preserve the existing all-survivor anti-cherry-picking behavior.
11. Current-capacity evidence requires persistent real-time public collection; one manual capture cannot satisfy it.
12. Historical depth archives must not silently backfill that current/prospective contract.
13. A focused stdlib SQLite operational store is now justified for product-maintenance/collector state while QAP research artifacts remain immutable Parquet/JSON.
14. The frozen future primary IA is `Home | Research | Portfolios | History`.
15. Sample versus Local Market workspace identity must be explicit.
16. Packaging is deferred until the Product core proves what process-lifecycle burden remains.

## 7. No scientific-authority change

This investigation does not authorize changes to:

- economic objective;
- owned-inventory authority;
- Spot-only/Shariah action-space mechanics;
- HODL/control semantics;
- costs/fills/timing;
- final-OOS discipline;
- strict historical PIT claims;
- prospective outcome/capacity policy;
- basket financial authority;
- live/private exchange or capital authority.

Those remain governed by the existing QAP design and the stop conditions in the Phase-17 design freeze.
