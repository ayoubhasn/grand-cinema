"""Pages HTML publiques (rendues avec Jinja2)."""

from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_optional_user
from app.main_helpers import templates_dir
from app.models import Film, Reservation, ReservationSeat, Screening, Ticket, User

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


@router.get("/seances/{screening_id}", response_class=HTMLResponse)
def screening_page(
    request: Request,
    screening_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    """Page de choix des places pour une séance."""
    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if screening is None:
        return templates.TemplateResponse(
            request, "404.html", _context(user), status_code=404
        )
    taken = [
        row[0]
        for row in db.query(ReservationSeat.seat_label)
        .filter(ReservationSeat.screening_id == screening_id)
        .all()
    ]
    return templates.TemplateResponse(
        request,
        "screening.html",
        _context(
            user,
            screening=screening,
            taken=taken,
            rows=screening.room.rows,
            cols=screening.room.cols,
        ),
    )


@router.get("/mes-billets", response_class=HTMLResponse)
def my_tickets_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    """Page des billets de l'utilisateur connecté."""
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    reservations = (
        db.query(Reservation)
        .filter(Reservation.user_id == user.id)
        .order_by(Reservation.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request, "my_tickets.html", _context(user, reservations=reservations)
    )


@router.get("/billets/{code}", response_class=HTMLResponse)
def ticket_page(
    request: Request,
    code: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    """Page d'un billet électronique (QR code)."""
    ticket = db.query(Ticket).filter(Ticket.code == code.upper()).first()
    if ticket is None:
        return templates.TemplateResponse(
            request, "404.html", _context(user), status_code=404
        )
    return templates.TemplateResponse(
        request, "ticket_detail.html", _context(user, ticket=ticket)
    )


@router.get("/admin", response_class=HTMLResponse)
def admin_page(
    request: Request, user: User | None = Depends(get_optional_user)
):
    """Page d'administration (réservée aux administrateurs)."""
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    if user.role != "admin":
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "admin.html", _context(user))
