import json
from pathlib import Path

from app.services.ocr import extract_text
from app.services.parser import parse_bill_text


BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
GROUND_TRUTH_DIR = BASE_DIR / "ground_truth"


def load_ground_truth(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_bill_id(ground_truth: dict, path: Path) -> str:
    """
    Get bill ID from JSON when available.
    Otherwise derive it from the JSON filename.
    """

    bill_id = ground_truth.get("bill_id")

    if bill_id:
        return str(bill_id)

    return path.stem


def normalize_item(item: dict) -> dict | None:
    """
    Convert different real-world invoice item formats
    into the common evaluation format.

    Supported examples:
    - name + total_price
    - description + item_total_amount
    - description + total_amount
    - description + net_amount
    """

    name = (
        item.get("name")
        or item.get("description")
        or item.get("item_name")
        or item.get("product_name")
    )

    if not name:
        return None

    quantity = item.get("quantity", 1)

    if isinstance(quantity, str):
        quantity_text = quantity.strip()

        try:
            quantity = float(
                quantity_text.split()[0]
            )
        except (ValueError, IndexError):
            quantity = 1.0

    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        quantity = 1.0

    total_price = (
        item.get("total_price")
        if item.get("total_price") is not None
        else item.get("item_total_amount")
    )

    if total_price is None:
        total_price = item.get("total_amount")

    if total_price is None:
        total_price = item.get("net_amount")

    if total_price is None:
        return None

    try:
        total_price = float(total_price)
    except (TypeError, ValueError):
        return None

    unit_price = item.get("unit_price")

    if unit_price is None:
        unit_price = item.get("unit_amount")

    if unit_price is None and quantity:
        unit_price = total_price / quantity

    try:
        unit_price = float(unit_price)
    except (TypeError, ValueError):
        unit_price = total_price

    return {
        "name": str(name).strip(),
        "quantity": quantity,
        "unit_price": unit_price,
        "total_price": total_price,
    }


def normalize_ground_truth(
    ground_truth: dict,
    path: Path,
) -> dict:
    """
    Normalize different bill/invoice JSON structures
    into the schema required by the evaluator.
    """

    bill_id = get_bill_id(
        ground_truth,
        path,
    )

    raw_items = ground_truth.get(
        "items",
        [],
    )

    normalized_items = []

    for item in raw_items:

        normalized_item = normalize_item(
            item
        )

        if normalized_item:
            normalized_items.append(
                normalized_item
            )

    summary = ground_truth.get(
        "invoice_summary",
        {},
    )

    if not isinstance(summary, dict):
        summary = {}

    summary_data = ground_truth.get(
        "summary",
        {},
    )

    if not isinstance(summary_data, dict):
        summary_data = {}

    subtotal = ground_truth.get(
        "subtotal"
    )

    if subtotal is None:
        subtotal = summary.get(
            "subtotal"
        )

    if subtotal is None:
        subtotal = summary_data.get(
            "subtotal"
        )

    if subtotal is None:
        subtotal = ground_truth.get(
            "products_total"
        )

    tax = ground_truth.get(
        "tax"
    )

    if tax is None:
        tax = summary.get(
            "total_tax_amount"
        )

    if tax is None:
        tax = 0.0

    service_charge = ground_truth.get(
        "service_charge",
        0.0,
    )

    discount = ground_truth.get(
        "discount",
        0.0,
    )

    total = ground_truth.get(
        "total"
    )

    if total is None:
        total = summary.get(
            "grand_total"
        )

    if total is None:
        total = summary_data.get(
            "grand_total"
        )

    if total is None:
        total = summary_data.get(
            "total"
        )

    return {
        "bill_id": bill_id,
        "items": normalized_items,
        "subtotal": (
            float(subtotal)
            if subtotal is not None
            else None
        ),
        "tax": float(tax),
        "service_charge": float(
            service_charge
        ),
        "discount": float(
            discount
        ),
        "total": (
            float(total)
            if total is not None
            else None
        ),
        "printed_total_is_correct":
            ground_truth.get(
                "printed_total_is_correct"
            ),
    }


def compare_items(
    predicted_items: list,
    expected_items: list,
) -> dict:

    expected_by_name = {
        item["name"].lower().strip(): item
        for item in expected_items
    }

    predicted_by_name = {
        item.name.lower().strip(): item
        for item in predicted_items
    }

    matched = 0
    quantity_correct = 0
    price_correct = 0

    for name, expected in expected_by_name.items():

        predicted = predicted_by_name.get(
            name
        )

        if predicted is None:
            continue

        matched += 1

        if (
            abs(
                predicted.quantity
                - expected["quantity"]
            )
            <= 0.01
        ):
            quantity_correct += 1

        if (
            abs(
                predicted.total_price
                - expected["total_price"]
            )
            <= 0.01
        ):
            price_correct += 1

    expected_count = len(
        expected_items
    )

    item_detection_accuracy = (
        matched / expected_count
        if expected_count
        else 0.0
    )

    quantity_accuracy = (
        quantity_correct / matched
        if matched
        else 0.0
    )

    price_accuracy = (
        price_correct / matched
        if matched
        else 0.0
    )

    return {
        "expected_items": expected_count,
        "matched_items": matched,
        "item_detection_accuracy": round(
            item_detection_accuracy * 100,
            2,
        ),
        "quantity_accuracy": round(
            quantity_accuracy * 100,
            2,
        ),
        "price_accuracy": round(
            price_accuracy * 100,
            2,
        ),
    }


def compare_field(
    predicted: float,
    expected: float | None,
) -> bool | None:

    if expected is None:
        return None

    return (
        abs(
            predicted - expected
        )
        <= 0.01
    )


def print_field_result(
    label: str,
    predicted: float,
    expected: float | None,
) -> None:

    if expected is None:

        print(
            f"{label}: SKIP "
            f"(not available in ground truth)"
        )

        return

    result = compare_field(
        predicted,
        expected,
    )

    print(
        f"{label}: "
        f"{'PASS' if result else 'FAIL'} "
        f"(predicted={predicted}, "
        f"expected={expected})"
    )


def evaluate_bill(
    image_path: Path,
    ground_truth_path: Path,
) -> dict:

    raw_ground_truth = load_ground_truth(
        ground_truth_path
    )

    ground_truth = normalize_ground_truth(
        raw_ground_truth,
        ground_truth_path,
    )

    print()
    print("=" * 60)
    print(
        f"Bill: {ground_truth['bill_id']}"
    )
    print(
        f"Image: {image_path.name}"
    )
    print("=" * 60)

    text = extract_text(
        str(image_path)
    )

    bill = parse_bill_text(
        text
    )

    item_metrics = compare_items(
        bill.items,
        ground_truth["items"],
    )

    subtotal_correct = compare_field(
        bill.subtotal,
        ground_truth["subtotal"],
    )

    tax_correct = compare_field(
        bill.tax,
        ground_truth["tax"],
    )

    service_charge_correct = compare_field(
        bill.service_charge,
        ground_truth[
            "service_charge"
        ],
    )

    discount_correct = compare_field(
        bill.discount,
        ground_truth["discount"],
    )

    total_correct = compare_field(
        bill.total,
        ground_truth["total"],
    )

    print(
        f"Items detected: "
        f"{item_metrics['matched_items']}/"
        f"{item_metrics['expected_items']}"
    )

    print(
        f"Item detection accuracy: "
        f"{item_metrics['item_detection_accuracy']}%"
    )

    print(
        f"Quantity accuracy: "
        f"{item_metrics['quantity_accuracy']}%"
    )

    print(
        f"Price accuracy: "
        f"{item_metrics['price_accuracy']}%"
    )

    print_field_result(
        "Subtotal",
        bill.subtotal,
        ground_truth["subtotal"],
    )

    print_field_result(
        "Tax",
        bill.tax,
        ground_truth["tax"],
    )

    print_field_result(
        "Service charge",
        bill.service_charge,
        ground_truth[
            "service_charge"
        ],
    )

    print_field_result(
        "Discount",
        bill.discount,
        ground_truth["discount"],
    )

    print_field_result(
        "Total",
        bill.total,
        ground_truth["total"],
    )

    wrong_total_check = None

    if (
        ground_truth[
            "printed_total_is_correct"
        ]
        is False
    ):

        calculated_total = round(
            ground_truth["subtotal"]
            + ground_truth["tax"]
            + ground_truth[
                "service_charge"
            ]
            - ground_truth[
                "discount"
            ],
            2,
        )

        if ground_truth["total"] is not None:

            wrong_total_check = (
                abs(
                    calculated_total
                    - ground_truth["total"]
                )
                > 0.01
            )

            print(
                "Wrong printed total check: "
                f"{'PASS' if wrong_total_check else 'FAIL'} "
                f"(calculated={calculated_total}, "
                f"printed={ground_truth['total']})"
            )

    return {
        "bill_id": ground_truth["bill_id"],
        "item_metrics": item_metrics,
        "subtotal_correct": subtotal_correct,
        "tax_correct": tax_correct,
        "service_charge_correct": (
            service_charge_correct
        ),
        "discount_correct": discount_correct,
        "total_correct": total_correct,
        "wrong_total_check": (
            wrong_total_check
        ),
    }


def find_image(
    bill_id: str,
) -> Path | None:

    extensions = (
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    )

    for extension in extensions:

        image_path = (
            IMAGES_DIR
            / f"{bill_id}{extension}"
        )

        if image_path.exists():
            return image_path

    return None


def main() -> None:

    ground_truth_files = sorted(
        GROUND_TRUTH_DIR.glob(
            "*.json"
        )
    )

    if not ground_truth_files:

        print(
            "No ground-truth files found."
        )

        return

    results = []

    for ground_truth_path in ground_truth_files:

        ground_truth = load_ground_truth(
            ground_truth_path
        )

        bill_id = get_bill_id(
            ground_truth,
            ground_truth_path,
        )

        image_path = find_image(
            bill_id
        )

        if image_path is None:

            print()
            print(
                f"Skipping {bill_id}: "
                "matching image not found."
            )

            continue

        try:

            result = evaluate_bill(
                image_path,
                ground_truth_path,
            )

            results.append(
                result
            )

        except Exception as error:

            print()
            print(
                f"ERROR evaluating "
                f"{bill_id}: {error}"
            )

    if not results:

        print(
            "No bills could be evaluated."
        )

        return

    print()
    print("=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    print(
        f"Bills evaluated: "
        f"{len(results)}"
    )

    average_detection = sum(
        result["item_metrics"][
            "item_detection_accuracy"
        ]
        for result in results
    ) / len(results)

    average_quantity = sum(
        result["item_metrics"][
            "quantity_accuracy"
        ]
        for result in results
    ) / len(results)

    average_price = sum(
        result["item_metrics"][
            "price_accuracy"
        ]
        for result in results
    ) / len(results)

    print(
        f"Average item detection: "
        f"{average_detection:.2f}%"
    )

    print(
        f"Average quantity accuracy: "
        f"{average_quantity:.2f}%"
    )

    print(
        f"Average price accuracy: "
        f"{average_price:.2f}%"
    )

    wrong_total_results = [
        result["wrong_total_check"]
        for result in results
        if result["wrong_total_check"]
        is not None
    ]

    if wrong_total_results:

        passed = sum(
            wrong_total_results
        )

        print(
            f"Wrong-total validation: "
            f"{passed}/"
            f"{len(wrong_total_results)} "
            "passed"
        )


if __name__ == "__main__":
    main()