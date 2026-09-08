import re

from rapidfuzz import fuzz

from app.models.bill import Bill, BillItem


SUMMARY_KEYWORDS = (
    "subtotal",
    "sub total",
    "discount",
    "cgst",
    "sgst",
    "gst",
    "tax",
    "service charge",
    "total",
    "amount due",
    "grand total",
)


SUMMARY_OCR_ALIASES = (
    "tou",
    "totat",
    "totat",
    "motsl",
    "motai",
    "tota",
)


IGNORED_KEYWORDS = (
    "item",
    "qty",
    "quantity",
    "price",
    "amount",
    "bill no",
    "table no",
    "server",
    "date",
    "time",
    "gstin",
    "thank you",
    "visit again",
    "please check",
    "wrong total",
    "invoice",
    "cashier",
    "payment",
)


def _clean_price(value: str) -> float:
    """Convert OCR price text into a float."""

    value = (
        value
        .replace(",", "")
        .replace("₹", "")
        .replace("$", "")
        .replace("€", "")
        .replace("£", "")
        .replace("¥", "")
        .strip()
    )

    return float(value)


def _extract_prices(
    text: str,
) -> list[float]:
    """
    Extract monetary values from OCR text.

    Supports common OCR currency noise such as:
    ₹599.00
    $99.00
    1,398.00
    """

    matches = re.findall(
        r"(?:₹|\$|€|£|¥)?\s*"
        r"\d{1,6}(?:,\d{3})*"
        r"(?:\.\d{1,2})?",
        text,
    )

    values = []

    for value in matches:

        try:
            values.append(
                _clean_price(value)
            )

        except ValueError:
            continue

    return values


def _normalise_ocr_text(
    text: str,
) -> str:
    """Normalize common OCR spacing and punctuation."""

    text = text.replace(
        "|",
        " ",
    )

    text = text.replace(
        ",",
        " ",
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def _looks_like_summary(
    line: str,
) -> bool:
    """Detect normal and noisy OCR summary lines."""

    lower_line = line.lower()

    if any(
        keyword in lower_line
        for keyword in SUMMARY_KEYWORDS
    ):
        return True

    words = re.findall(
        r"[a-z]+",
        lower_line,
    )

    for word in words:

        if len(word) < 3:
            continue

        for alias in SUMMARY_OCR_ALIASES:

            score = fuzz.ratio(
                word,
                alias,
            )

            if score >= 80:
                return True

    return False


def _extract_quantity(
    before_price: str,
):
    """
    Extract quantity from the part before the price.

    Handles examples such as:
        Pizza 1
        Pizza 2
        Pizza v
        Pizza 1 PC
    """

    before_price = before_price.strip()

    matches = list(
        re.finditer(
            r"(?:^|\s)"
            r"(\d+(?:\.\d+)?)"
            r"(?:\s*(?:pc|pcs|x|nos?))?"
            r"\s*$",
            before_price,
            re.IGNORECASE,
        )
    )

    if matches:

        match = matches[-1]

        try:
            return (
                float(match.group(1)),
                match.start(1),
            )
        except ValueError:
            pass

    # OCR sometimes changes "1" into "l" or "I".
    ocr_quantity_matches = list(
        re.finditer(
            r"(?:^|\s)"
            r"([lIi])"
            r"\s*$",
            before_price,
        )
    )

    if ocr_quantity_matches:

        match = ocr_quantity_matches[-1]

        return (
            1.0,
            match.start(1),
        )

    # Generic fallback.
    matches = list(
        re.finditer(
            r"\b(\d+(?:\.\d+)?)\b",
            before_price,
        )
    )

    if matches:

        match = matches[-1]

        try:
            return (
                float(match.group(1)),
                match.start(1),
            )
        except ValueError:
            pass

    return None, None


def _clean_item_name(
    value: str,
) -> str:
    """Clean OCR noise from an extracted item name."""

    value = re.sub(
        r"^[\s\-_=|:;,.]+",
        "",
        value,
    )

    value = re.sub(
        r"[\s\-_=|:;,.]+$",
        "",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def _parse_item_line(
    line: str,
) -> BillItem | None:
    """
    Parse an OCR item row.

    Expected general structure:

        Item Name    Quantity    Amount

    The parser deliberately does not depend
    on specific restaurant or product names.
    """

    line = _normalise_ocr_text(
        line
    )

    if not line:
        return None

    lower_line = line.lower()

    if _looks_like_summary(line):
        return None

    if any(
        keyword in lower_line
        for keyword in IGNORED_KEYWORDS
    ):
        return None

    price_matches = list(
        re.finditer(
            r"(?:₹|\$|€|£|¥)?\s*"
            r"\d{1,6}(?:,\d{3})*"
            r"(?:\.\d{1,2})?",
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

    if total_price < 0:
        return None

    before_price = line[
        :price_match.start()
    ].strip()

    quantity, quantity_position = (
        _extract_quantity(
            before_price
        )
    )

    if quantity is None:
        return None

    if quantity <= 0:
        return None

    if quantity_position is not None:

        item_name = before_price[
            :quantity_position
        ]

    else:

        item_name = before_price

    item_name = _clean_item_name(
        item_name
    )

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
        name_confidence=0.80,
        quantity_confidence=0.90,
        price_confidence=0.95,
        confidence=0.86,
    )


def _find_summary_value(
    lines: list[str],
    keywords: tuple[str, ...],
) -> tuple[float, float]:
    """
    Find a monetary value associated with summary keywords.
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


def _find_total(
    lines: list[str],
) -> tuple[float, float]:
    """
    Find the printed total.

    Searches from bottom to top because totals
    normally appear near the end of a receipt.
    """

    for line in reversed(lines):

        lower_line = line.lower()

        if (
            "subtotal" in lower_line
            or "sub total" in lower_line
        ):
            continue

        is_total = (
            "total" in lower_line
            or "amount due" in lower_line
            or "grand total" in lower_line
        )

        if not is_total:

            words = re.findall(
                r"[a-z]+",
                lower_line,
            )

            if not any(
                fuzz.ratio(
                    word,
                    "total",
                )
                >= 80
                for word in words
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


def _find_gst_or_tax(
    lines: list[str],
) -> tuple[float, float]:
    """
    Extract GST/tax amount.

    Handles examples:

        GST (18%) 251.64
        Tax 29.95
        CGST 9.43
        SGST 9.43
    """

    cgst, cgst_confidence = (
        _find_summary_value(
            lines,
            ("cgst",),
        )
    )

    sgst, sgst_confidence = (
        _find_summary_value(
            lines,
            ("sgst",),
        )
    )

    if (
        cgst_confidence
        or sgst_confidence
    ):

        tax = round(
            cgst + sgst,
            2,
        )

        confidence_values = [
            value
            for value in (
                cgst_confidence,
                sgst_confidence,
            )
            if value > 0
        ]

        return (
            tax,
            min(
                confidence_values
            ),
        )

    return _find_summary_value(
        lines,
        (
            "gst",
            "tax",
        ),
    )


def parse_bill_text(
    text: str,
) -> Bill:
    """
    Convert OCR text into a structured Bill.
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

    tax, tax_confidence = (
        _find_gst_or_tax(
            lines
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

    discount, discount_confidence = (
        _find_summary_value(
            lines,
            (
                "discount",
            ),
        )
    )

    total, total_confidence = _find_total(
        lines
    )

    # If OCR missed subtotal but item rows
    # were successfully extracted, use their sum.
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
        subtotal_confidence=(
            subtotal_confidence
        ),
        tax_confidence=(
            tax_confidence
        ),
        service_charge_confidence=(
            service_confidence
        ),
        discount_confidence=(
            discount_confidence
        ),
        total_confidence=(
            total_confidence
        ),
        confidence=overall_confidence,
    )