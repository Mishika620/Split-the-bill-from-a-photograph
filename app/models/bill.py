from pydantic import BaseModel, Field


class BillItem(BaseModel):
    name: str

    quantity: float = Field(
        gt=0
    )

    unit_price: float = Field(
        ge=0
    )

    total_price: float = Field(
        ge=0
    )

    # People who consumed this item
    assigned_to: list[str] = Field(
        default_factory=list
    )

    # Per-field confidence scores
    name_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    quantity_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    price_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )


class Bill(BaseModel):
    items: list[BillItem] = Field(
        default_factory=list
    )

    subtotal: float = Field(
        default=0.0,
        ge=0,
    )

    tax: float = Field(
        default=0.0,
        ge=0,
    )

    service_charge: float = Field(
        default=0.0,
        ge=0,
    )

    discount: float = Field(
        default=0.0,
        ge=0,
    )

    total: float = Field(
        default=0.0,
        ge=0,
    )

    # Confidence scores for bill-level fields
    subtotal_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    tax_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    service_charge_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    discount_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    total_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    # Overall bill confidence
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )