from app.models.bill import Bill, BillItem
from app.services.validator import validate_bill


def test_valid_bill():
    bill = Bill(
        items=[
            BillItem(
                name="Pizza",
                quantity=1,
                unit_price=450,
                total_price=450,
            ),
            BillItem(
                name="Coke",
                quantity=2,
                unit_price=60,
                total_price=120,
            ),
        ],
        subtotal=570,
        tax=57,
        service_charge=23,
        discount=0,
        total=650,
    )

    result = validate_bill(bill)

    assert result.valid is True
    assert result.items_total == 570
    assert result.expected_total == 650
    assert result.total_difference == 0
    assert result.errors == []


def test_wrong_printed_total():
    bill = Bill(
        items=[
            BillItem(
                name="Pizza",
                quantity=1,
                unit_price=450,
                total_price=450,
            ),
            BillItem(
                name="Coke",
                quantity=2,
                unit_price=60,
                total_price=120,
            ),
        ],
        subtotal=570,
        tax=57,
        service_charge=23,
        discount=0,
        total=700,
    )

    result = validate_bill(bill)

    assert result.valid is False
    assert result.items_total == 570
    assert result.expected_total == 650
    assert result.printed_total == 700
    assert result.total_difference == -50
    assert len(result.errors) > 0