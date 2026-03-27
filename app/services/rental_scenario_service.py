from app.services.rental_service import calculate_rental_offer


def calculate_rental_scenarios(inputs, db):

    scenarios = [24, 36, 48]

    results = []

    for m in scenarios:

        inputs.months = m

        result = calculate_rental_offer(inputs, db)

        results.append({
            "months": m,
            "monthly_per_machine": result["result"]["monthly_rent_per_machine"],
            "monthly_total": result["result"]["monthly_rent_total"]
        })

    return results