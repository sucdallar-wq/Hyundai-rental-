from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import get_db, hash_password, authenticate_user, create_access_token, get_current_user
from app.models import User


router = APIRouter()


@router.post("/create-user")
def create_user(
    username: str,
    password: str,
    role: str,
    db: Session = Depends(get_db),
):

    existing = db.query(User).filter(User.username == username).first()

    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        username=username,
        password=hash_password(password),
        role=role,
    )

    db.add(user)
    db.commit()

    return {"message": "User created"}


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.username})

    return {"access_token": token, "token_type": "bearer"}


@router.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.username}"}