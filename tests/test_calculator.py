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


def test_three_people_shared_item():

    bill = Bill(
        items=[
            BillItem(
                name="Large Pizza",
                quantity=1,
                unit_price=900,
                total_price=900,
                assigned_to=[
                    "you",
                    "alex",
                    "sam",
                ],
            )
        ],
        subtotal=900,
        tax=90,
        service_charge=45,
        discount=0,
        total=1035,
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
        {
            "id": "sam",
            "name": "Sam",
        },
    ]

    result = calculate_split(
        bill,
        people,
    )

    assert len(result) == 3

    assert result[0].item_total == 300
    assert result[1].item_total == 300
    assert result[2].item_total == 300

    assert result[0].tax == 30
    assert result[1].tax == 30
    assert result[2].tax == 30

    assert result[0].service_charge == 15
    assert result[1].service_charge == 15
    assert result[2].service_charge == 15

    assert sum(
        result_item.final_total
        for result_item in result
    ) == 1035


def test_multiple_shared_items():

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
                name="Pasta",
                quantity=1,
                unit_price=400,
                total_price=400,
                assigned_to=[
                    "alex",
                    "sam",
                ],
            ),
            BillItem(
                name="Coke",
                quantity=2,
                unit_price=100,
                total_price=200,
                assigned_to=[
                    "you",
                ],
            ),
        ],
        subtotal=1200,
        tax=120,
        service_charge=60,
        discount=0,
        total=1380,
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
        {
            "id": "sam",
            "name": "Sam",
        },
    ]

    result = calculate_split(
        bill,
        people,
    )

    you = result[0]
    alex = result[1]
    sam = result[2]

    assert you.item_total == 500
    assert alex.item_total == 500
    assert sam.item_total == 200

    assert you.tax == 50
    assert alex.tax == 50
    assert sam.tax == 20

    assert you.service_charge == 25
    assert alex.service_charge == 25
    assert sam.service_charge == 10

    assert sum(
        item.final_total
        for item in result
    ) == 1380


def test_discount_is_distributed_proportionally():

    bill = Bill(
        items=[
            BillItem(
                name="Pizza",
                quantity=1,
                unit_price=600,
                total_price=600,
                assigned_to=[
                    "you",
                ],
            ),
            BillItem(
                name="Pasta",
                quantity=1,
                unit_price=400,
                total_price=400,
                assigned_to=[
                    "alex",
                ],
            ),
        ],
        subtotal=1000,
        tax=100,
        service_charge=50,
        discount=100,
        total=1050,
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

    assert you.item_total == 600
    assert alex.item_total == 400

    assert you.tax == 60
    assert alex.tax == 40

    assert you.service_charge == 30
    assert alex.service_charge == 20

    assert you.discount == 60
    assert alex.discount == 40

    assert you.final_total == 630
    assert alex.final_total == 420

    assert sum(
        item.final_total
        for item in result
    ) == 1050


def test_rounding_correction_keeps_exact_total():

    bill = Bill(
        items=[
            BillItem(
                name="Pizza",
                quantity=1,
                unit_price=100,
                total_price=100,
                assigned_to=[
                    "you",
                ],
            ),
            BillItem(
                name="Pasta",
                quantity=1,
                unit_price=100,
                total_price=100,
                assigned_to=[
                    "alex",
                ],
            ),
            BillItem(
                name="Coke",
                quantity=1,
                unit_price=100,
                total_price=100,
                assigned_to=[
                    "sam",
                ],
            ),
        ],
        subtotal=300,
        tax=100,
        service_charge=50,
        discount=10,
        total=440,
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
        {
            "id": "sam",
            "name": "Sam",
        },
    ]

    result = calculate_split(
        bill,
        people,
    )

    assert sum(
        item.item_total
        for item in result
    ) == 300

    assert sum(
        item.tax
        for item in result
    ) == 100

    assert sum(
        item.service_charge
        for item in result
    ) == 50

    assert sum(
        item.discount
        for item in result
    ) == 10

    assert sum(
        item.final_total
        for item in result
    ) == 440


def test_empty_people_returns_empty_result():

    bill = Bill(
        items=[
            BillItem(
                name="Pizza",
                quantity=1,
                unit_price=500,
                total_price=500,
                assigned_to=[
                    "you",
                ],
            )
        ],
        subtotal=500,
        tax=50,
        service_charge=0,
        discount=0,
        total=550,
    )

    result = calculate_split(
        bill,
        [],
    )

    assert result == []