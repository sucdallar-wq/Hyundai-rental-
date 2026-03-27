from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_db, get_current_user
from app.models import User, Machine
from app.services.excel_service import import_excel


router = APIRouter(prefix="/excel", tags=["Excel"])


# --------------------------------------------------
# EXCEL IMPORT
# --------------------------------------------------

@router.post("/upload")
def upload_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can upload")

    file_location = f"./{file.filename}"

    with open(file_location, "wb+") as f:
        f.write(file.file.read())

    import_excel(file_location, db)

    return {"message": "Excel imported successfully"}


# --------------------------------------------------
# MACHINE LIST
# --------------------------------------------------

@router.get("/machines")
def get_machines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    machines = db.query(Machine).all()

    return [
        {
            "id": m.id,
            "model_code": m.model_code,
            "model_name": m.model_name,
            "type": m.type,
            "price_usd": m.price_usd
        }
        for m in machines
    ]