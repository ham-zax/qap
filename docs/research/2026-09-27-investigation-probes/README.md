# Investigation probes (2026-09-27)

Throwaway measurement scripts behind the
[investigation findings](../2026-09-27-research-product-investigation-findings.md).
They are not part of QAP runtime. Run them from a scratch directory with these
live snapshots saved beside them:

- `binance_ei.json`: `https://api.binance.com/api/v3/exchangeInfo`
- `gate_pairs.json`: `https://api.gateio.ws/api/v4/spot/currency_pairs`
- `gate_currencies.json`: `https://api.gateio.ws/api/v4/spot/currencies`
- `cg_list.json`: `https://api.coingecko.com/api/v3/coins/list?include_platform=true`
- `cg_binance/`, `cg_gate/`: `./fetch_cg.sh binance` and `./fetch_cg.sh gate`
- `ru.json` and `ras.ts` (for `matrix.ts`): `GET /api/research-universe` from the
  workspace under test, and a copy of `web/src/features/discovery/researchAssetSearch.ts`

Then: `python3 gate_match.py`, `python3 cg_match.py`,
`node --experimental-strip-types matrix.ts`.
