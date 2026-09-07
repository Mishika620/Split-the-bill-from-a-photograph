from pathlib import Path
import tempfile

from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel

from app.models.bill import Bill
from app.services.ocr import extract_text
from app.services.parser import parse_bill_text
from app.services.validator import validate_bill
from app.services.calculator import calculate_split


router = APIRouter()


class ReviewResponse(BaseModel):
    bill: Bill
    validation: dict


class SplitRequest(BaseModel):
    bill: Bill
    people: list[dict]


class SplitResponse(BaseModel):
    results: list[dict]
    total: float


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


@router.post(
    "/split",
    response_model=SplitResponse,
)
def split_bill(request: SplitRequest):
    """
    Calculate each person's share of the bill
    according to actual item consumption.
    """

    if not request.people:
        raise HTTPException(
            status_code=400,
            detail="At least one person is required.",
        )

    # Make sure every bill item has an assignment.
    unassigned_items = [
        item.name
        for item in request.bill.items
        if not item.assigned_to
    ]

    if unassigned_items:
        raise HTTPException(
            status_code=400,
            detail=(
                "The following items are not assigned: "
                + ", ".join(unassigned_items)
            ),
        )

    results = calculate_split(
        request.bill,
        request.people,
    )

    result_data = [
        {
            "person_id": result.person_id,
            "person_name": result.person_name,
            "item_total": result.item_total,
            "tax": result.tax,
            "service_charge": result.service_charge,
            "discount": result.discount,
            "final_total": result.final_total,
        }
        for result in results
    ]

    total = round(
        sum(
            result["final_total"]
            for result in result_data
        ),
        2,
    )

    return SplitResponse(
        results=result_data,
        total=total,
    )