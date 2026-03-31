from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from app.auth import get_db, get_current_user
from app.models import User
from app.services.rental_service import (
    RentalInputs,
    calculate_rental_offer
)

from app.services.rental_scenario_service import (
    calculate_rental_scenarios
)
import os
from app.services.pdf_service import create_rental_offer_pdf
from app.services.survey_service import (
    calculate_usage_factor,
    calculate_residual_factor
)

from app.services.survey_service import calculate_usage_factor
from app.services.survey_service import calculate_residual_factor
from app.models import Settings
from app.models import RentalOffer
from app.services.mail_service import send_rental_offer_email

router = APIRouter(prefix="/rental", tags=["Rental"])

# --------------------------------------------------
# RENTAL CALCULATION
# --------------------------------------------------

@router.post("/calculate")

def rental_calculate(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    inp = RentalInputs(
        model=payload.get("model"),
        machine_count=int(payload.get("machine_count", 1)),
        yearly_hours=int(payload.get("yearly_hours", 2000)),
        months=int(payload.get("months", 36)),
        interest_rate=float(payload.get("interest_rate", 18)),
        insurance_rate=float(payload.get("insurance_rate", 2.5)),
        profit_margin=float(payload.get("profit_margin", 10)),
        management_fee_monthly=float(payload.get("management_fee_monthly", 50)),
        usage_factor=float(payload.get("usage_factor", 1.0)),
    )
    return calculate_rental_offer(inp, db)

# --------------------------------------------------
# RENTAL SCENARIOS
# --------------------------------------------------

@router.post("/scenarios")
def rental_scenarios(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    inp = RentalInputs(
        model=payload["model"],
        machine_count=payload["machine_count"],
        yearly_hours=payload["yearly_hours"],
        months=36,
        interest_rate=payload["interest_rate"],
        insurance_rate=payload["insurance_rate"],
        profit_margin=payload["profit_margin"],
        management_fee_monthly=payload["management_fee_monthly"],
        usage_factor=payload["usage_factor"]
    )

    scenarios = calculate_rental_scenarios(inp, db)

    return {
        "model": inp.model,
        "machine_count": inp.machine_count,
        "scenarios": scenarios
    }

@router.post("/rental-offer-auto")
def rental_offer_auto(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi import HTTPException
    
    settings = db.query(Settings).first()

    if not settings:
        raise HTTPException(status_code=500, detail="Settings tanımlı değil")

    interest_rate = settings.interest_rate
    insurance_rate = settings.insurance_rate
    profit_margin = settings.profit_margin
    management_fee_monthly = settings.management_fee

    answers = payload.get("answers", [])
    survey_score = sum(answers)

    usage_factor = calculate_usage_factor(survey_score)
    residual_factor = calculate_residual_factor(usage_factor)

    scenarios = []

    model = payload["model"]
    machine_count = payload["machine_count"]
    yearly_hours = payload["yearly_hours"]

    for months in [24, 36, 48]:

        inputs = RentalInputs(
            model=model,
            machine_count=machine_count,
            yearly_hours=yearly_hours,
            months=months,
            interest_rate=interest_rate,
            insurance_rate=insurance_rate,
            profit_margin=profit_margin,
            management_fee_monthly=management_fee_monthly,  
            usage_factor=usage_factor,
            residual_factor=residual_factor,
        )

        result = calculate_rental_offer(inputs, db)

        scenarios.append({
            "months": months,
            "monthly_per_machine": result["result"]["monthly_rent_per_machine"],
            "breakdown": result["breakdown_usd"]
        })

    file_path = create_rental_offer_pdf(
        customer=payload["customer"],
        email=payload.get("email"),
        model=payload["model"],
        machine_count=payload["machine_count"],
        yearly_hours=payload["yearly_hours"],
        survey_score=survey_score,
        usage_factor=usage_factor,
        residual_factor=residual_factor,
        scenarios=scenarios,
        salesman=current_user.username           
    )
    file_name = os.path.basename(file_path)
    #send_rental_offer_email(payload.get("email"), file_path)
    offer = RentalOffer(
        customer=payload["customer"],
        email=payload.get("email"),
        model=payload["model"],
        machine_count=payload["machine_count"],
        yearly_hours=payload["yearly_hours"],
        survey_score=survey_score,
        usage_factor=usage_factor,
        residual_factor=residual_factor,
        monthly_rent=scenarios[1]["monthly_per_machine"],
        pdf_file=file_name
    )
    
    print(current_user.__dict__)
    db.add(offer)
    db.commit()
    db.refresh(offer)

    return {
        "survey_score": survey_score,
        "usage_factor": usage_factor,
        "residual_factor": residual_factor,
        "scenarios": scenarios,
        "pdf_file": file_name
    }