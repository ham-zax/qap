# Phase-10 Simple-First Development Result

**Date:** 2026-08-17

**Scope:** Small development/protocol comparison on the existing two-asset BTC/USDT fixture. This is a falsification and integration result, not a fresh scientific final-OOS claim.

**Empirical status:** this fixture note is retained as an integration comparison among momentum, rolling pair evidence, and the pair-blind control. The authoritative slow-momentum family evidence is now `docs/research/2026-08-17-phase10-momentum-family-results.md`, which evaluates a predeclared nine-attempt family on recorded 2023 daily Binance data and leaves the reserved 2024 final-OOS window unconsumed because no core member survives development.

## Frozen comparison

All three strategy variants used the same `research_family_id` (`family-two-asset-v1`), admitted dataset, starting inventory, external-flow stream, next-open execution timing, fee/slippage model, quantization/minimum-notional rules, HODL role, matched-contribution role, periodic/band controls, and primary incremental benchmark (`periodic-2`).

Dataset fingerprint:

- `fixture-btcusdt-1h`: `1443f2d96c061b5d143242d84821de94f67d05e9eaca64c7eb1f89c12b655cff`

Development artifact provenance reported commit `22bae0989e7c3a20c32bbf1d9b8662c56e83c461` with `git_dirty=true`. These runs therefore document current development behavior but are not treated as clean-tree reproducibility evidence.

| Variant | Run ID | Primary control-relative terminal wealth | HODL-relative terminal wealth | Fills | Fees | Slippage | Turnover |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Slow momentum | `run-4822c2323bea00abe580bed0` | `-0.00846521894339695711400553632993406066274021458317` | `-0.00842854705395581067207228495746384530785047190295` | 9 | `16.44280846670950846030489860112847918377195874552194905825` | `8.22551699185067956993741800956902410393794834693444175` | `16442.80846670950846030489860112847918377195874552194905825` |
| Rolling log-ratio z-score | `run-52ef3fc3211ac3552e63f5e7` | `-0.00846521894339695711400553632993406066274021458317` | `-0.00842854705395581067207228495746384530785047190295` | 9 | `16.44280846670950846030489860112847918377195874552194905825` | `8.22551699185067956993741800956902410393794834693444175` | `16442.80846670950846030489860112847918377195874552194905825` |
| Cross-sectional/common-mode | `run-db436ce20b5fe68070bfc7ba` | `-0.00846521894339695711400553632993406066274021458317` | `-0.00842854705395581067207228495746384530785047190295` | 9 | `16.44280846670950846030489860112847918377195874552194905825` | `8.22551699185067956993741800956902410393794834693444175` | `16442.80846670950846030489860112847918377195874552194905825` |

All three variants finish with the same terminal strategy value, `43877.03679286245537776080139063222484512761661829455060919175`, and the same maximum HODL-relative drawdown, `0.00842854705395581067207228495746384530785047190295`.

For the rolling pair model, the persisted portfolio projection shows terminal max weight `0.60055721764023409085435770597454700155996910397648` and terminal Herfindahl concentration `0.5202235080390908124391568351254307923865214371475164584437384274888601534724738289623637386967863808`. Relative to HODL, terminal asset value deltas are `-16799.3288653803435740837923118951258594605701684818765` in BTC and `+16426.36565824279895184459370252735070458818678677642710919175` in USDT.

## Interpretation

The fixture is a monotonic two-asset path. Under the frozen thresholds and max tilt, slow momentum, rolling log-ratio evidence, and the pair-blind common-mode rule all request the same bounded allocation path once they have sufficient history. Consequently they produce identical fills and economics.

This is a negative/falsifying result:

- none of the three strategies beats HODL;
- none beats the predeclared primary periodic control;
- the explicit pair model shows no incremental economic value over the pair-blind control;
- because the basket has only BTC and USDT, the internal common-mode residual is algebraically pair-degenerate and cannot independently establish or refute a stronger pair-information claim;
- no pair-specific alpha claim survives this comparison, so richer factor attribution is not warranted for this result.

The rolling model also produced a versioned persisted `evidence.parquet`; inspection through the artifact reader/API projection confirmed invalid-history observations remain present with null values and validity status, followed by causal valid scores. Model-free runs correctly have no evidence artifact.

## Selection pressure and holdout status

This comparison intentionally evaluates a small declared family, and all variants remain under the same research-family lineage. No broad parameter/pair search was used to support a superiority claim, so no SPA/Reality-Check multiplicity result is asserted or required here.

The Phase-10 final-OOS scenario test separately verifies that a losing rolling-model run is committed, executed, persisted as `negative`, and marks the holdout consumed. That scenario is a protocol regression fixture; it is not being promoted as a scientific validation result. Since the development comparison provides no surviving positive candidate, this phase does not justify consuming another scientific holdout for model promotion.

## Student-t branch

The separate admission review in `docs/research/2026-08-17-student-t-admission.md` records `REJECT` for the current Student-t/Copula branch. Historical MI was economically weak OOS and the surviving tail observations were pair-dependent; no current residual tail-specific question survives the simpler comparison strongly enough to justify Copula code or dependencies.

## Phase-10 research conclusion

Keep all implemented models research-only. The phase establishes causal model plumbing, simple-first falsification controls, shared execution/economic evaluation, immutable negative final-OOS handling, and inspectable persisted model evidence. It does **not** establish real relationship alpha on this fixture and does not grant any model automatic runtime authority.
