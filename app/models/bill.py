from pydantic import BaseModel, Field


class BillItem(BaseModel):
    name: str
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    total_price: float = Field(ge=0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Bill(BaseModel):
    items: list[BillItem] = Field(default_factory=list)

    subtotal: float = Field(default=0.0, ge=0)
    tax: float = Field(default=0.0, ge=0)
    service_charge: float = Field(default=0.0, ge=0)
    discount: float = Field(default=0.0, ge=0)
    total: float = Field(default=0.0, ge=0)

    confidence: float = Field(default=0.0, ge=0.0, le=1.0)