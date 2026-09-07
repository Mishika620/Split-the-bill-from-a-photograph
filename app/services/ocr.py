import cv2
import pytesseract

from app.services.image_processing import preprocess_image


def extract_text(image_path: str) -> str:
    """Extract text from a bill photograph using multiple OCR modes."""

    processed_image = preprocess_image(
        image_path
    )

    # Try the most suitable receipt layouts.
    configs = [
        "--psm 6",
        "--psm 4",
        "--psm 11",
    ]

    results = []

    for config in configs:

        text = pytesseract.image_to_string(
            processed_image,
            config=config,
        )

        if text.strip():
            results.append(text.strip())

    # PSM 6 is generally the best starting point
    # for a structured receipt, so return it first.
    if results:
        return results[0]

    return ""