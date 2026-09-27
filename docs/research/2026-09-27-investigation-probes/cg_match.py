"""Measure venue-code -> CoinGecko coin_id coverage from exchange tickers."""

import glob
import json
import re
from collections import Counter, defaultdict


def tickers(ex):
    out = defaultdict(set)
    stale = set()
    for path in glob.glob(f"cg_{ex}/p*.json"):
        for t in json.load(open(path)).get("tickers", []):
            if t.get("coin_id"):
                out[t["base"].upper()].add(t["coin_id"])
                if t.get("is_stale") or t.get("is_anomaly"):
                    stale.add(t["base"].upper())
    return out, stale


ei = json.load(open("binance_ei.json"))["symbols"]
bn_bases = sorted(
    {
        s["baseAsset"]
        for s in ei
        if s["quoteAsset"] == "USDT"
        and s["status"] == "TRADING"
        and s["isSpotTradingAllowed"]
    }
)
cur = {c["currency"].upper(): c for c in json.load(open("gate_currencies.json"))}
gp = json.load(open("gate_pairs.json"))
lev = re.compile(r"\d+x(Long|Short)$", re.I)
gt_all = sorted(
    {
        p["base"].upper()
        for p in gp
        if p["quote"] == "USDT" and p["trade_status"] == "tradable"
    }
)
gt_crypto = [
    b
    for b in gt_all
    if not lev.search(cur.get(b, {}).get("name") or "")
    and not cur.get(b, {}).get("category")
]

cg = json.load(open("cg_list.json"))
by_addr = defaultdict(set)
for c in cg:
    for a in (c.get("platforms") or {}).values():
        if a:
            by_addr[a.strip().lower()].add(c["id"])


def addr_ids(b):
    addrs = {
        ch["addr"].strip().lower()
        for ch in cur.get(b, {}).get("chains", [])
        if ch.get("addr")
    }
    return set().union(*(by_addr.get(a, set()) for a in addrs)) if addrs else None


for ex, bases in (("binance", bn_bases), ("gate", gt_crypto)):
    m, stale = tickers(ex)
    c = Counter()
    for b in bases:
        ids = m.get(b, set())
        c["unique" if len(ids) == 1 else ("multi" if ids else "none")] += 1
    print(
        ex,
        "USDT bases considered:",
        len(bases),
        dict(c),
        "stale_or_anomaly:",
        len(stale & set(bases)),
    )
    print("  none sample:", [b for b in bases if not m.get(b)][:25])

bm, _ = tickers("binance")
gm, _ = tickers("gate")
agree = Counter()
for b in gt_crypto:
    a = addr_ids(b)
    t = gm.get(b, set())
    if a is None or len(a) != 1 or len(t) != 1:
        continue
    agree["address_and_ticker_agree" if a == t else "address_and_ticker_DISAGREE"] += 1
print("gate address vs ticker:", dict(agree))

combined = Counter()
for b in gt_crypto:
    a = addr_ids(b)
    t = gm.get(b, set())
    ids = (a if a and len(a) == 1 else set()) | (t if len(t) == 1 else set())
    combined[
        "resolved" if len(ids) == 1 else ("conflict" if len(ids) > 1 else "unresolved")
    ] += 1
print("gate combined (address OR ticker, conflict if disagree):", dict(combined))

both = sorted(set(bn_bases) & set(gt_all))
x = Counter()
diff = []
for b in both:
    bi, gi = bm.get(b, set()), gm.get(b, set())
    if len(bi) == 1 and len(gi) == 1:
        if bi == gi:
            x["same_coin"] += 1
        else:
            x["SAME_TICKER_DIFFERENT_COIN"] += 1
            diff.append((b, sorted(bi)[0], sorted(gi)[0]))
    else:
        x["undetermined"] += 1
print("cross-venue same ticker:", len(both), dict(x))
print("  different-coin examples:", diff[:15])
print(
    "W:",
    bm.get("W"),
    gm.get("W"),
    "BTC:",
    bm.get("BTC"),
    gm.get("BTC"),
    "DAI:",
    bm.get("DAI"),
    gm.get("DAI"),
    "PIXEL:",
    bm.get("PIXEL"),
    gm.get("PIXEL"),
)
stockish = [
    b
    for b in bn_bases
    if len(bm.get(b, set())) == 1
    and re.search(r"stock|tokenized|ondo|xstock|backed", next(iter(bm[b])))
]
print("binance resolved to stock-like coin ids:", len(stockish), stockish[:10])
dis = []
for b in gt_crypto:
    a = addr_ids(b)
    t = gm.get(b, set())
    if a and len(a) == 1 and len(t) == 1 and a != t:
        dis.append((b, sorted(a)[0], sorted(t)[0]))
print("gate disagreements:", dis)
