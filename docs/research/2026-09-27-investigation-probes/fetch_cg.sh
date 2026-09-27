#!/usr/bin/env bash
# Fetch all CoinGecko exchange ticker pages (keyless) for one exchange id.
set -u
ex="$1"
mkdir -p "cg_$ex"
for page in $(seq 1 80); do
  out="cg_$ex/p$page.json"
  for _ in 1 2 3 4 5; do
    code=$(curl -sS --max-time 30 -o "$out" -w '%{http_code}' "https://api.coingecko.com/api/v3/exchanges/$ex/tickers?page=$page&order=base_target")
    if [ "$code" = "200" ]; then break; fi
    sleep 30
  done
  n=$(jq '.tickers|length' "$out" 2>/dev/null || echo 0)
  echo "$ex page=$page code=$code n=$n"
  if [ "$n" = "0" ]; then break; fi
  sleep 13
done
