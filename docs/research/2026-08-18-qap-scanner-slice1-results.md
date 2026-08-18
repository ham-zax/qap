# QAP Scanner V1 Slice-1 Results

Date: 2026-08-18
Status: searched-development implementation evidence; not final-OOS evidence and not a trading recommendation.

## Scope

This record closes the Slice-1 implementation/verification evidence requested by the approved plan. Scanner discovery/scout results remain research screening evidence; authoritative economics remain owned by the ordinary QAP experiment/policy/execution/evaluation path.

The remediation pass also restored clean-checkout execution, final-OOS pre-read protection, exact completed-artifact integrity, complete SSD denominator publication, future-row-stable causal candidate identity, explicit protocol component labels, explicit manual deep replay, scanner architecture enforcement, and repository source-size compliance.

## Reproducible verification

Focused Slice-1 behavioral verification was run in two bounded batches:

```text
31 passed
35 passed
```

The covered surfaces include the canonical end-to-end scenarios, scanner artifacts, SSD graph, candidate trials, PIT universe/slices, CLI/manual replay, scanner architecture guards, experiment scanner adapter, and benchmark smoke regression.

Static/architecture evidence:

```text
focused Pyright: 0 errors, 0 warnings, 0 informations
focused Ruff: all checks passed
source-size: ok
import-linter: 8 kept, 0 broken
```

Three temporary prohibited-import probes were also run and each was rejected: scanner -> execution, financial core -> scanner, and non-adapter experiment -> scanner. After probe cleanup, import-linter returned 8/8 kept.

## 500 / 1,000 asset benchmark

Command:

```bash
uv run python scripts/benchmark_scanner_slice1.py \
  --assets 500 1000 \
  --bars 720 \
  --scout-sample 200
```

Inputs are deterministic synthetic positive price matrices generated locally with no network I/O. `peak_rss_kib` is the process high-water resident set reported by the Linux runtime. Scout time is sampled on the production scout kernel and projected over the frozen fixed trial count; authoritative replay is not performance-simulated beyond its frozen cap.

| Assets | Bars | Valid SSD pairs | Retained edges | Fixed trials | SSD seconds | Projected full scout seconds | Peak RSS KiB | All-horizon replay ceiling |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 500 | 720 | 124,750 | 2,795 | 50,310 | 39.7707 | 47.0765 | 110,712 | 30 |
| 1,000 | 720 | 499,500 | 5,667 | 102,006 | 158.7503 | 92.3223 | 194,908 | 30 |

Deterministic distance digests:

```text
500:  5ba3c88067ec644ecf6a510929c7a2031df02e0d21ab88833f6b1650796ddfcd
1000: 312f979f658db36145fd2debad2deff625d5d24660dbb15ae45badb5753a2016
```

## Performance conclusion

The required workload is measurable on the local research machine without distributed infrastructure or a new runtime dependency. The dominant measured scale cost is the quadratic Python SSD pair loop; doubling 500 -> 1,000 assets produces the expected roughly 4x SSD work. Post-graph trial enumeration remains bounded by the retained `k=8` union, and authoritative deep replay remains capped at 10 per horizon / 30 across the three horizons.

This evidence does not justify adding a database, scheduler, distributed compute layer, Polars, or DuckDB. If future local-research latency needs require optimization, the first justified target is local vectorization of the SSD kernel while preserving the frozen distance/tie/digest semantics.

## Research outcome limitations

This document verifies implementation integrity and bounded workload, not alpha. Slice-1 historical search/replay is development evidence. A zero-survivor result is valid. Prospective freeze-before-outcome evidence and empirical capacity/actionability remain Slice 2 concerns; final OOS remains sealed and unavailable to scanner search.
