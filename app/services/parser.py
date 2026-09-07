import re

from app.models.bill import Bill, BillItem


MONEY_PATTERN = r"(?:₹|Rs\.?|INR|\$|€|£)?\s*\d+(?:,\d{3})*(?:\.\d{1,2})?"


def parse_money(value: str) -> float:
    """Convert a currency-like string into a float."""

    cleaned = (
        value.replace(",", "")
        .replace("₹", "")
        .replace("Rs.", "")
        .replace("Rs", "")
        .replace("INR", "")
        .replace("$", "")
        .replace("€", "")
        .replace("£", "")
        .strip()
    )

    return float(cleaned)


def calculate_confidence(
    name: str,
    quantity: float,
    item_total: float,
) -> tuple[float, float, float, float]:
    """Calculate deterministic confidence scores for an item."""

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


def extract_money_values(line: str) -> list[float]:
    """Extract all money-like values from a line."""

    matches = re.findall(MONEY_PATTERN, line)

    values = []

    for match in matches:
        try:
            values.append(parse_money(match))
        except ValueError:
            continue

    return values


def is_summary_line(line: str) -> bool:
    """Check whether a line represents a bill summary field."""

    lower_line = line.lower()

    summary_keywords = [
        "subtotal",
        "tax",
        "gst",
        "cgst",
        "sgst",
        "vat",
        "service charge",
        "service",
        "discount",
        "grand total",
        "total",
        "amount due",
        "net amount",
    ]

    return any(keyword in lower_line for keyword in summary_keywords)


def parse_item_line(line: str) -> BillItem | None:
    """
    Parse common item formats such as:

    Pizza 1 250
    Pizza 2 $500.00
    Pizza 250
    """

    # Format:
    # Item Name   Quantity   Price
    match = re.match(
        rf"^(.+?)\s+(\d+(?:\.\d+)?)\s+({MONEY_PATTERN})$",
        line,
        re.IGNORECASE,
    )

    if match:
        name = match.group(1).strip()
        quantity = float(match.group(2))
        item_total = parse_money(match.group(3))

    else:
        # Format:
        # Item Name   Price
        match = re.match(
            rf"^(.+?)\s+({MONEY_PATTERN})$",
            line,
            re.IGNORECASE,
        )

        if not match:
            return None

        name = match.group(1).strip()
        quantity = 1.0
        item_total = parse_money(match.group(2))

    # Avoid treating random OCR text as an item.
    if not name:
        return None

    # Remove obvious non-item lines.
    if is_summary_line(name):
        return None

    unit_price = item_total / quantity if quantity > 0 else 0.0

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

    return BillItem(
        name=name,
        quantity=quantity,
        unit_price=round(unit_price, 2),
        total_price=round(item_total, 2),
        name_confidence=name_confidence,
        quantity_confidence=quantity_confidence,
        price_confidence=price_confidence,
        confidence=item_confidence,
    )


def parse_bill_text(text: str) -> Bill:
    """Parse OCR text into a structured Bill."""

    items: list[BillItem] = []

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

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            continue

        lower_line = line.lower()

        money_values = extract_money_values(line)

        if not money_values:
            continue

        amount = money_values[-1]

        # -------------------------
        # SUBTOTAL
        # -------------------------
        if "subtotal" in lower_line:
            subtotal = amount
            subtotal_confidence = 0.95
            continue

        # -------------------------
        # TAX / GST
        # -------------------------
        if any(
            keyword in lower_line
            for keyword in [
                "tax",
                "gst",
                "cgst",
                "sgst",
                "vat",
            ]
        ):
            tax += amount
            tax_confidence = 0.95
            continue

        # -------------------------
        # SERVICE CHARGE
        # -------------------------
        if (
            "service charge" in lower_line
            or "service fee" in lower_line
        ):
            service_charge = amount
            service_charge_confidence = 0.95
            continue

        # -------------------------
        # DISCOUNT
        # -------------------------
        if "discount" in lower_line:
            discount = amount
            discount_confidence = 0.95
            continue

        # -------------------------
        # TOTAL
        # -------------------------
        if (
            "grand total" in lower_line
            or "amount due" in lower_line
            or "net amount" in lower_line
            or lower_line.startswith("total")
        ):
            total = amount
            total_confidence = 0.95
            continue

        # -------------------------
        # ITEM
        # -------------------------
        item = parse_item_line(line)

        if item:
            items.append(item)

    # ---------------------------------
    # AUTOMATIC SUBTOTAL CALCULATION
    # ---------------------------------
    items_total = round(
        sum(item.total_price for item in items),
        2,
    )

    if subtotal == 0.0 and items_total > 0:
        subtotal = items_total
        subtotal_confidence = 0.90

    # ---------------------------------
    # OVERALL CONFIDENCE
    # ---------------------------------
    confidence_values = [
        item.confidence
        for item in items
    ]

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
        value
        for value in confidence_values
        if value > 0
    ]

    overall_confidence = (
        sum(non_zero_confidences)
        / len(non_zero_confidences)
        if non_zero_confidences
        else 0.0
    )

    return Bill(
        items=items,
        subtotal=round(subtotal, 2),
        tax=round(tax, 2),
        service_charge=round(service_charge, 2),
        discount=round(discount, 2),
        total=round(total, 2),
        subtotal_confidence=subtotal_confidence,
        tax_confidence=tax_confidence,
        service_charge_confidence=service_charge_confidence,
        discount_confidence=discount_confidence,
        total_confidence=total_confidence,
        confidence=round(overall_confidence, 2),
    )