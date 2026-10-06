# app/services/rental_scenario_service.py
from app.services.rental_service import RentalInputs, calculate_rental_offer
from sqlalchemy.orm import Session

def calculate_rental_scenarios(inputs: RentalInputs, db: Session):
    scenarios = [24, 36, 48, 60]
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