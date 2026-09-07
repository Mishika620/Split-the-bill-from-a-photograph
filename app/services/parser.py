import re

from app.models.bill import Bill, BillItem


# ---------------------------------------------------------
# MONEY PARSING
# ---------------------------------------------------------

def parse_money(value: str) -> float:
    """Convert a currency-like string into a float."""

    cleaned = (
        value.replace(",", "")
        .replace("₹", "")
        .replace("$", "")
        .replace("€", "")
        .replace("£", "")
        .strip()
    )

    return float(cleaned)


# ---------------------------------------------------------
# CONFIDENCE
# ---------------------------------------------------------

def calculate_confidence(
    name: str,
    quantity: float,
    item_total: float,
) -> tuple[float, float, float, float]:
    """
    Calculate deterministic confidence scores.

    These rules provide an initial confidence estimate.
    Later this can be replaced with OCR-model confidence.
    """

    name_confidence = 0.90 if name.strip() else 0.0

    quantity_confidence = (
        0.95
        if quantity > 0
        else 0.0
    )

    price_confidence = (
        0.95
        if item_total >= 0
        else 0.0
    )

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


# ---------------------------------------------------------
# MONEY EXTRACTION
# ---------------------------------------------------------

def extract_money_values(line: str) -> list[float]:
    """
    Extract currency/decimal values from an OCR line.

    Supports examples such as:
        ₹450
        ₹1,250
        $12.50
        1250.00
        450
    """

    money_pattern = (
        r"(?:₹|\$|€|£)?\s*"
        r"\d+(?:,\d{3})*"
        r"(?:\.\d{1,2})?"
    )

    matches = re.findall(
        money_pattern,
        line,
    )

    values = []

    for match in matches:
        try:
            values.append(
                parse_money(match)
            )
        except ValueError:
            continue

    return values


# ---------------------------------------------------------
# NORMALIZE OCR TEXT
# ---------------------------------------------------------

def normalize_line(line: str) -> str:
    """Normalize common OCR formatting issues."""

    line = line.strip()

    # Convert repeated whitespace to one space.
    line = re.sub(
        r"\s+",
        " ",
        line,
    )

    return line


# ---------------------------------------------------------
# SUMMARY FIELD DETECTION
# ---------------------------------------------------------

def detect_summary_field(
    line: str,
) -> str | None:
    """
    Identify whether an OCR line represents
    subtotal, tax, service charge, discount or total.
    """

    normalized = line.lower()

    # Remove punctuation that OCR may introduce.
    normalized = re.sub(
        r"[^a-z0-9\s]",
        " ",
        normalized,
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    ).strip()

    if "service charge" in normalized:
        return "service_charge"

    if "service tax" in normalized:
        return "tax"

    if "cgst" in normalized:
        return "tax"

    if "sgst" in normalized:
        return "tax"

    if "gst" in normalized:
        return "tax"

    if "tax" in normalized:
        return "tax"

    if "subtotal" in normalized:
        return "subtotal"

    if "sub total" in normalized:
        return "subtotal"

    if "discount" in normalized:
        return "discount"

    # Total should be checked after the more specific
    # fields above.
    if re.search(
        r"\bgrand total\b",
        normalized,
    ):
        return "total"

    if re.search(
        r"\btotal\b",
        normalized,
    ):
        return "total"

    return None


# ---------------------------------------------------------
# ITEM PARSING
# ---------------------------------------------------------

def parse_item_line(
    line: str,
) -> BillItem | None:
    """
    Parse an item line.

    Expected common formats:

        Pizza 2 450
        Pizza 1 ₹450
        Garlic Bread 2 300.00

    The final numeric value is treated as the
    item's total price.
    """

    # First try:
    # name + quantity + price
    item_match = re.match(
        r"(.+?)\s+"
        r"(\d+(?:\.\d+)?)\s+"
        r"(?:₹|\$|€|£)?\s*"
        r"(\d+(?:,\d{3})*(?:\.\d{1,2})?)"
        r"\s*$",
        line,
    )

    if not item_match:
        return None

    name = item_match.group(1).strip()

    try:
        quantity = float(
            item_match.group(2)
        )

        item_total = parse_money(
            item_match.group(3)
        )

    except ValueError:
        return None

    if not name:
        return None

    if quantity <= 0:
        return None

    if item_total < 0:
        return None

    unit_price = (
        item_total / quantity
    )

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
        unit_price=unit_price,
        total_price=item_total,
        assigned_to=[],
        name_confidence=name_confidence,
        quantity_confidence=quantity_confidence,
        price_confidence=price_confidence,
        confidence=item_confidence,
    )


# ---------------------------------------------------------
# BILL PARSER
# ---------------------------------------------------------

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

        line = normalize_line(
            raw_line
        )

        if not line:
            continue

        # ---------------------------------------------
        # Check summary fields first.
        # ---------------------------------------------

        summary_field = detect_summary_field(
            line
        )

        if summary_field:

            money_values = extract_money_values(
                line
            )

            if not money_values:
                continue

            amount = money_values[-1]

            if summary_field == "subtotal":
                subtotal = amount
                subtotal_confidence = 0.95

            elif summary_field == "tax":
                tax += amount

                # Cap confidence at 1.0.
                tax_confidence = min(
                    1.0,
                    tax_confidence + 0.90,
                )

            elif summary_field == "service_charge":
                service_charge = amount
                service_charge_confidence = 0.95

            elif summary_field == "discount":
                discount = amount
                discount_confidence = 0.95

            elif summary_field == "total":
                total = amount
                total_confidence = 0.95

            continue

        # ---------------------------------------------
        # Try parsing the line as an item.
        # ---------------------------------------------

        item = parse_item_line(
            line
        )

        if item:
            items.append(item)

    # -------------------------------------------------
    # If subtotal was not explicitly detected,
    # calculate it from extracted items.
    # -------------------------------------------------

    if (
        subtotal == 0.0
        and items
    ):
        subtotal = round(
            sum(
                item.total_price
                for item in items
            ),
            2,
        )

        subtotal_confidence = 0.70

    # -------------------------------------------------
    # If total was not explicitly detected,
    # calculate an estimated total.
    # -------------------------------------------------

    if (
        total == 0.0
        and (
            subtotal > 0
            or tax > 0
            or service_charge > 0
            or discount > 0
        )
    ):
        total = round(
            subtotal
            + tax
            + service_charge
            - discount,
            2,
        )

        total_confidence = 0.60

    # -------------------------------------------------
    # Overall confidence
    # -------------------------------------------------

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
        round(
            sum(non_zero_confidences)
            / len(non_zero_confidences),
            2,
        )
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