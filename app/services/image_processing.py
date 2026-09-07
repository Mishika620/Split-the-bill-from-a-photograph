import cv2
import numpy as np


def preprocess_image(image_path: str) -> np.ndarray:
    """Preprocess a bill photograph before OCR."""

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    # Resize very large photographs
    height, width = image.shape[:2]

    max_width = 1800

    if width > max_width:
        scale = max_width / width

        image = cv2.resize(
            image,
            (
                int(width * scale),
                int(height * scale),
            ),
            interpolation=cv2.INTER_AREA,
        )

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Reduce noise
    denoised = cv2.GaussianBlur(
        gray,
        (3, 3),
        0,
    )

    # Improve contrast
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    enhanced = clahe.apply(denoised)

    # Convert to black and white
    threshold = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    return threshold