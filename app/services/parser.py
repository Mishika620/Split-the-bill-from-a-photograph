import re

from app.models.bill import Bill, BillItem


def parse_money(value: str) -> float:
    """Convert a currency-like string into a float."""

    cleaned = value.replace(",", "").replace("₹", "").strip()

    return float(cleaned)


def parse_bill_text(text: str) -> Bill:
    """Parse OCR text into a structured Bill."""

    items = []

    subtotal = 0.0
    tax = 0.0
    service_charge = 0.0
    discount = 0.0
    total = 0.0

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

        elif "service charge" in lower_line:
            service_charge = amount

        elif "tax" in lower_line:
            tax = amount

        elif "discount" in lower_line:
            discount = amount

        elif "total" in lower_line:
            total = amount

        else:
            item_match = re.match(
                r"(.+?)\s+(\d+(?:\.\d+)?)\s+"
                r"(?:₹|\$)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)$",
                line,
            )

            if item_match:
                name = item_match.group(1).strip()
                quantity = float(item_match.group(2))
                item_total = parse_money(item_match.group(3))

                unit_price = item_total / quantity

                items.append(
                    BillItem(
                        name=name,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=item_total,
                    )
                )

    return Bill(
        items=items,
        subtotal=subtotal,
        tax=tax,
        service_charge=service_charge,
        discount=discount,
        total=total,
    )