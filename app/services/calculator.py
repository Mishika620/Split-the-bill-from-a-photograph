from dataclasses import dataclass

from app.models.bill import Bill


@dataclass
class PersonSplit:
    person_id: str
    person_name: str
    item_total: float
    tax: float
    service_charge: float
    discount: float
    final_total: float


def calculate_split(
    bill: Bill,
    people: list[dict],
) -> list[PersonSplit]:
    """
    Calculate each person's share of a bill.

    Rules:
    - An item can be assigned to one or more people.
    - A shared item is divided equally between its assignees.
    - Tax is distributed proportionally according to consumption.
    - Service charge is distributed proportionally according to consumption.
    - Discount is distributed proportionally according to consumption.
    - Final amounts are rounded to two decimal places.
    """

    if not people:
        return []

    # -------------------------------------------------
    # Prepare people
    # -------------------------------------------------

    person_ids = [
        person["id"]
        for person in people
    ]

    person_names = {
        person["id"]: person["name"]
        for person in people
    }

    consumption = {
        person_id: 0.0
        for person_id in person_ids
    }

    # -------------------------------------------------
    # Calculate item consumption
    # -------------------------------------------------

    for item in bill.items:

        assigned_people = item.assigned_to

        if not assigned_people:
            continue

        valid_assignees = [
            person_id
            for person_id in assigned_people
            if person_id in consumption
        ]

        if not valid_assignees:
            continue

        item_share = (
            item.total_price
            / len(valid_assignees)
        )

        for person_id in valid_assignees:
            consumption[person_id] += item_share

    # -------------------------------------------------
    # Total actual consumption
    # -------------------------------------------------

    total_consumption = sum(
        consumption.values()
    )

    if total_consumption <= 0:
        return [
            PersonSplit(
                person_id=person_id,
                person_name=person_names[person_id],
                item_total=0.0,
                tax=0.0,
                service_charge=0.0,
                discount=0.0,
                final_total=0.0,
            )
            for person_id in person_ids
        ]

    # -------------------------------------------------
    # Calculate proportional amounts
    # -------------------------------------------------

    results: list[PersonSplit] = []

    for person_id in person_ids:

        item_total = round(
            consumption[person_id],
            2,
        )

        ratio = (
            consumption[person_id]
            / total_consumption
        )

        tax = round(
            bill.tax * ratio,
            2,
        )

        service_charge = round(
            bill.service_charge * ratio,
            2,
        )

        discount = round(
            bill.discount * ratio,
            2,
        )

        final_total = round(
            item_total
            + tax
            + service_charge
            - discount,
            2,
        )

        results.append(
            PersonSplit(
                person_id=person_id,
                person_name=person_names[person_id],
                item_total=item_total,
                tax=tax,
                service_charge=service_charge,
                discount=discount,
                final_total=final_total,
            )
        )

    # -------------------------------------------------
    # Rounding correction
    #
    # Correct the last person's final amount so that
    # the sum of individual payments equals the bill.
    # -------------------------------------------------

    expected_total = round(
        bill.subtotal
        + bill.tax
        + bill.service_charge
        - bill.discount,
        2,
    )

    calculated_total = round(
        sum(
            result.final_total
            for result in results
        ),
        2,
    )

    difference = round(
        expected_total - calculated_total,
        2,
    )

    if results and difference != 0:
        last = results[-1]

        results[-1] = PersonSplit(
            person_id=last.person_id,
            person_name=last.person_name,
            item_total=last.item_total,
            tax=last.tax,
            service_charge=last.service_charge,
            discount=last.discount,
            final_total=round(
                last.final_total + difference,
                2,
            ),
        )

    return results