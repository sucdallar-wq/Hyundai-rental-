from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.auth import get_db, get_current_user
from app.models import Settings, User

router = APIRouter(prefix="/settings", tags=["Settings"])


class SettingsUpdate(BaseModel):
    interest_rate: Optional[float] = None
    insurance_rate: Optional[float] = None
    profit_margin: Optional[float] = None
    management_fee: Optional[float] = None


@router.get("/")
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    s = db.query(Settings).first()
    if not s:
        return {"message": "Settings bulunamadı"}
    return {
        "interest_rate": s.interest_rate,
        "insurance_rate": s.insurance_rate,
        "profit_margin": s.profit_margin,
        "management_fee": s.management_fee
    }


@router.put("/update")
def update_settings(
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    s = db.query(Settings).first()
    if not s:
        return {"message": "Settings bulunamadı"}

    if payload.interest_rate is not None:
        s.interest_rate = payload.interest_rate
    if payload.insurance_rate is not None:
        s.insurance_rate = payload.insurance_rate
    if payload.profit_margin is not None:
        s.profit_margin = payload.profit_margin
    if payload.management_fee is not None:
        s.management_fee = payload.management_fee

    db.commit()
    return {
        "message": "Settings güncellendi",
        "interest_rate": s.interest_rate,
        "insurance_rate": s.insurance_rate,
        "profit_margin": s.profit_margin,
        "management_fee": s.management_fee
    }


@router.post("/create-default")
def create_default_settings(db: Session = Depends(get_db)):
    existing = db.query(Settings).first()
    if existing:
        return {"message": "Settings zaten var"}

    s = Settings(
        interest_rate=15,
        insurance_rate=2.5,
        profit_margin=10,
        management_fee=50
    )
    db.add(s)
    db.commit()
    return {"message": "Settings oluşturuldu"}