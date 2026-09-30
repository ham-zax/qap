"""D4 discovery exclusions, over recorded Gate currency evidence where possible."""

import pytest

from qap.asset_eligibility import AssetEligibility, classify_asset
from qap.market.adapters.spot_directory import gate_currencies_from_payload
from qap.market.directory import SpotCurrencyEvidence

from .recorded import load

_GATE = {
    currency.venue_asset_code: currency
    for currency in gate_currencies_from_payload(load("gate_case_currencies.json"))
}


@pytest.mark.parametrize(
    ("code", "reason"),
    [
        ("ARB3L", "leveraged_token"),  # recorded Gate name "ARB3xLong"
        ("AAPLX", "tokenized_stock"),  # recorded Gate categories stocks, xstocks
    ],
)
def test_recorded_gate_metadata_excludes_with_a_typed_reason(
    code: str, reason: str
) -> None:
    result = classify_asset(code, currency=_GATE[code])

    assert (result.eligible, result.reason) == (False, reason)


def test_recorded_crypto_assets_remain_eligible() -> None:
    for code in ("W", "BTC", "ETH", "DYDX", "GHO", "DAI"):
        assert classify_asset(code, currency=_GATE[code]).eligible, code


def test_ondo_token_is_not_excluded_by_its_ondo_stocks_category_alone() -> None:
    assert _GATE["ONDO"].categories == ("ondo-stocks",)

    assert classify_asset("ONDO", currency=_GATE["ONDO"]).eligible


def test_forex_tag_excludes_only_without_registry_crypto_evidence() -> None:
    usdc = _GATE["USDC"]
    assert usdc.categories == ("forex",)

    without = classify_asset("USDC", currency=usdc)
    with_evidence = classify_asset("USDC", currency=usdc, registry_evidence=True)

    assert (without.eligible, without.reason) == (False, "synthetic_asset")
    assert with_evidence.eligible


def test_fiat_code_excluded_unless_registry_identifies_a_crypto_asset() -> None:
    """RON is Ronin on Gate: the registry ticker keeps it eligible."""

    assert classify_asset("EUR").reason == "fiat_currency"
    assert classify_asset("RON").reason == "fiat_currency"
    assert classify_asset("RON", registry_evidence=True).eligible


@pytest.mark.parametrize("code", ["BTCUP", "ETHDOWN", "XRPBULL", "SXPBEAR"])
def test_binance_directional_tokens_are_leveraged_without_any_name(
    code: str,
) -> None:
    result = classify_asset(code)

    assert (result.eligible, result.reason) == (False, "leveraged_token")


def test_ordinary_codes_ending_like_directional_tokens_stay_eligible() -> None:
    for code in ("JUP", "SYRUP", "BULL", "BEAR"):
        assert classify_asset(code).eligible, code


def test_leveraged_code_pattern_only_applies_when_no_name_is_known() -> None:
    assert classify_asset("PENGU3L").reason == "leveraged_token"
    assert classify_asset("PENGU3L", names=("Pengu Long Duration Coin",)).eligible


def test_registry_names_identify_binance_tokenized_stocks() -> None:
    result = classify_asset("AAPLB", names=("Apple (Binance Tokenized Stock)",))

    assert (result.eligible, result.reason) == (False, "tokenized_stock")


@pytest.mark.parametrize(
    ("category", "reason"),
    [
        ("metals", "synthetic_asset"),
        ("commodities", "synthetic_asset"),
        ("indices", "synthetic_asset"),
        ("stocks", "tokenized_stock"),
        ("xstocks", "tokenized_stock"),
    ],
)
def test_venue_classes_exclude_even_with_registry_evidence(
    category: str, reason: str
) -> None:
    currency = SpotCurrencyEvidence(venue_asset_code="XYZ", categories=(category,))

    result = classify_asset("XYZ", currency=currency, registry_evidence=True)

    assert (result.eligible, result.reason) == (False, reason)


def test_registry_supplied_categories_are_classified_like_venue_ones() -> None:
    result = classify_asset("XYZ", registry_categories=("Tokenized_Stocks",))
    assert result.eligible  # only exact class labels count, not substrings

    assert not classify_asset("XYZ", registry_categories=("stocks",)).eligible


def test_binance_stock_permission_group_excludes_unnamed_tokenized_stocks() -> None:
    """ADBEB carries no stock name or class; Binance's stock permission group does."""

    result = classify_asset(
        "ADBEB", registry_evidence=False, venue_permissions=("TRD_GRP_261",)
    )

    assert result == AssetEligibility(False, "tokenized_stock")
