"""Token-efficient AI-Agent CLI for QAP Pair Rotation Lab."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from pydantic import ValidationError

from qap.experiment.lab_statistics import FamilyResolutionError
from qap.experiment.live_paper_execution import BookProvider
from qap.experiment.live_paper_runner import LivePaperError
from qap.lab_cli_paper import (
    PAPER_COMMANDS,
    PaperInputsProvider,
    add_paper_parsers,
    format_paper_md,
    run_paper_command,
)
from qap.policy.lab_settings import LabSettings
from qap.product_lab_advisor import advise_pair_strategies
from qap.product_lab_store import LabStoreError, LabStudyStore
from qap.product_lab_study import LabStudyService
from qap.product_market_data import ProductMarketData, ProductMarketDataError
from qap.product_market_data_generation import ProductGenerationReadError
from qap.product_pair_rotation_analysis import PairAnalysisError, PairRotationAnalysis
from qap.product_pair_rotation_data import (
    PairRotationData,
    ProductMarketDataPreparationError,
)
from qap.product_paper_inputs import PaperInputError
from qap.product_universe import ProductUniverse, ProductUniverseError


def _compact_study(envelope: dict[str, Any]) -> dict[str, Any]:
    res = envelope["result"]
    return {
        "study_id": envelope["study_id"],
        "created_at": envelope["created_at"],
        "call": res["call"],
        "proof": res["proof"],
        "statistics": {
            k: {
                "terminal_value_usdt": v.get("terminal_value_usdt"),
                "return_pct": v.get("return_pct"),
                "maximum_drawdown_pct": v.get("maximum_drawdown_pct"),
                "rotations": v.get("rotations"),
                "fees_usdt": v.get("fees_usdt"),
                "slippage_usdt": v.get("slippage_usdt"),
            }
            for k, v in res.get("statistics", {}).items()
        },
        "trade_count": len(res.get("trades", [])),
    }


def _format_md(payload: Any) -> str:
    if isinstance(payload, dict) and "studies" in payload and "advisor" in payload:
        p_map = cast(dict[str, Any], payload)
        lines = [
            f"## Compare (best={p_map.get('best_study_id')})",
            f"Regime: {p_map['advisor']['regime_label']}",
        ]
        for s in cast(list[dict[str, Any]], p_map["studies"]):
            p = s["proof"]
            lines.append(
                f"- {s['study_id'][:10]} call={s['call']['status']} "
                f"passes={p['passes']} vs_hodl={p['vs_hodl_pct']} "
                f"vs_ctrl={p['vs_control_pct']}"
            )
        return "\n".join(lines)
    if isinstance(payload, dict) and "proof" in payload and "call" in payload:
        p_map = cast(dict[str, Any], payload)
        p = p_map["proof"]
        return (
            f"## Study {p_map['study_id'][:12]}\n"
            f"call: {p_map['call']['status']} ({p_map['call']['headline']})\n"
            f"passes={p['passes']} vs_hodl={p['vs_hodl_pct']} "
            f"vs_ctrl={p['vs_control_pct']} trades={p_map['trade_count']}"
        )
    if isinstance(payload, dict) and "measurements" in payload:
        p_map = cast(dict[str, Any], payload)
        adv = p_map.get("advisor", {})
        return (
            f"## Analysis {p_map['coin_a']['code']}/{p_map['coin_b']['code']} "
            f"({p_map['bar']})\nregime={adv.get('regime_label')}\n"
            f"{adv.get('pro_summary', '')}"
        )
    return json.dumps(payload, indent=2, default=str)


def _build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--run-root", type=Path, default=Path("runs"))
    common.add_argument("--data-root", type=Path, default=Path("."))
    common.add_argument("--actor-id", default="local")
    common.add_argument("--format", choices=["json", "md"], default="json")
    parser = argparse.ArgumentParser(prog="qap.lab_cli", parents=[common])
    sub = parser.add_subparsers(dest="command", required=True)

    p_coins = sub.add_parser("coins", parents=[common])
    p_coins.add_argument("--query", default="")
    p_coins.add_argument("--limit", type=int, default=25)
    p_coins.add_argument("--prepare", action="store_true")

    p_prep = sub.add_parser("prepare", parents=[common])
    p_prep.add_argument("--coin-a", required=True)
    p_prep.add_argument("--coin-b", required=True)
    p_prep.add_argument("--anchor", default=None)
    p_prep.add_argument("--days", type=int, default=365)

    p_ana = sub.add_parser("analyze", parents=[common])
    p_ana.add_argument("--coin-a", required=True)
    p_ana.add_argument("--coin-b", required=True)
    p_ana.add_argument("--anchor", default=None)
    p_ana.add_argument("--bar", choices=["1m", "15m", "1h", "4h", "1d"], default="1h")
    p_ana.add_argument("--days", type=int, default=180)
    p_ana.add_argument("--band-lookback", type=int, default=672)
    p_ana.add_argument("--include-series", action="store_true")

    p_study = sub.add_parser("study", parents=[common])
    p_study.add_argument("--coin-a", required=True)
    p_study.add_argument("--coin-b", required=True)
    p_study.add_argument("--anchor", default=None)
    p_study.add_argument("--bar", choices=["1m", "15m", "1h", "4h", "1d"], default="1h")
    p_study.add_argument("--days", type=int, default=180)
    p_study.add_argument("--band-lookback", type=int, default=672)
    p_study.add_argument("--settings", default="{}")

    p_cmp = sub.add_parser("compare", parents=[common])
    p_cmp.add_argument("--coin-a", required=True)
    p_cmp.add_argument("--coin-b", required=True)
    p_cmp.add_argument("--anchor", default=None)
    p_cmp.add_argument("--bar", choices=["1m", "15m", "1h", "4h", "1d"], default="1h")
    p_cmp.add_argument("--days", type=int, default=180)
    p_cmp.add_argument("--band-lookback", type=int, default=672)
    p_cmp.add_argument("--candidates", default=None)

    p_saved = sub.add_parser("saved", parents=[common])
    p_saved.add_argument("--limit", type=int, default=20)
    p_saved.add_argument("--study-id", default=None)
    add_paper_parsers(sub.add_parser, common)
    return parser


def _run_command(
    args: argparse.Namespace, book_provider: BookProvider | None = None
) -> Any:
    if args.command in PAPER_COMMANDS:
        return run_paper_command(args, book_provider)
    uni = ProductUniverse(args.run_root)
    data = ProductMarketData(args.run_root, args.data_root)
    repo_root = Path(__file__).resolve().parents[2]

    if args.command == "coins":
        if args.prepare and uni.read_directory() is None:
            uni.refresh_directory()
        return {"coins": uni.search(args.query, limit=args.limit)}

    if args.command == "prepare":
        prep = PairRotationData(uni, data)
        scope = uni.research_scope((str(args.coin_a), str(args.coin_b)))
        proj = prep.prepare(scope, lookback_days=args.days, include_execution=True)
        datasets = [g.dataset_id for g in proj.generations]
        if (
            args.anchor
            and str(args.anchor) != "none"
            and str(args.anchor) not in (str(args.coin_a), str(args.coin_b))
        ):
            a_scope = uni.research_scope((str(args.coin_a), str(args.anchor)))
            a_proj = prep.prepare(
                a_scope, lookback_days=args.days, include_execution=True
            )
            datasets.extend(g.dataset_id for g in a_proj.generations)
        return {"datasets": sorted(set(datasets))}

    if args.command == "analyze":
        analysis = PairRotationAnalysis(uni, data, args.data_root).analyze(
            args.coin_a,
            args.coin_b,
            bar=args.bar,
            days=args.days,
            band_lookback=args.band_lookback,
            anchor=args.anchor,
        )
        advisor = advise_pair_strategies(analysis)
        out = dict(analysis)
        if not args.include_series:
            out.pop("series", None)
        out["advisor"] = advisor
        return out

    if args.command == "study":
        settings = LabSettings.model_validate(json.loads(args.settings))
        svc = LabStudyService(
            uni, data, args.data_root, args.run_root, repo_root, actor_id=args.actor_id
        )
        env = svc.run(
            args.coin_a,
            args.coin_b,
            bar=args.bar,
            days=args.days,
            band_lookback=args.band_lookback,
            anchor=args.anchor,
            settings=settings,
        )
        return _compact_study(env)

    if args.command == "compare":
        svc = LabStudyService(
            uni, data, args.data_root, args.run_root, repo_root, actor_id=args.actor_id
        )
        if args.candidates is not None:
            raw_cands = json.loads(args.candidates)
            if not isinstance(raw_cands, list):
                raise ValueError("--candidates must be a JSON array.")
            cands = [
                LabSettings.model_validate(item)
                for item in cast(list[object], raw_cands)
            ]
        else:
            analysis = PairRotationAnalysis(uni, data, args.data_root).analyze(
                args.coin_a,
                args.coin_b,
                bar=args.bar,
                days=args.days,
                band_lookback=args.band_lookback,
                anchor=args.anchor,
            )
            cands = [
                LabSettings.model_validate(s["settings"])
                for s in advise_pair_strategies(analysis)["suggestions"]
            ]
        comp = svc.compare(
            args.coin_a,
            args.coin_b,
            bar=args.bar,
            days=args.days,
            band_lookback=args.band_lookback,
            anchor=args.anchor,
            candidates=cands,
        )
        return {
            "advisor": comp["advisor"],
            "best_study_id": comp["best_study_id"],
            "studies": [_compact_study(s) for s in comp["studies"]],
        }

    store = LabStudyStore(args.run_root, actor_id=args.actor_id)
    if args.study_id:
        return _compact_study(store.read(args.study_id))
    return {"studies": store.list(limit=args.limit)}


def main(
    argv: Sequence[str] | None = None,
    *,
    book_provider: BookProvider | None = None,
    paper_inputs_provider: PaperInputsProvider | None = None,
) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    try:
        if args.command in PAPER_COMMANDS:
            payload = run_paper_command(
                args,
                book_provider,
                paper_inputs_provider=paper_inputs_provider,
            )
        else:
            payload = _run_command(args, book_provider)
    except (
        FamilyResolutionError,
        LabStoreError,
        LivePaperError,
        PaperInputError,
        PairAnalysisError,
        ProductUniverseError,
        ProductMarketDataError,
        ProductMarketDataPreparationError,
        ProductGenerationReadError,
    ) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 3
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    if args.format != "md":
        text = json.dumps(payload, separators=(",", ":"), default=str)
    elif args.command in PAPER_COMMANDS:
        text = format_paper_md(payload)
    else:
        text = _format_md(payload)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
