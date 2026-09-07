import cv2
import numpy as np


def preprocess_image(
    image_path: str,
) -> np.ndarray:
    """
    Preprocess a bill photograph for OCR.

    The receipt used by the project has clear printed
    text, so Otsu thresholding is preferred over
    aggressive adaptive thresholding.
    """

    image = cv2.imread(
        image_path
    )

    if image is None:
        raise ValueError(
            f"Could not read image: {image_path}"
        )

    height, width = image.shape[:2]

    max_width = 2000

    if width > max_width:

        scale = (
            max_width / width
        )

        image = cv2.resize(
            image,
            (
                int(width * scale),
                int(height * scale),
            ),
            interpolation=cv2.INTER_AREA,
        )

    # Convert the receipt to grayscale.
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    # Slight denoising while preserving printed text.
    denoised = cv2.GaussianBlur(
        gray,
        (3, 3),
        0,
    )

    # Improve local contrast.
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    enhanced = clahe.apply(
        denoised
    )

    # Otsu thresholding works well for
    # clean printed receipts.
    _, threshold = cv2.threshold(
        enhanced,
        0,
        255,
        cv2.THRESH_BINARY
        + cv2.THRESH_OTSU,
    )

    return threshold