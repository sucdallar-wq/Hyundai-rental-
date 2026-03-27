from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth import get_db
from app.models import Settings

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.post("/create-default")
def create_default_settings(db: Session = Depends(get_db)):

    existing = db.query(Settings).first()

    if existing:
        return {"message": "Settings zaten var"}

    s = Settings(
        interest_rate=18,
        insurance_rate=2.5,
        profit_margin=10,
        management_fee=50
    )

    db.add(s)
    db.commit()

    return {"message": "Settings oluşturuldu"}