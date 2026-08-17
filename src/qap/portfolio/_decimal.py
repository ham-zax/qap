"""Context-independent exact Decimal arithmetic for portfolio accounting."""

from collections.abc import Iterable
from decimal import Decimal

_ZERO = Decimal("0")


def _finite_components(value: Decimal) -> tuple[int, int]:
    sign, digits, exponent = value.as_tuple()
    if not isinstance(exponent, int):
        raise ValueError("exact portfolio arithmetic requires finite Decimal values")

    coefficient = 0
    for digit in digits:
        coefficient = coefficient * 10 + digit
    if sign:
        coefficient = -coefficient
    return coefficient, exponent


def _from_coefficient(coefficient: int, exponent: int) -> Decimal:
    if coefficient == 0:
        return _ZERO

    sign = 1 if coefficient < 0 else 0
    magnitude = abs(coefficient)
    while magnitude % 10 == 0:
        magnitude //= 10
        exponent += 1

    reversed_digits: list[int] = []
    while magnitude:
        magnitude, digit = divmod(magnitude, 10)
        reversed_digits.append(digit)
    digits = tuple(reversed(reversed_digits))
    return Decimal((sign, digits, exponent))


def canonical_decimal(value: Decimal) -> Decimal:
    """Return one context-free representation with no insignificant zeros."""

    coefficient, exponent = _finite_components(value)
    return _from_coefficient(coefficient, exponent)


def exact_sum(values: Iterable[Decimal]) -> Decimal:
    """Add finite Decimals exactly without consulting the ambient context."""

    components = tuple(_finite_components(value) for value in values)
    if not components:
        return _ZERO

    common_exponent = min(exponent for _, exponent in components)
    total_coefficient = sum(
        coefficient * 10 ** (exponent - common_exponent)
        for coefficient, exponent in components
    )
    return _from_coefficient(total_coefficient, common_exponent)


def exact_add(left: Decimal, right: Decimal) -> Decimal:
    """Add two finite Decimals exactly without ambient precision/exponent limits."""

    return exact_sum((left, right))
