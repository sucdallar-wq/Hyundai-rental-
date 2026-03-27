from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
from app.auth import get_db, get_current_user 
from app.models import User
from app.database import engine, Base
from fastapi import File, UploadFile
from app.api.auth_router import router as auth_router
from app.api.rental_router import router as rental_router
from app.api.maintenance_router import router as maintenance_router
from app.api.offer_router import router as offer_router
from app.api.excel_router import router as excel_router
from app.services.rental_service import RentalInputs
from app.services.rental_service import calculate_rental_offer
from app.api.settings_router import router as settings_router
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # öneml
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "pdf")

app.mount("/pdf", StaticFiles(directory=PDF_DIR), name="pdf")

app.include_router(auth_router)
app.include_router(rental_router)
app.include_router(maintenance_router)
app.include_router(offer_router)
app.include_router(excel_router)
app.include_router(settings_router)

Base.metadata.create_all(bind=engine)




@app.get("/")
def root():
    return {"message": "System running"}

# --------------------------------------------------
# ROOT
# --------------------------------------------------

@app.get("/")
def root():
    return {"message": "Hyundai Bayi Test Sistemi Çalışıyor 🚀"}


# --------------------------------------------------
# MAINTENANCE COST
# --------------------------------------------------

@app.get("/maintenance-cost")
def get_maintenance_cost(
    model_code: str,
    hours: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recete_id = f"{model_code}_{hours}"

    package = db.query(MaintenancePackage).filter(
        MaintenancePackage.recete_id == recete_id
    ).first()

    if not package:
        raise HTTPException(status_code=404, detail="Maintenance package not found")

    return {
        "recete_id": recete_id,
        "total_cost": package.total_cost
    }


# --------------------------------------------------
# MAINTENANCE LINES
# --------------------------------------------------

@app.get("/maintenance-lines")
def get_maintenance_lines(
    model: str,
    hours: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    recete_id = f"{model}_{hours}"

    lines = db.query(MaintenanceLine).filter(
        MaintenanceLine.recete_id == recete_id
    ).order_by(MaintenanceLine.line_id).all()

    if not lines:
        raise HTTPException(status_code=404, detail="Recete not found")

    return [
        {
            "part_code": l.part_code,
            "description": l.description,
            "quantity": l.quantity,
            "unit": l.unit,
            "unit_price": l.unit_price,
            "line_total": l.line_total
        }
        for l in lines
    ]


# --------------------------------------------------
# MAINTENANCE PDF
# --------------------------------------------------

@app.get("/maintenance-offer-pdf")
def maintenance_offer_pdf(
    model: str,
    hours: int,
    customer: str,
    discount: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    recete_id = f"{model}_{hours}"

    lines = db.query(MaintenanceLine).filter(
        MaintenanceLine.recete_id == recete_id
    ).all()

    if not lines:
        raise HTTPException(status_code=404, detail="Recete bulunamadı")

    file_name = create_maintenance_pdf(
        recete_id,
        lines,
        discount,
        customer,
        model,
        hours
    )

    file_path = os.path.join(PDF_DIR, file_name)
    
    return FileResponse(
    file_path,
    media_type="application/pdf",
    filename=file_name
    )


# --------------------------------------------------
# MAINTENANCE EMAIL
# --------------------------------------------------

@app.get("/send-offer-email")
def send_offer_email_api(
    email: str,
    model: str,
    hours: int,
    discount: float,
    customer: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    recete_id = f"{model}_{hours}"

    lines = db.query(MaintenanceLine).filter(
        MaintenanceLine.recete_id == recete_id
    ).all()

    file_name = create_maintenance_pdf(
        recete_id,
        lines,
        discount,
        customer,
        model,
        hours
    )

    send_offer_email(email, file_name)

    return {"message": "Teklif email ile gönderildi"}


# --------------------------------------------------
# SURVEY
# --------------------------------------------------

class SurveyInput(BaseModel):
    answers: list[int]


@app.post("/survey-calculate")
def survey_calculate(payload: SurveyInput):

    score = sum(payload.answers)

    usage_factor = calculate_usage_factor(score)

    residual_factor = calculate_residual_factor(usage_factor)

    return {
        "score": score,
        "usage_factor": usage_factor,
        "residual_factor": residual_factor
    }







# --------------------------------------------------
# DEBUG TIRES
# --------------------------------------------------

@app.get("/debug-tires")
def debug_tires(db: Session = Depends(get_db)):

    tires = db.query(TireCost).all()

    return [
        {
            "model": t.machine_model,
            "tire_price_usd": t.tire_price_usd
        }
        for t in tires
    ]
@app.get("/maintenance-hours")
def get_maintenance_hours(
    model: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    lines = db.query(MaintenanceLine).filter(
        MaintenanceLine.recete_id.like(f"{model}_%")
    ).all()

    if not lines:
        raise HTTPException(status_code=404, detail="Model için bakım reçetesi bulunamadı")

    hours = set()

    for l in lines:

        try:
            hour = int(l.recete_id.split("_")[1])
            hours.add(hour)
        except:
            continue

    return {
        "model": model,
        "available_hours": sorted(list(hours))
    }

@app.get("/debug-recetes")
def debug_recetes(db: Session = Depends(get_db)):

    lines = db.query(MaintenanceLine.recete_id).distinct().all()

    return [l[0] for l in lines]

@app.get("/offers")
def list_offers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    offers = db.query(RentalOffer).order_by(
        RentalOffer.created_at.desc()
    ).all()

    return [

        {
            "id": o.id,
            "customer": o.customer,
            "model": o.model,
            "machines": o.machine_count,
            "monthly_rent": o.monthly_rent,
            "created": o.created_at
        }

        for o in offers
    ]