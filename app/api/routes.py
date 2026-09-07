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


# ---------------------------------------------------------
# EXTRACT BILL
# ---------------------------------------------------------

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
        "image/webp",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only JPG, PNG and WEBP images "
                "are supported."
            ),
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty.",
        )

    suffix = Path(
        file.filename or ".jpg"
    ).suffix

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as temp_file:

        temp_file.write(file_bytes)

        temp_path = temp_file.name

    try:

        extracted_text = extract_text(
            temp_path
        )

        bill = parse_bill_text(
            extracted_text
        )

        return {
            "bill": bill,
            "raw_text": extracted_text,
        }

    finally:

        Path(temp_path).unlink(
            missing_ok=True
        )


# ---------------------------------------------------------
# HUMAN REVIEW / VALIDATION
# ---------------------------------------------------------

@router.post(
    "/review",
    response_model=ReviewResponse,
)
def review_bill(bill: Bill):
    """
    Validate a corrected bill before splitting.
    """

    validation_result = validate_bill(
        bill
    )

    return ReviewResponse(
        bill=bill,
        validation=validation_result.__dict__,
    )


# ---------------------------------------------------------
# SPLIT BILL
# ---------------------------------------------------------

@router.post(
    "/split",
    response_model=SplitResponse,
)
def split_bill(
    request: SplitRequest
):
    """
    Calculate each person's share of the bill.

    The bill must pass arithmetic validation
    before the split calculation is performed.
    """

    # -------------------------------------------------
    # 1. People validation
    # -------------------------------------------------

    if not request.people:

        raise HTTPException(
            status_code=400,
            detail="At least one person is required.",
        )

    # -------------------------------------------------
    # 2. Validate unique person IDs
    # -------------------------------------------------

    person_ids = [
        person.get("id")
        for person in request.people
    ]

    if any(
        not person_id
        for person_id in person_ids
    ):

        raise HTTPException(
            status_code=400,
            detail="Every person must have an ID.",
        )

    if len(person_ids) != len(set(person_ids)):

        raise HTTPException(
            status_code=400,
            detail="Person IDs must be unique.",
        )

    # -------------------------------------------------
    # 3. Make sure every item is assigned
    # -------------------------------------------------

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

    # -------------------------------------------------
    # 4. Validate assignment IDs
    # -------------------------------------------------

    invalid_assignments = []

    valid_person_ids = set(
        person_ids
    )

    for item in request.bill.items:

        for person_id in item.assigned_to:

            if person_id not in valid_person_ids:

                invalid_assignments.append(
                    f"{item.name} → {person_id}"
                )

    if invalid_assignments:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid item assignments: "
                + ", ".join(
                    invalid_assignments
                )
            ),
        )

    # -------------------------------------------------
    # 5. Validate bill arithmetic
    # -------------------------------------------------

    validation_result = validate_bill(
        request.bill
    )

    if not validation_result.valid:

        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "Bill validation failed. "
                    "Please review and correct "
                    "the extracted values before "
                    "splitting."
                ),
                "errors": validation_result.errors,
                "items_total": (
                    validation_result.items_total
                ),
                "printed_subtotal": (
                    validation_result.printed_subtotal
                ),
                "expected_total": (
                    validation_result.expected_total
                ),
                "printed_total": (
                    validation_result.printed_total
                ),
                "subtotal_difference": (
                    validation_result.subtotal_difference
                ),
                "total_difference": (
                    validation_result.total_difference
                ),
            },
        )

    # -------------------------------------------------
    # 6. Calculate consumption-based split
    # -------------------------------------------------

    results = calculate_split(
        request.bill,
        request.people,
    )

    # -------------------------------------------------
    # 7. Convert results into API response
    # -------------------------------------------------

    result_data = [
        {
            "person_id": result.person_id,
            "person_name": result.person_name,
            "item_total": result.item_total,
            "tax": result.tax,
            "service_charge": (
                result.service_charge
            ),
            "discount": result.discount,
            "final_total": result.final_total,
        }
        for result in results
    ]

    # -------------------------------------------------
    # 8. Calculate final bill total
    # -------------------------------------------------

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