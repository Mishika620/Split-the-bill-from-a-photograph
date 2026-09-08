import json
import re
from pathlib import Path

from rapidfuzz import fuzz

from app.services.ocr import extract_text
from app.services.parser import parse_bill_text
from app.services.validator import validate_bill


GROUND_TRUTH_DIR = Path(
    "test_data/ground_truth"
)

IMAGE_DIR = Path(
    "test_data/images"
)


IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
)


def clean_text(value) -> str:
    """Normalize text for comparison."""

    if value is None:
        return ""

    text = str(value).lower().strip()

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    return " ".join(
        text.split()
    )


def to_float(value, default=None):
    """Safely convert a value to float."""

    if value is None:
        return default

    if isinstance(value, str):
        value = value.replace(
            ",",
            "",
        )

        value = re.sub(
            r"[^\d.\-]",
            "",
            value,
        )

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def get_bill_id(data, filename):
    """Get bill ID from JSON or filename."""

    return (
        data.get("bill_id")
        or data.get("id")
        or Path(filename).stem
    )


def get_items_container(data):
    """
    Locate the item list.

    Supports multiple invoice JSON formats.
    """

    possible_locations = [
        data.get("items"),
        data.get("order_summary", {}).get(
            "items"
        ),
        data.get("invoice_summary", {}).get(
            "items"
        ),
        data.get("summary", {}).get(
            "items"
        ),
    ]

    for items in possible_locations:

        if isinstance(items, list):
            return items

    return []


def normalize_item(item):
    """Convert different item schemas into one format."""

    if not isinstance(item, dict):
        return None

    name = (
        item.get("name")
        or item.get("description")
        or item.get("item_name")
        or item.get("product_name")
        or ""
    )

    quantity = (
        item.get("quantity")
        if item.get("quantity") is not None
        else item.get("qty")
    )

    unit_price = (
        item.get("unit_price")
        if item.get("unit_price") is not None
        else item.get("unit_amount")
    )

    total_price = (
        item.get("total_price")
        if item.get("total_price") is not None
        else item.get("item_total_amount")
    )

    if total_price is None:
        total_price = item.get(
            "total_amount"
        )

    if total_price is None:
        total_price = item.get(
            "net_amount"
        )

    quantity = to_float(
        quantity
    )

    unit_price = to_float(
        unit_price
    )

    total_price = to_float(
        total_price
    )

    if (
        total_price is None
        and unit_price is not None
        and quantity is not None
    ):
        total_price = round(
            unit_price * quantity,
            2,
        )

    if (
        unit_price is None
        and total_price is not None
        and quantity
    ):
        unit_price = round(
            total_price / quantity,
            2,
        )

    return {
        "name": str(name).strip(),
        "quantity": quantity,
        "unit_price": unit_price,
        "total_price": total_price,
    }


def normalize_ground_truth(
    data,
):
    """
    Normalize the complete ground-truth schema.

    Handles:
    - order_summary
    - invoice_summary
    - summary
    - top-level fields
    """

    items = []

    for raw_item in get_items_container(
        data
    ):
        normalized = normalize_item(
            raw_item
        )

        if normalized:
            items.append(
                normalized
            )

    order_summary = data.get(
        "order_summary"
    )

    if not isinstance(
        order_summary,
        dict,
    ):
        order_summary = {}

    invoice_summary = data.get(
        "invoice_summary"
    )

    if not isinstance(
        invoice_summary,
        dict,
    ):
        invoice_summary = {}

    summary = data.get(
        "summary"
    )

    if not isinstance(
        summary,
        dict,
    ):
        summary = {}

    # -----------------------------
    # Subtotal
    # -----------------------------

    subtotal = None

    for source in (
        order_summary,
        invoice_summary,
        summary,
        data,
    ):

        for key in (
            "products_total",
            "subtotal",
            "sub_total",
            "items_total",
        ):

            if source.get(key) is not None:

                subtotal = to_float(
                    source.get(key)
                )

                if subtotal is not None:
                    break

        if subtotal is not None:
            break

    # -----------------------------
    # Tax
    # -----------------------------

    tax = None

    tax_details = order_summary.get(
        "tax_details",
        {},
    )

    if not isinstance(
        tax_details,
        dict,
    ):
        tax_details = {}

    for source in (
        tax_details,
        invoice_summary,
        summary,
        data,
    ):

        for key in (
            "igst_amount",
            "total_tax_amount",
            "tax",
            "tax_amount",
            "total_tax",
        ):

            if source.get(key) is not None:

                tax = to_float(
                    source.get(key)
                )

                if tax is not None:
                    break

        if tax is not None:
            break

    # -----------------------------
    # CGST + SGST
    # -----------------------------

    if tax is None:

        cgst = to_float(
            data.get("cgst")
        )

        sgst = to_float(
            data.get("sgst")
        )

        if (
            cgst is not None
            or sgst is not None
        ):

            tax = round(
                (cgst or 0)
                + (sgst or 0),
                2,
            )

    # -----------------------------
    # Service charge
    # -----------------------------

    service_charge = None

    for source in (
        order_summary,
        invoice_summary,
        summary,
        data,
    ):

        for key in (
            "service_charge",
            "service_charge_amount",
        ):

            if source.get(key) is not None:

                service_charge = to_float(
                    source.get(key)
                )

                if service_charge is not None:
                    break

        if service_charge is not None:
            break

    # -----------------------------
    # Discount
    # -----------------------------

    discount = None

    for source in (
        order_summary,
        invoice_summary,
        summary,
        data,
    ):

        for key in (
            "discount",
            "discount_amount",
            "total_discount",
        ):

            if source.get(key) is not None:

                discount = to_float(
                    source.get(key)
                )

                if discount is not None:
                    break

        if discount is not None:
            break

    # -----------------------------
    # Printed total
    # -----------------------------

    total = None

    for source in (
        order_summary,
        invoice_summary,
        summary,
        data,
    ):

        for key in (
            "grand_total",
            "total",
            "final_total",
            "amount_paid",
        ):

            if source.get(key) is not None:

                total = to_float(
                    source.get(key)
                )

                if total is not None:
                    break

        if total is not None:
            break

    # -----------------------------
    # Explicit wrong-total flag
    # -----------------------------

    printed_total_is_correct = data.get(
        "printed_total_is_correct"
    )

    return {
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "service_charge": service_charge,
        "discount": discount,
        "total": total,
        "printed_total_is_correct": (
            printed_total_is_correct
        ),
    }


def find_image(bill_id):
    """Find image corresponding to a bill."""

    candidates = []

    for extension in IMAGE_EXTENSIONS:

        candidates.append(
            IMAGE_DIR
            / f"{bill_id}{extension}"
        )

    # Also support JSON filename mapping.
    for candidate in candidates:

        if candidate.exists():
            return candidate

    return None


def match_items(
    predicted_items,
    expected_items,
):
    """
    Fuzzy match predicted OCR items
    against ground-truth items.
    """

    matches = []

    used_expected = set()

    for predicted in predicted_items:

        predicted_name = clean_text(
            predicted.name
        )

        best_index = None
        best_score = 0

        for index, expected in enumerate(
            expected_items
        ):

            if index in used_expected:
                continue

            expected_name = clean_text(
                expected["name"]
            )

            if not expected_name:
                continue

            score = fuzz.token_set_ratio(
                predicted_name,
                expected_name,
            )

            if score > best_score:

                best_score = score
                best_index = index

        if (
            best_index is not None
            and best_score >= 60
        ):

            used_expected.add(
                best_index
            )

            matches.append(
                (
                    predicted,
                    expected_items[
                        best_index
                    ],
                    best_score,
                )
            )

    return matches


def compare_bill(
    bill_id,
    predicted_bill,
    expected,
):
    """Compare OCR/parser output with ground truth."""

    expected_items = expected[
        "items"
    ]

    predicted_items = (
        predicted_bill.items
    )

    matches = match_items(
        predicted_items,
        expected_items,
    )

    matched_count = len(
        matches
    )

    expected_count = len(
        expected_items
    )

    item_detection_accuracy = (
        matched_count / expected_count * 100
        if expected_count
        else 0
    )

    quantity_correct = 0
    price_correct = 0

    for (
        predicted,
        ground_truth,
        score,
    ) in matches:

        expected_quantity = (
            ground_truth[
                "quantity"
            ]
        )

        expected_price = (
            ground_truth[
                "total_price"
            ]
        )

        if (
            expected_quantity is not None
            and abs(
                predicted.quantity
                - expected_quantity
            )
            <= 0.01
        ):
            quantity_correct += 1

        if (
            expected_price is not None
            and abs(
                predicted.total_price
                - expected_price
            )
            <= 0.01
        ):
            price_correct += 1

    quantity_accuracy = (
        quantity_correct
        / matched_count
        * 100
        if matched_count
        else 0
    )

    price_accuracy = (
        price_correct
        / matched_count
        * 100
        if matched_count
        else 0
    )

    print(
        f"Items detected: "
        f"{matched_count}/{expected_count}"
    )

    print(
        f"Item detection accuracy: "
        f"{item_detection_accuracy:.1f}%"
    )

    print(
        f"Quantity accuracy: "
        f"{quantity_accuracy:.1f}%"
    )

    print(
        f"Price accuracy: "
        f"{price_accuracy:.1f}%"
    )

    # -----------------------------
    # Field comparisons
    # -----------------------------

    fields = (
        (
            "Subtotal",
            predicted_bill.subtotal,
            expected["subtotal"],
        ),
        (
            "Tax",
            predicted_bill.tax,
            expected["tax"],
        ),
        (
            "Service charge",
            predicted_bill.service_charge,
            expected["service_charge"],
        ),
        (
            "Discount",
            predicted_bill.discount,
            expected["discount"],
        ),
        (
            "Total",
            predicted_bill.total,
            expected["total"],
        ),
    )

    for (
        field_name,
        predicted_value,
        expected_value,
    ) in fields:

        if expected_value is None:

            print(
                f"{field_name}: "
                f"SKIP (not available in ground truth)"
            )

            continue

        difference = abs(
            predicted_value
            - expected_value
        )

        if difference <= 0.01:

            print(
                f"{field_name}: "
                f"PASS "
                f"(predicted={predicted_value}, "
                f"expected={expected_value})"
            )

        else:

            print(
                f"{field_name}: "
                f"FAIL "
                f"(predicted={predicted_value}, "
                f"expected={expected_value})"
            )

    # -----------------------------
    # Wrong printed total detection
    # -----------------------------

    explicit_flag = expected[
        "printed_total_is_correct"
    ]

    validation = validate_bill(
        predicted_bill
    )

    if explicit_flag is False:

        detected_wrong_total = (
            not validation.valid
            and abs(
                validation.total_difference
            ) > 0.01
        )

        if detected_wrong_total:

            print(
                "Wrong printed total: PASS "
                "(inconsistency detected)"
            )

        else:

            print(
                "Wrong printed total: FAIL "
                "(inconsistency not detected)"
            )

    return {
        "item_detection": (
            item_detection_accuracy
        ),
        "quantity": quantity_accuracy,
        "price": price_accuracy,
    }


def evaluate_bill(
    json_path,
):
    """Evaluate one bill."""

    with open(
        json_path,
        "r",
        encoding="utf-8",
    ) as file:

        ground_truth_raw = json.load(
            file
        )

    bill_id = get_bill_id(
        ground_truth_raw,
        json_path.name,
    )

    image_path = find_image(
        bill_id
    )

    if image_path is None:

        print(
            f"Image not found for {bill_id}"
        )

        return None

    print(
        "\n"
        + "=" * 65
    )

    print(
        f"Bill: {bill_id}"
    )

    print(
        f"Image: {image_path.name}"
    )

    expected = normalize_ground_truth(
        ground_truth_raw
    )

    try:

        extracted_text = extract_text(
            str(image_path)
        )

        predicted_bill = parse_bill_text(
            extracted_text
        )

        return compare_bill(
            bill_id,
            predicted_bill,
            expected,
        )

    except Exception as error:

        print(
            f"ERROR: {error}"
        )

        return None


def main():
    """Evaluate all available ground-truth bills."""

    json_files = sorted(
        GROUND_TRUTH_DIR.glob(
            "*.json"
        )
    )

    if not json_files:

        print(
            "No ground-truth JSON files found."
        )

        return

    results = []

    for json_path in json_files:

        result = evaluate_bill(
            json_path
        )

        if result is not None:

            results.append(
                result
            )

    print(
        "\n"
        + "=" * 65
    )

    print(
        "FINAL EVALUATION SUMMARY"
    )

    print(
        "=" * 65
    )

    print(
        f"Bills evaluated: "
        f"{len(results)}"
    )

    if not results:

        return

    avg_item_detection = (
        sum(
            result[
                "item_detection"
            ]
            for result in results
        )
        / len(results)
    )

    avg_quantity = (
        sum(
            result[
                "quantity"
            ]
            for result in results
        )
        / len(results)
    )

    avg_price = (
        sum(
            result[
                "price"
            ]
            for result in results
        )
        / len(results)
    )

    print(
        f"Average item detection: "
        f"{avg_item_detection:.2f}%"
    )

    print(
        f"Average quantity accuracy: "
        f"{avg_quantity:.2f}%"
    )

    print(
        f"Average price accuracy: "
        f"{avg_price:.2f}%"
    )


if __name__ == "__main__":
    main()