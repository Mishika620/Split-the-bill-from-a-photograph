from pathlib import Path
import tempfile

from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel

from app.models.bill import Bill
from app.services.ocr import extract_text
from app.services.parser import parse_bill_text
from app.services.validator import validate_bill


router = APIRouter()


class ReviewResponse(BaseModel):
    bill: Bill
    validation: dict


@router.post("/extract")
async def extract_bill(
    file: UploadFile = File(...)
):
    """
    Upload a bill photograph and extract
    structured bill information using OCR.
    """

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/jpg",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPG and PNG images are supported.",
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty.",
        )

    suffix = Path(file.filename or ".jpg").suffix

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as temp_file:

        temp_file.write(file_bytes)

        temp_path = temp_file.name

    try:
        extracted_text = extract_text(temp_path)

        bill = parse_bill_text(extracted_text)

        return {
            "bill": bill,
            "raw_text": extracted_text,
        }

    finally:
        Path(temp_path).unlink(
            missing_ok=True
        )


@router.post(
    "/review",
    response_model=ReviewResponse,
)
def review_bill(bill: Bill):
    """
    Validate a corrected bill before splitting.
    """

    validation_result = validate_bill(bill)

    return ReviewResponse(
        bill=bill,
        validation=validation_result.__dict__,
    )