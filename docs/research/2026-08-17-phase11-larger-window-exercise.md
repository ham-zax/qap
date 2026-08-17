# Phase-11 Larger-Window Paper Exercise

**Date:** 2026-08-17

**Purpose:** Exercise the existing multi-asset paper-operation, immutable artifact, reconciliation, and filesystem-reader paths over a representative recorded window. This is an operational/performance check, not research alpha, final-OOS evidence, or prospective candidate evidence.

**Measured commit:** `d05c4360a522c8a5b2dc335857a05cdf4f2b466d`

**Machine-readable result:** `docs/research/2026-08-17-phase11-larger-window-exercise.json`

## Inputs and boundaries

The exercise used three recorded public Binance daily series from 2023, so it did **not** inspect the reserved BTCUSDT 2024 final-OOS dataset:

- BTCUSDT: 365 bars, fingerprint `0cff5a7068c2d3e7957b481f826ce8ca80956191873671035a08353cfdb4d5fc`
- ETHUSDT: 365 bars, fingerprint `bfe77b4d12ba680c2a90d9c4b39bb2efab16427f4f25579775d56202df88b237`
- SOLUSDT: 365 bars, fingerprint `0b6ed55cc33f1149d98ea0f4b2b29ddecdf455257157be751c42647884a63be1`

The paper path carried each operation's real ending holdings into the next day and alternated between two fixed target allocations every 30 days. It used the recorded Phase-11 Binance exchange-info snapshot for normalized precision/minimum constraints. Applying that later metadata snapshot to 2023 prices is intentional for an **operational stress exercise**; this result is not a historical execution-fidelity claim.

A separate temporary experiment root contained 25 deliberately distinct copies of the small deterministic fixture manifest under an artificial scan-only family. Those runs exist only to exercise the real `RunArtifactReader.list_experiments()` filesystem path and are not research-family evidence.

All generated operation/run directories lived under a temporary directory and were deleted by the exercise. Market bars remained in the separate Parquet fixtures rather than being copied into every operation artifact.

## Observed result

The clean run processed:

- 365 carried-state multi-asset paper operations;
- 1,095 admitted market rows across three series;
- 391 realized fills;
- 704 explicit no-fill order outcomes from the modeled precision/minimum constraints;
- 365/365 operation artifacts accepted by the independent reconciliation boundary.

Observed paper-operation metrics on this machine:

- execution time: `1.0189322330115829` seconds;
- total immutable JSON artifact bytes: `2044653`;
- average artifact size: `5601.789041095891` bytes;
- largest artifact: `6644` bytes;
- full 365-operation read-only list scan: `0.05282372600049712` seconds.

Observed temporary experiment-reader metrics:

- 25 run artifacts generated in `1.8677885409997543` seconds;
- full 25-run `list_experiments()` scan: `0.11853980498563033` seconds.

Process maximum resident set size reported by the Linux process was `198088` KiB.

These timings and memory values are **observations, not performance SLAs**. They are included to establish that the current bounded workload did not expose a material bottleneck requiring profiling or a new compute/indexing framework.

## Conclusion

Section 11.8's bounded larger-window check does not reveal a need for speculative optimization:

- multi-asset carried-state execution remained reconciled across the full window;
- explicit no-fill behavior remained visible rather than being silently rounded away;
- immutable operation artifacts stayed compact and did not embed the historical market window;
- the filesystem paper-operation and experiment list readers completed the measured bounded scans without a material delay on this machine;
- no database, catalog/index service, alternate compute engine, or profiling-driven rewrite is justified by this result.

If a future materially larger real workload makes either reader slow, measure that workload first and write a separate indexing/performance plan rather than introducing infrastructure preemptively.
