import pytesseract

from app.services.image_processing import preprocess_image


def extract_text(
    image_path: str,
) -> str:
    """
    Extract text from a bill photograph using Tesseract OCR.

    PSM 6 is used because the bill has a structured,
    block-like layout containing item and price columns.
    """

    processed_image = preprocess_image(
        image_path
    )

    text = pytesseract.image_to_string(
        processed_image,
        config="--psm 6",
    )

    return text.strip()