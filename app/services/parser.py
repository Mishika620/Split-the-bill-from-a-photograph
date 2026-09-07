import re

from app.models.bill import Bill, BillItem


SUMMARY_KEYWORDS = (
    "subtotal",
    "sub total",
    "discount",
    "cgst",
    "sgst",
    "tax",
    "service charge",
    "total",
)


def _clean_price(value: str) -> float:
    """Convert OCR price text into a float."""

    value = (
        value
        .replace(",", "")
        .replace("₹", "")
        .strip()
    )

    return float(value)


def _extract_prices(
    text: str,
) -> list[float]:
    """Extract monetary values from a line."""

    matches = re.findall(
        r"\b\d{1,6}(?:,\d{3})*(?:\.\d{2})\b",
        text,
    )

    return [
        _clean_price(value)
        for value in matches
    ]


def _is_summary_line(
    line: str,
) -> bool:
    """Check whether a line belongs to the bill summary."""

    lower_line = line.lower()

    return any(
        keyword in lower_line
        for keyword in SUMMARY_KEYWORDS
    )


def _parse_item_line(
    line: str,
) -> BillItem | None:
    """
    Parse an item line containing:

        Item Name    Quantity    Price

    Example:

        Margherita Pizza 1 299.00
        Coke 2 120.00
    """

    if _is_summary_line(line):
        return None

    ignored_keywords = (
        "item",
        "qty",
        "price",
        "bill no",
        "table no",
        "server",
        "date",
        "time",
        "gstin",
        "thank you",
        "scan for",
    )

    lower_line = line.lower()

    if any(
        keyword in lower_line
        for keyword in ignored_keywords
    ):
        return None

    price_matches = list(
        re.finditer(
            r"\b\d{1,6}(?:,\d{3})*(?:\.\d{2})\b",
            line,
        )
    )

    if not price_matches:
        return None

    price_match = price_matches[-1]

    try:
        total_price = _clean_price(
            price_match.group()
        )
    except ValueError:
        return None

    before_price = line[
        :price_match.start()
    ].strip()

    quantity_matches = list(
        re.finditer(
            r"(?:^|\s)(\d+(?:\.\d+)?)\s*"
            r"(?:[^\d\s]\s*)?$",
            before_price,
        )
    )

    if not quantity_matches:

        quantity_matches = list(
            re.finditer(
                r"\b(\d+(?:\.\d+)?)\b",
                before_price,
            )
        )

    if not quantity_matches:
        return None

    quantity_match = quantity_matches[-1]

    try:
        quantity = float(
            quantity_match.group(1)
        )
    except ValueError:
        return None

    if quantity <= 0:
        return None

    item_name = before_price[
        :quantity_match.start()
    ].strip()

    item_name = re.sub(
        r"[\s=_%|]+$",
        "",
        item_name,
    )

    item_name = item_name.strip()

    if not item_name:
        return None

    if len(item_name) < 2:
        return None

    unit_price = round(
        total_price / quantity,
        2,
    )

    return BillItem(
        name=item_name,
        quantity=quantity,
        unit_price=unit_price,
        total_price=round(
            total_price,
            2,
        ),
        assigned_to=[],
        name_confidence=0.90,
        quantity_confidence=0.95,
        price_confidence=0.95,
        confidence=0.93,
    )


def _find_summary_value(
    lines: list[str],
    keywords: tuple[str, ...],
) -> tuple[float, float]:
    """
    Find a monetary value associated with summary keywords.

    Returns:
        (value, confidence)
    """

    for line in lines:

        lower_line = line.lower()

        if not any(
            keyword in lower_line
            for keyword in keywords
        ):
            continue

        prices = _extract_prices(
            line
        )

        if prices:
            return (
                prices[-1],
                0.95,
            )

    return (
        0.0,
        0.0,
    )


def parse_bill_text(
    text: str,
) -> Bill:
    """
    Convert OCR text into a structured Bill.

    Supports both:
    - generic Tax lines
    - separate CGST and SGST lines

    The parser does not depend on a specific
    restaurant or fixed item names.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    items: list[BillItem] = []

    for line in lines:

        item = _parse_item_line(
            line
        )

        if item is not None:
            items.append(item)

    subtotal, subtotal_confidence = (
        _find_summary_value(
            lines,
            (
                "subtotal",
                "sub total",
            ),
        )
    )

    discount, discount_confidence = (
        _find_summary_value(
            lines,
            (
                "discount",
            ),
        )
    )

    service_charge, service_confidence = (
        _find_summary_value(
            lines,
            (
                "service charge",
            ),
        )
    )

    # First look for explicit CGST and SGST.
    cgst, cgst_confidence = (
        _find_summary_value(
            lines,
            (
                "cgst",
            ),
        )
    )

    sgst, sgst_confidence = (
        _find_summary_value(
            lines,
            (
                "sgst",
            ),
        )
    )

    # If CGST/SGST are present, combine them.
    if cgst_confidence or sgst_confidence:

        tax = round(
            cgst + sgst,
            2,
        )

        if (
            cgst_confidence
            and sgst_confidence
        ):
            tax_confidence = min(
                cgst_confidence,
                sgst_confidence,
            )
        elif cgst_confidence:
            tax_confidence = cgst_confidence
        else:
            tax_confidence = sgst_confidence

    else:

        # Otherwise support a generic Tax line.
        tax, tax_confidence = (
            _find_summary_value(
                lines,
                (
                    "tax",
                ),
            )
        )

    total = 0.0
    total_confidence = 0.0

    for line in reversed(lines):

        lower_line = line.lower()

        if (
            "total" not in lower_line
            or "subtotal" in lower_line
            or "sub total" in lower_line
        ):
            continue

        prices = _extract_prices(
            line
        )

        if prices:
            total = prices[-1]
            total_confidence = 0.95
            break

    # If subtotal is not printed, derive it
    # from the extracted item totals.
    if subtotal == 0.0 and items:

        subtotal = round(
            sum(
                item.total_price
                for item in items
            ),
            2,
        )

        subtotal_confidence = 0.70

    confidence_values = [
        item.confidence
        for item in items
    ]

    confidence_values.extend(
        [
            subtotal_confidence,
            tax_confidence,
            service_confidence,
            discount_confidence,
            total_confidence,
        ]
    )

    non_zero_confidences = [
        value
        for value in confidence_values
        if value > 0
    ]

    if non_zero_confidences:

        overall_confidence = round(
            sum(
                non_zero_confidences
            )
            / len(
                non_zero_confidences
            ),
            2,
        )

    else:

        overall_confidence = 0.0

    return Bill(
        items=items,
        subtotal=round(
            subtotal,
            2,
        ),
        tax=round(
            tax,
            2,
        ),
        service_charge=round(
            service_charge,
            2,
        ),
        discount=round(
            discount,
            2,
        ),
        total=round(
            total,
            2,
        ),
        subtotal_confidence=subtotal_confidence,
        tax_confidence=tax_confidence,
        service_charge_confidence=service_confidence,
        discount_confidence=discount_confidence,
        total_confidence=total_confidence,
        confidence=overall_confidence,
    )