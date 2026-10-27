"""Pages HTML publiques (rendues avec Jinja2)."""

from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_optional_user
from app.main_helpers import templates_dir
from app.models import Film, Screening, User

router = APIRouter()
templates = Jinja2Templates(directory=str(templates_dir()))


def _context(user: User | None, **extra) -> dict:
    context = {"user": user}
    context.update(extra)
    return context


@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    """Page d'accueil : liste des films et leurs affiches."""
    films = db.query(Film).order_by(Film.title).all()
    return templates.TemplateResponse(
        request, "index.html", _context(user, films=films)
    )


@router.get("/films/{film_id}", response_class=HTMLResponse)
def film_detail(
    request: Request,
    film_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    """Page de détail d'un film et calendrier de ses séances."""
    film = db.query(Film).filter(Film.id == film_id).first()
    if film is None:
        return templates.TemplateResponse(
            request, "404.html", _context(user), status_code=404
        )
    screenings = (
        db.query(Screening)
        .filter(
            Screening.film_id == film_id,
            Screening.start_time >= datetime.now(),
        )
        .order_by(Screening.start_time)
        .all()
    )
    by_day: dict[str, list[Screening]] = {}
    for screening in screenings:
        by_day.setdefault(screening.start_time.strftime("%Y-%m-%d"), []).append(
            screening
        )
    return templates.TemplateResponse(
        request,
        "film_detail.html",
        _context(user, film=film, by_day=by_day),
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user: User | None = Depends(get_optional_user)):
    """Page de connexion."""
    return templates.TemplateResponse(request, "login.html", _context(user))


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, user: User | None = Depends(get_optional_user)):
    """Page d'inscription."""
    return templates.TemplateResponse(request, "register.html", _context(user))
