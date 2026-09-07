from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_split_bill_api():

    payload = {
        "bill": {
            "items": [
                {
                    "name": "Pizza",
                    "quantity": 1,
                    "unit_price": 600,
                    "total_price": 600,
                    "assigned_to": ["you", "alex"],
                },
                {
                    "name": "Coke",
                    "quantity": 1,
                    "unit_price": 120,
                    "total_price": 120,
                    "assigned_to": ["you"],
                },
            ],
            "subtotal": 720,
            "tax": 72,
            "service_charge": 36,
            "discount": 0,
            "total": 828,
        },
        "people": [
            {
                "id": "you",
                "name": "You",
            },
            {
                "id": "alex",
                "name": "Alex",
            },
        ],
    }

    response = client.post(
        "/split",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["results"]) == 2

    assert data["results"][0]["person_name"] == "You"
    assert data["results"][1]["person_name"] == "Alex"

    assert data["results"][0]["item_total"] == 420
    assert data["results"][1]["item_total"] == 300

    assert data["results"][0]["tax"] == 42
    assert data["results"][1]["tax"] == 30

    assert data["results"][0]["service_charge"] == 21
    assert data["results"][1]["service_charge"] == 15

    assert data["results"][0]["final_total"] == 483
    assert data["results"][1]["final_total"] == 345

    assert data["total"] == 828


def test_split_bill_rejects_unassigned_item():

    payload = {
        "bill": {
            "items": [
                {
                    "name": "Pizza",
                    "quantity": 1,
                    "unit_price": 500,
                    "total_price": 500,
                    "assigned_to": [],
                }
            ],
            "subtotal": 500,
            "tax": 50,
            "service_charge": 0,
            "discount": 0,
            "total": 550,
        },
        "people": [
            {
                "id": "you",
                "name": "You",
            },
            {
                "id": "alex",
                "name": "Alex",
            },
        ],
    }

    response = client.post(
        "/split",
        json=payload,
    )

    assert response.status_code == 400

    data = response.json()

    assert "Pizza" in data["detail"]