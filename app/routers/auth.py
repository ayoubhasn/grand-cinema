"""Routes d'authentification : inscription, connexion, déconnexion, profil."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE_NAME = "access_token"


class RegisterBody(BaseModel):
    email: str
    password: str
    full_name: str = ""


class LoginBody(BaseModel):
    email: str
    password: str


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterBody, db: Session = Depends(get_db)) -> dict:
    """Crée un compte utilisateur (rôle ``user``)."""
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Cet e-mail est déjà utilisé.")
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_payload(user)


@router.post("/login")
def login(body: LoginBody, response: Response, db: Session = Depends(get_db)) -> dict:
    """Connecte l'utilisateur et pose un cookie JWT HttpOnly."""
    user = db.query(User).filter(User.email == body.email).first()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="E-mail ou mot de passe incorrect.")
    token = create_access_token(user.id, user.role)
    response.set_cookie(
        COOKIE_NAME, token, httponly=True, samesite="lax", path="/"
    )
    return _user_payload(user)


@router.post("/logout")
def logout(response: Response) -> dict:
    """Déconnecte l'utilisateur (suppression du cookie)."""
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"detail": "Déconnecté."}


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    """Retourne le profil de l'utilisateur connecté."""
    return _user_payload(user)
