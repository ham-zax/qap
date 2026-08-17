"""Deterministic Decimal arithmetic for economic evaluation."""

from collections.abc import Iterable
from decimal import MAX_EMAX, MIN_EMIN, Context, Decimal, localcontext

EVALUATION_PRECISION = 50
RECONCILIATION_TOLERANCE = Decimal("1e-45")
_ZERO = Decimal("0")
_CONTEXT = Context(prec=EVALUATION_PRECISION, Emin=MIN_EMIN, Emax=MAX_EMAX)


def _finite_components(value: Decimal) -> tuple[int, int, int]:
    if not value.is_finite():
        raise ValueError("economic arithmetic requires finite Decimal values")
    sign, digits, exponent = value.as_tuple()
    if not isinstance(exponent, int):
        raise ValueError("economic arithmetic requires finite Decimal values")
    coefficient = int("".join(str(digit) for digit in digits)) if digits else 0
    return sign, coefficient, exponent


def _from_coefficient(coefficient: int, exponent: int) -> Decimal:
    if coefficient == 0:
        return _ZERO
    sign = 1 if coefficient < 0 else 0
    digits = tuple(int(character) for character in str(abs(coefficient)))
    while len(digits) > 1 and digits[-1] == 0:
        digits = digits[:-1]
        exponent += 1
    return Decimal((sign, digits, exponent))


def canonical_decimal(value: Decimal) -> Decimal:
    """Return one context-independent finite representation."""

    sign, coefficient, exponent = _finite_components(value)
    return _from_coefficient(-coefficient if sign else coefficient, exponent)


def exact_sum(values: Iterable[Decimal]) -> Decimal:
    """Sum finite decimals exactly without ambient context dependence."""

    components = [_finite_components(value) for value in values]
    if not components:
        return _ZERO
    common_exponent = min(exponent for _, _, exponent in components)
    total = sum(
        (-coefficient if sign else coefficient) * 10 ** (exponent - common_exponent)
        for sign, coefficient, exponent in components
    )
    return _from_coefficient(total, common_exponent)


def exact_add(left: Decimal, right: Decimal) -> Decimal:
    return exact_sum((left, right))


def exact_subtract(left: Decimal, right: Decimal) -> Decimal:
    return exact_sum((left, right.copy_negate()))


def exact_multiply(left: Decimal, right: Decimal) -> Decimal:
    left_sign, left_coefficient, left_exponent = _finite_components(left)
    right_sign, right_coefficient, right_exponent = _finite_components(right)
    coefficient = left_coefficient * right_coefficient
    if left_sign != right_sign:
        coefficient = -coefficient
    return _from_coefficient(coefficient, left_exponent + right_exponent)


def divide(left: Decimal, right: Decimal) -> Decimal:
    """Divide under QAP's explicit financial evaluation context."""

    _finite_components(left)
    _finite_components(right)
    if right == _ZERO:
        raise ValueError("economic division denominator must be non-zero")
    with localcontext(_CONTEXT):
        return canonical_decimal(left / right)


def natural_log(value: Decimal) -> Decimal:
    """Take a positive natural log under the evaluation context."""

    _finite_components(value)
    if value <= _ZERO:
        raise ValueError("log-relative wealth requires strictly positive values")
    with localcontext(_CONTEXT) as context:
        return canonical_decimal(context.ln(value))
