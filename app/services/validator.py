from dataclasses import dataclass

from app.models.bill import Bill


@dataclass
class ValidationResult:
    valid: bool
    items_total: float
    expected_total: float
    printed_subtotal: float
    printed_total: float
    subtotal_difference: float
    total_difference: float
    errors: list[str]


def validate_bill(
    bill: Bill,
    tolerance: float = 0.01,
) -> ValidationResult:
    """
    Validate the arithmetic of an extracted bill.

    Checks:
    1. Sum of item totals vs printed subtotal.
    2. Subtotal + tax + service charge - discount vs printed total.
    """

    errors = []

    # Calculate total from individual items.
    items_total = round(
        sum(item.total_price for item in bill.items),
        2,
    )

    # Calculate difference between items and printed subtotal.
    subtotal_difference = round(
        items_total - bill.subtotal,
        2,
    )

    if abs(subtotal_difference) > tolerance:
        errors.append(
            "Item total does not match the printed subtotal."
        )

    # Calculate what the final bill should be.
    expected_total = round(
        bill.subtotal
        + bill.tax
        + bill.service_charge
        - bill.discount,
        2,
    )

    # Compare expected total with printed total.
    total_difference = round(
        expected_total - bill.total,
        2,
    )

    if abs(total_difference) > tolerance:
        errors.append(
            "Printed total does not match the calculated total."
        )

    return ValidationResult(
        valid=len(errors) == 0,
        items_total=items_total,
        expected_total=expected_total,
        printed_subtotal=bill.subtotal,
        printed_total=bill.total,
        subtotal_difference=subtotal_difference,
        total_difference=total_difference,
        errors=errors,
    )