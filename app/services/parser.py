import re

from app.models.bill import Bill, BillItem


def parse_money(value: str) -> float:
    """Convert a currency-like string into a float."""

    cleaned = value.replace(",", "").replace("₹", "").replace("$", "").strip()

    return float(cleaned)


def calculate_confidence(
    name: str,
    quantity: float,
    item_total: float,
) -> tuple[float, float, float, float]:
    """
    Calculate confidence scores for an extracted bill item.

    The initial implementation uses deterministic rules.
    Later this can be replaced with OCR-model confidence.
    """

    name_confidence = 0.90 if name.strip() else 0.0
    quantity_confidence = 0.95 if quantity > 0 else 0.0
    price_confidence = 0.95 if item_total >= 0 else 0.0

    overall_confidence = (
        name_confidence
        + quantity_confidence
        + price_confidence
    ) / 3

    return (
        name_confidence,
        quantity_confidence,
        price_confidence,
        overall_confidence,
    )


def parse_bill_text(text: str) -> Bill:
    """Parse OCR text into a structured Bill."""

    items = []

    subtotal = 0.0
    tax = 0.0
    service_charge = 0.0
    discount = 0.0
    total = 0.0

    subtotal_confidence = 0.0
    tax_confidence = 0.0
    service_charge_confidence = 0.0
    discount_confidence = 0.0
    total_confidence = 0.0

    lines = text.splitlines()

    for line in lines:
        line = line.strip()

        if not line:
            continue

        lower_line = line.lower()

        money_values = re.findall(
            r"(?:₹|\$)?\s*\d+(?:,\d{3})*(?:\.\d{1,2})?",
            line,
        )

        if not money_values:
            continue

        try:
            values = [parse_money(value) for value in money_values]
        except ValueError:
            continue

        amount = values[-1]

        if "subtotal" in lower_line:
            subtotal = amount
            subtotal_confidence = 0.95

        elif "service charge" in lower_line:
            service_charge = amount
            service_charge_confidence = 0.95

        elif "tax" in lower_line:
            tax = amount
            tax_confidence = 0.95

        elif "discount" in lower_line:
            discount = amount
            discount_confidence = 0.95

        elif "total" in lower_line:
            total = amount
            total_confidence = 0.95

        else:
            item_match = re.match(
                r"(.+?)\s+(\d+(?:\.\d+)?)\s+"
                r"(?:₹|\$)?\s*"
                r"(\d+(?:,\d{3})*(?:\.\d{1,2})?)$",
                line,
            )

            if item_match:
                name = item_match.group(1).strip()
                quantity = float(item_match.group(2))
                item_total = parse_money(item_match.group(3))

                unit_price = item_total / quantity

                (
                    name_confidence,
                    quantity_confidence,
                    price_confidence,
                    item_confidence,
                ) = calculate_confidence(
                    name,
                    quantity,
                    item_total,
                )

                items.append(
                    BillItem(
                        name=name,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=item_total,
                        name_confidence=name_confidence,
                        quantity_confidence=quantity_confidence,
                        price_confidence=price_confidence,
                        confidence=item_confidence,
                    )
                )

    confidence_values = []

    for item in items:
        confidence_values.append(item.confidence)

    confidence_values.extend(
        [
            subtotal_confidence,
            tax_confidence,
            service_charge_confidence,
            discount_confidence,
            total_confidence,
        ]
    )

    non_zero_confidences = [
        value for value in confidence_values if value > 0
    ]

    overall_confidence = (
        sum(non_zero_confidences) / len(non_zero_confidences)
        if non_zero_confidences
        else 0.0
    )

    return Bill(
        items=items,
        subtotal=subtotal,
        tax=tax,
        service_charge=service_charge,
        discount=discount,
        total=total,
        subtotal_confidence=subtotal_confidence,
        tax_confidence=tax_confidence,
        service_charge_confidence=service_charge_confidence,
        discount_confidence=discount_confidence,
        total_confidence=total_confidence,
        confidence=overall_confidence,
    )