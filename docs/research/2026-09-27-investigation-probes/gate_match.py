"""Measure Gate metadata coverage and CoinGecko contract-address matching."""

import json
import re
from collections import Counter, defaultdict

cur = {c["currency"].upper(): c for c in json.load(open("gate_currencies.json"))}
pairs = json.load(open("gate_pairs.json"))
usdt = [p for p in pairs if p["quote"] == "USDT" and p["trade_status"] == "tradable"]
bases = sorted({p["base"].upper() for p in usdt})
cg = json.load(open("cg_list.json"))
by_addr = defaultdict(set)
by_sym = defaultdict(set)
for c in cg:
    by_sym[c["symbol"].lower()].add(c["id"])
    for addr in (c.get("platforms") or {}).values():
        if addr:
            by_addr[addr.strip().lower()].add(c["id"])

stats = Counter()
examples = defaultdict(list)
for b in bases:
    c = cur.get(b)
    if not c:
        stats["no_currency_record"] += 1
        continue
    if c.get("name"):
        stats["has_name"] += 1
    if c.get("category"):
        stats["has_category"] += 1
        for cat in c["category"]:
            stats[f"category:{cat}"] += 1
    addrs = {ch["addr"].strip().lower() for ch in c.get("chains", []) if ch.get("addr")}
    ids = set().union(*(by_addr.get(a, set()) for a in addrs)) if addrs else set()
    sym_ids = by_sym.get(b.lower(), set())
    if not addrs:
        stats["no_contract_address (native or unknown)"] += 1
        key = (
            "native_symbol_unique"
            if len(sym_ids) == 1
            else ("native_symbol_ambiguous" if sym_ids else "native_symbol_none")
        )
    elif len(ids) == 1:
        key = "address_unique_match"
    elif len(ids) > 1:
        key = "address_multi_match"
    else:
        key = "address_no_match"
    stats[key] += 1
    if len(examples[key]) < 8:
        examples[key].append(
            (b, c.get("name"), sorted(ids)[:3] if addrs else len(sym_ids))
        )
    if len(sym_ids) > 1:
        stats["symbol_collision_in_coingecko"] += 1

print("gate tradable USDT bases:", len(bases))
for k, v in sorted(stats.items()):
    print(f"  {k}: {v}")
for k, v in examples.items():
    print(k, v)


lev = re.compile(r"\d+x(Long|Short)$", re.I)


def klass(b):
    c = cur.get(b, {})
    name = c.get("name") or ""
    if lev.search(name) or re.search(r"\d[LS]$", b) and "x" in name.lower():
        return "leveraged_token"
    if c.get("category"):
        return "stock_or_rwa_category"
    return "crypto"


cls = Counter()
res = Counter()
for b in bases:
    k = klass(b)
    cls[k] += 1
    c = cur[b]
    addrs = {ch["addr"].strip().lower() for ch in c.get("chains", []) if ch.get("addr")}
    ids = set().union(*(by_addr.get(a, set()) for a in addrs)) if addrs else set()
    sym = by_sym.get(b.lower(), set())
    if k != "crypto":
        continue
    if addrs and len(ids) == 1:
        res["address_unique"] += 1
    elif addrs and len(ids) > 1:
        res["address_multi"] += 1
    elif addrs:
        res["address_none"] += 1
    elif len(sym) == 1:
        res["native_symbol_unique(weak)"] += 1
    elif sym:
        res["native_symbol_ambiguous"] += 1
    else:
        res["native_none"] += 1
print("classes", dict(cls))
print("crypto-class resolution", dict(res))
