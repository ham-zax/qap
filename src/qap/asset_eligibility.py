"""D4 discovery exclusions; admission remains owned by ProductUniverse."""

import re
from dataclasses import dataclass
from typing import Literal

from qap.market.directory import SpotCurrencyEvidence

EligibilityReason = Literal[
    "owned_spot_candidate",
    "fiat_currency",
    "leveraged_token",
    "tokenized_stock",
    "synthetic_asset",
]

_FIAT = frozenset(
    "USD EUR GBP AUD CAD CHF JPY CNY TRY BRL ARS RUB UAH NGN PLN ZAR AED INR IDR "
    "KRW VND THB HKD SGD TWD MXN COP SEK NOK DKK NZD SAR ILS PEN CLP CZK HUF "
    "RON BGN PKR BDT EGP KZT GEL UZS BYN UYU BOB RSD LKR NPR PHP MYR".split()
)
_LEVERAGED_CODE = re.compile(r"[235]\d*[LS]$")
_LEVERAGED_NAME = re.compile(r"\d+x\s*(?:long|short)\b", re.IGNORECASE)
# Binance's retired UP/DOWN and BULL/BEAR tokens carry no leverage marker in a name.
_DIRECTIONAL = re.compile(
    r"^(?:BTC|ETH|BNB|XRP|DOT|ADA|LINK|LTC|BCH|EOS|TRX|XTZ|SUSHI|YFI|UNI|SXP|FIL|"
    r"AAVE|XLM|1INCH)(?:UP|DOWN|BULL|BEAR)$"
)
_TOKENIZED_NAME = re.compile(r"tokeni[sz]ed|\bx\s?stocks?\b", re.IGNORECASE)
# Venue and registry class labels; "ondo-stocks" alone also tags the ONDO token.
_STOCK_CLASSES = frozenset({"stocks", "xstocks", "gstocks", "equities", "equity"})
_SYNTHETIC_CLASSES = frozenset({"metals", "commodities", "indices"})
# Binance lists every tokenized stock (AAPLB, TSLAB …) under this permission group,
# including those the registry does not name as stocks. Observed 2026-09-30.
_BINANCE_STOCK_PERMISSION = "TRD_GRP_261"
# Gate tags stablecoins such as USDC as forex; that alone is not synthetic exposure.
_FOREX_CLASSES = frozenset({"forex", "foreign exchange"})


@dataclass(frozen=True)
class AssetEligibility:
    eligible: bool
    reason: EligibilityReason


def _classes(*sources: tuple[str, ...]) -> frozenset[str]:
    return frozenset(
        category.strip().lower().replace("_", " ").replace("-", " ")
        for categories in sources
        for category in categories
    )


def classify_asset(
    code: str,
    *,
    currency: SpotCurrencyEvidence | None = None,
    registry_categories: tuple[str, ...] = (),
    names: tuple[str, ...] = (),
    registry_evidence: bool = False,
    venue_permissions: tuple[str, ...] = (),
) -> AssetEligibility:
    """Classify one venue asset code from venue metadata and registry evidence.

    `registry_evidence` says the registry identifies a crypto asset for this
    venue code. It keeps real assets eligible when they share a fiat code (RON, BOB)
    or carry a venue forex tag (USDC).
    """

    normalized = code.upper()
    venue_categories = () if currency is None else currency.categories
    classes = _classes(registry_categories, venue_categories)
    all_names = names + (
        () if currency is None or currency.name is None else (currency.name,)
    )
    if any(_LEVERAGED_NAME.search(name) for name in all_names) or (
        not all_names and _LEVERAGED_CODE.search(normalized)
    ):
        return AssetEligibility(False, "leveraged_token")
    if _DIRECTIONAL.search(normalized):
        return AssetEligibility(False, "leveraged_token")
    if _BINANCE_STOCK_PERMISSION in venue_permissions:
        return AssetEligibility(False, "tokenized_stock")
    if classes & _STOCK_CLASSES or any(_TOKENIZED_NAME.search(n) for n in all_names):
        return AssetEligibility(False, "tokenized_stock")
    if classes & _SYNTHETIC_CLASSES or (
        classes & _FOREX_CLASSES and not registry_evidence
    ):
        return AssetEligibility(False, "synthetic_asset")
    if normalized in _FIAT and not registry_evidence:
        return AssetEligibility(False, "fiat_currency")
    return AssetEligibility(True, "owned_spot_candidate")
