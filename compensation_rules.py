
from decimal import Decimal, ROUND_HALF_UP

RULE_VERSION = "v1"

COMPENSATION_RATES = {
    "low": Decimal("0.00"),
    "medium": Decimal("0.02"),
    "high": Decimal("0.05"),
    "critical": Decimal("0.10"),
}


def calculate_compensation(
    payment_amount: Decimal,
    severity: str,
) -> tuple[Decimal, str]:
    rate = COMPENSATION_RATES.get(severity.lower())

    if rate is None:
        raise ValueError(f"Unsupported incident severity: {severity}")

    if payment_amount <= Decimal("0.00"):
        raise ValueError("Payment amount must be positive")

    compensation_amount = (
        payment_amount * rate
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    return compensation_amount, RULE_VERSION
