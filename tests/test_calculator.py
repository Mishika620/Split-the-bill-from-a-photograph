from app.models.bill import Bill, BillItem
from app.services.calculator import calculate_split


def test_shared_item_is_split_equally():

    bill = Bill(
        items=[
            BillItem(
                name="Pizza",
                quantity=1,
                unit_price=600,
                total_price=600,
                assigned_to=[
                    "you",
                    "alex",
                ],
            )
        ],
        subtotal=600,
        tax=60,
        service_charge=30,
        discount=0,
        total=690,
    )

    people = [
        {
            "id": "you",
            "name": "You",
        },
        {
            "id": "alex",
            "name": "Alex",
        },
    ]

    result = calculate_split(
        bill,
        people,
    )

    assert len(result) == 2

    assert result[0].item_total == 300
    assert result[1].item_total == 300

    assert result[0].tax == 30
    assert result[1].tax == 30

    assert result[0].service_charge == 15
    assert result[1].service_charge == 15

    assert result[0].final_total == 345
    assert result[1].final_total == 345


def test_consumption_based_split():

    bill = Bill(
        items=[
            BillItem(
                name="Pizza",
                quantity=1,
                unit_price=600,
                total_price=600,
                assigned_to=[
                    "you",
                    "alex",
                ],
            ),
            BillItem(
                name="Coke",
                quantity=1,
                unit_price=120,
                total_price=120,
                assigned_to=[
                    "you",
                ],
            ),
        ],
        subtotal=720,
        tax=72,
        service_charge=36,
        discount=0,
        total=828,
    )

    people = [
        {
            "id": "you",
            "name": "You",
        },
        {
            "id": "alex",
            "name": "Alex",
        },
    ]

    result = calculate_split(
        bill,
        people,
    )

    you = result[0]
    alex = result[1]

    assert you.item_total == 420
    assert alex.item_total == 300

    assert you.tax == 42
    assert alex.tax == 30

    assert you.service_charge == 21
    assert alex.service_charge == 15

    assert you.final_total == 483
    assert alex.final_total == 345


def test_unassigned_item_is_not_charged():

    bill = Bill(
        items=[
            BillItem(
                name="Pizza",
                quantity=1,
                unit_price=500,
                total_price=500,
                assigned_to=[],
            )
        ],
        subtotal=500,
        tax=50,
        service_charge=0,
        discount=0,
        total=550,
    )

    people = [
        {
            "id": "you",
            "name": "You",
        },
        {
            "id": "alex",
            "name": "Alex",
        },
    ]

    result = calculate_split(
        bill,
        people,
    )

    assert result[0].item_total == 0
    assert result[1].item_total == 0