# Phase-11 Larger-Window Paper Exercise

**Date:** 2026-08-17

**Purpose:** Exercise the existing multi-asset paper-operation, immutable artifact, reconciliation, and filesystem-reader paths over a representative recorded window. This is an operational/performance check, not research alpha, final-OOS evidence, or prospective candidate evidence.

**Measured commit:** `67d24bd56c62ca384a54ce802a802914d78a8fc9`

**Measured code fingerprint:** `f57d7465d33f9e6490edd59a9cebcfe6aff0856f83f0410195402e52f654e444`

The machine-readable exercise emitted both values itself with `git_dirty=false`; they are not hand-entered provenance fields.

**Machine-readable result:** `docs/research/2026-08-17-phase11-larger-window-exercise.json`

## Inputs and boundaries

The exercise used three recorded public Binance daily series from 2023, so it did **not** inspect the reserved BTCUSDT 2024 final-OOS dataset:

- BTCUSDT: 365 bars, fingerprint `0cff5a7068c2d3e7957b481f826ce8ca80956191873671035a08353cfdb4d5fc`
- ETHUSDT: 365 bars, fingerprint `bfe77b4d12ba680c2a90d9c4b39bb2efab16427f4f25579775d56202df88b237`
- SOLUSDT: 365 bars, fingerprint `0b6ed55cc33f1149d98ea0f4b2b29ddecdf455257157be751c42647884a63be1`

The paper path carried each operation's real ending holdings into the next day and alternated between two fixed target allocations every 30 days. It used the recorded Phase-11 Binance exchange-info snapshot for normalized precision/minimum constraints. Each modeled MARKET order also received an explicit notional-filter reference equal to that day's recorded close; this exercises the separate filter-price contract but is **not** a reconstruction of Binance's historical `avgPriceMins` reference series. Applying the later metadata snapshot and these deterministic reference values to 2023 prices is intentional for an **operational stress exercise**; this result is not a historical execution-fidelity claim.

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

- execution time: `1.2216496839973843` seconds;
- total immutable JSON artifact bytes: `2079544`;
- average artifact size: `5697.380821917808` bytes;
- largest artifact: `6740` bytes;
- full 365-operation read-only list scan: `0.05178837499988731` seconds.

Observed temporary experiment-reader metrics:

- 25 run artifacts generated in `1.8779373750003288` seconds;
- full 25-run `list_experiments()` scan: `0.11767132599197794` seconds.

Process maximum resident set size reported by the Linux process was `213240` KiB.

These timings and memory values are **observations, not performance SLAs**. They are included to establish that the current bounded workload did not expose a material bottleneck requiring profiling or a new compute/indexing framework.

## Conclusion

Section 11.8's bounded larger-window check does not reveal a need for speculative optimization:

- multi-asset carried-state execution remained reconciled across the full window;
- explicit no-fill behavior remained visible rather than being silently rounded away;
- immutable operation artifacts stayed compact and did not embed the historical market window;
- the filesystem paper-operation and experiment list readers completed the measured bounded scans without a material delay on this machine;
- no database, catalog/index service, alternate compute engine, or profiling-driven rewrite is justified by this result.

If a future materially larger real workload makes either reader slow, measure that workload first and write a separate indexing/performance plan rather than introducing infrastructure preemptively.
