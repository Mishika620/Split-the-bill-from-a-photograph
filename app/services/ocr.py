import pytesseract

from app.services.image_processing import preprocess_image


def extract_text(image_path: str) -> str:
    """Extract text from a bill photograph."""

    processed_image = preprocess_image(image_path)

    text = pytesseract.image_to_string(
        processed_image,
        config="--psm 6",
    )

    return text.strip()