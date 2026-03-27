from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import get_db, get_current_user
from app.models import User, RentalOffer


router = APIRouter(prefix="/offers", tags=["Offers"])


@router.get("/offers")
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


@router.get("/{offer_id}")
def get_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    offer = db.query(RentalOffer).filter(
        RentalOffer.id == offer_id
    ).first()

    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    return offer


@router.get("/{offer_id}/pdf")
def get_offer_pdf(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    offer = db.query(RentalOffer).filter(
        RentalOffer.id == offer_id
    ).first()

    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    return FileResponse(
        offer.pdf_file,
        media_type="application/pdf",
        filename=offer.pdf_file
    )