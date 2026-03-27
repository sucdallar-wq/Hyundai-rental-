from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi.responses import FileResponse

from app.auth import get_db, get_current_user
from app.models import User

from app.services.maintenance_service import get_maintenance_lines
from app.services.pdf_service import create_maintenance_pdf
from app.services.mail_service import send_offer_email
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(BASE_DIR, "pdf")



router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

class MaintenanceCalcRequest(BaseModel):
    model: str
    hours: int


class MaintenancePdfRequest(BaseModel):
    customer: str
    model: str
    hours: int
    discount: float = 0


# --------------------------------------------------
# CALCULATE MAINTENANCE
# --------------------------------------------------

@router.post("/calc")
def maintenance_calc(
    req: MaintenanceCalcRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    lines = get_maintenance_lines(db, req.model, req.hours)

    if not lines:
        raise HTTPException(status_code=404, detail="Bakım reçetesi bulunamadı")

    rows = []
    total = 0

    for l in lines:
        total += l.line_total

        rows.append({
            "code": l.part_code,
            "part_name": l.description,
            "quantity": l.quantity,
            "unit": l.unit,
            "unit_price": l.unit_price,
            "line_total": l.line_total
        })

    return {
        "rows": rows,
        "total": round(total, 2)
    }


# --------------------------------------------------
# CREATE PDF
# --------------------------------------------------

@router.post("/pdf")
def maintenance_pdf(
    req: MaintenancePdfRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    lines = get_maintenance_lines(db, req.model, req.hours)

    if not lines:
        raise HTTPException(status_code=404, detail="Bakım reçetesi bulunamadı")

    recete_id = f"{req.model}_{req.hours}"

    file_path = create_maintenance_pdf(
        recete_id,
        lines,
        req.discount,
        req.customer,
        req.model,
        req.hours,
        current_user.username
    )

    return FileResponse(
       file_path,
       media_type="application/pdf",
       filename=os.path.basename(file_path)
    )

# --------------------------------------------------
# SEND EMAIL
# --------------------------------------------------

@router.post("/send-mail")
def maintenance_send_mail(
    req: MaintenancePdfRequest,
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lines = get_maintenance_lines(db, req.model, req.hours)

    file_path = create_maintenance_pdf(
        f"{req.model}_{req.hours}",
        lines,
        req.discount,
        req.customer,
        req.model,
        req.hours,
        current_user.username
    )

    send_offer_email(email, file_path)

    return {"status":"mail sent"}