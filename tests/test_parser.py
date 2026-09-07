from app.services.parser import parse_bill_text


def test_parse_bill_text():
    text = """
    PIZZA HUT
    Margherita Pizza 2 450.00
    Garlic Bread 1 180.00
    Coke 2 120.00

    Subtotal 750.00
    Tax 75.00
    Service Charge 30.00
    Total 855.00
    """

    bill = parse_bill_text(text)

    assert len(bill.items) == 3

    assert bill.items[0].name == "Margherita Pizza"
    assert bill.items[0].quantity == 2
    assert bill.items[0].total_price == 450.0

    assert bill.subtotal == 750.0
    assert bill.tax == 75.0
    assert bill.service_charge == 30.0
    assert bill.total == 855.0