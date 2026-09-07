import json
from pathlib import Path

from app.services.ocr import extract_text
from app.services.parser import parse_bill_text


BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
GROUND_TRUTH_DIR = BASE_DIR / "ground_truth"


def load_ground_truth(path: Path) -> dict:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


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

        predicted = predicted_by_name.get(name)

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

    expected_count = len(expected_items)

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
    expected: float,
) -> bool:

    return abs(
        predicted - expected
    ) <= 0.01


def evaluate_bill(
    image_path: Path,
    ground_truth_path: Path,
) -> dict:

    ground_truth = load_ground_truth(
        ground_truth_path
    )

    print()
    print("=" * 60)
    print(f"Bill: {ground_truth['bill_id']}")
    print(f"Image: {image_path.name}")
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
        ground_truth["service_charge"],
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

    print(
        f"Subtotal: "
        f"{'PASS' if subtotal_correct else 'FAIL'} "
        f"(predicted={bill.subtotal}, "
        f"expected={ground_truth['subtotal']})"
    )

    print(
        f"Tax: "
        f"{'PASS' if tax_correct else 'FAIL'} "
        f"(predicted={bill.tax}, "
        f"expected={ground_truth['tax']})"
    )

    print(
        f"Service charge: "
        f"{'PASS' if service_charge_correct else 'FAIL'} "
        f"(predicted={bill.service_charge}, "
        f"expected={ground_truth['service_charge']})"
    )

    print(
        f"Discount: "
        f"{'PASS' if discount_correct else 'FAIL'} "
        f"(predicted={bill.discount}, "
        f"expected={ground_truth['discount']})"
    )

    print(
        f"Total: "
        f"{'PASS' if total_correct else 'FAIL'} "
        f"(predicted={bill.total}, "
        f"expected={ground_truth['total']})"
    )

    return {
        "bill_id": ground_truth["bill_id"],
        "item_metrics": item_metrics,
        "subtotal_correct": subtotal_correct,
        "tax_correct": tax_correct,
        "service_charge_correct": service_charge_correct,
        "discount_correct": discount_correct,
        "total_correct": total_correct,
    }


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

        bill_id = ground_truth[
            "bill_id"
        ]

        image_path = (
            IMAGES_DIR
            / f"{bill_id}.jpg"
        )

        if not image_path.exists():

            image_path = (
                IMAGES_DIR
                / f"{bill_id}.png"
            )

        if not image_path.exists():

            print()
            print(
                f"Skipping {bill_id}: "
                "matching image not found."
            )

            continue

        result = evaluate_bill(
            image_path,
            ground_truth_path,
        )

        results.append(
            result
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


if __name__ == "__main__":
    main()