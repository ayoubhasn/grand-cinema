"""Routes d'administration : statistiques, CRUD et réservations."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import Film, Reservation, ReservationSeat, Room, Screening, User
from app.routers.bookings import _reservation_payload, cancel_reservation

router = APIRouter(prefix="/api/admin", tags=["admin"])
Admin = get_current_admin


def _fill_rate(reserved: int, capacity: int) -> float:
    if capacity <= 0:
        return 0.0
    return round(100.0 * reserved / capacity, 1)


@router.get("/stats")
def stats(db: Session = Depends(get_db), admin: User = Depends(Admin)) -> dict:
    """Statistiques de fréquentation et taux de remplissage."""
    confirmed = db.query(Reservation).filter(Reservation.status == "confirmed").all()
    total_seats = sum(len(r.seats) for r in confirmed)
    total_revenue = round(
        sum(len(r.seats) * r.screening.price for r in confirmed), 2
    )
    screenings = db.query(Screening).all()
    total_capacity = sum(s.room.capacity for s in screenings)
    total_reserved = (
        db.query(ReservationSeat).join(Reservation).filter(
            Reservation.status == "confirmed"
        ).count()
    )

    per_film = []
    for film in db.query(Film).order_by(Film.title).all():
        film_screenings = [s for s in screenings if s.film_id == film.id]
        capacity = sum(s.room.capacity for s in film_screenings)
        reserved = sum(
            len(r.seats) for r in confirmed if r.screening.film_id == film.id
        )
        revenue = round(
            sum(
                len(r.seats) * r.screening.price
                for r in confirmed
                if r.screening.film_id == film.id
            ),
            2,
        )
        per_film.append(
            {
                "film_id": film.id,
                "title": film.title,
                "reservations": sum(
                    1 for r in confirmed if r.screening.film_id == film.id
                ),
                "seats": reserved,
                "revenue": revenue,
                "fill_rate": _fill_rate(reserved, capacity),
            }
        )

    per_room = []
    for room in db.query(Room).order_by(Room.id).all():
        room_screenings = [s for s in screenings if s.room_id == room.id]
        capacity = sum(s.room.capacity for s in room_screenings)
        reserved = sum(
            len(r.seats) for r in confirmed if r.screening.room_id == room.id
        )
        per_room.append(
            {
                "room_id": room.id,
                "name": room.name,
                "seats": reserved,
                "fill_rate": _fill_rate(reserved, capacity),
            }
        )

    per_screening = []
    for screening in sorted(screenings, key=lambda s: s.start_time):
        reserved = sum(
            len(r.seats)
            for r in confirmed
            if r.screening_id == screening.id
        )
        per_screening.append(
            {
                "screening_id": screening.id,
                "film_title": screening.film.title,
                "room_name": screening.room.name,
                "start_time": screening.start_time.isoformat(),
                "capacity": screening.room.capacity,
                "reserved": reserved,
                "fill_rate": _fill_rate(reserved, screening.room.capacity),
                "revenue": round(reserved * screening.price, 2),
            }
        )

    return {
        "total_reservations": len(confirmed),
        "total_seats": total_seats,
        "total_revenue": total_revenue,
        "global_fill_rate": _fill_rate(total_reserved, total_capacity),
        "per_film": per_film,
        "per_room": per_room,
        "per_screening": per_screening,
    }


class FilmBody(BaseModel):
    title: str
    genre: str = ""
    duration_min: int = 0
    synopsis: str = ""
    director: str = ""
    release_year: int = 0
    poster: str = "film1.svg"


class RoomBody(BaseModel):
    name: str
    room_type: str = "Standard"
    capacity: int
    rows: int
    cols: int


class ScreeningBody(BaseModel):
    film_id: int
    room_id: int
    start_time: datetime
    price: float = 11.0


@router.get("/films")
def admin_list_films(db: Session = Depends(get_db), admin: User = Depends(Admin)):
    return [
        {
            "id": f.id,
            "title": f.title,
            "genre": f.genre,
            "duration_min": f.duration_min,
            "director": f.director,
            "release_year": f.release_year,
            "poster": f.poster,
        }
        for f in db.query(Film).order_by(Film.id).all()
    ]


@router.post("/films", status_code=201)
def admin_create_film(
    body: FilmBody, db: Session = Depends(get_db), admin: User = Depends(Admin)
):
    film = Film(**body.model_dump())
    db.add(film)
    db.commit()
    db.refresh(film)
    return {"id": film.id, "title": film.title}


@router.put("/films/{film_id}")
def admin_update_film(
    film_id: int,
    body: FilmBody,
    db: Session = Depends(get_db),
    admin: User = Depends(Admin),
):
    film = db.query(Film).filter(Film.id == film_id).first()
    if film is None:
        raise HTTPException(status_code=404, detail="Film introuvable.")
    for key, value in body.model_dump().items():
        setattr(film, key, value)
    db.commit()
    return {"id": film.id, "title": film.title}


@router.delete("/films/{film_id}")
def admin_delete_film(
    film_id: int, db: Session = Depends(get_db), admin: User = Depends(Admin)
):
    film = db.query(Film).filter(Film.id == film_id).first()
    if film is None:
        raise HTTPException(status_code=404, detail="Film introuvable.")
    db.delete(film)
    db.commit()
    return {"detail": "Film supprimé."}


@router.get("/rooms")
def admin_list_rooms(db: Session = Depends(get_db), admin: User = Depends(Admin)):
    return [
        {
            "id": r.id,
            "name": r.name,
            "room_type": r.room_type,
            "capacity": r.capacity,
            "rows": r.rows,
            "cols": r.cols,
        }
        for r in db.query(Room).order_by(Room.id).all()
    ]


@router.post("/rooms", status_code=201)
def admin_create_room(
    body: RoomBody, db: Session = Depends(get_db), admin: User = Depends(Admin)
):
    if body.rows * body.cols != body.capacity:
        raise HTTPException(
            status_code=400,
            detail="La capacité doit être égale à rangées x sièges par rangée.",
        )
    room = Room(**body.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)
    return {"id": room.id, "name": room.name}


@router.put("/rooms/{room_id}")
def admin_update_room(
    room_id: int,
    body: RoomBody,
    db: Session = Depends(get_db),
    admin: User = Depends(Admin),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Salle introuvable.")
    if body.rows * body.cols != body.capacity:
        raise HTTPException(
            status_code=400,
            detail="La capacité doit être égale à rangées x sièges par rangée.",
        )
    for key, value in body.model_dump().items():
        setattr(room, key, value)
    db.commit()
    return {"id": room.id, "name": room.name}


@router.delete("/rooms/{room_id}")
def admin_delete_room(
    room_id: int, db: Session = Depends(get_db), admin: User = Depends(Admin)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Salle introuvable.")
    db.delete(room)
    db.commit()
    return {"detail": "Salle supprimée."}


@router.get("/screenings")
def admin_list_screenings(db: Session = Depends(get_db), admin: User = Depends(Admin)):
    return [
        {
            "id": s.id,
            "film_id": s.film_id,
            "film_title": s.film.title,
            "room_id": s.room_id,
            "room_name": s.room.name,
            "start_time": s.start_time.isoformat(),
            "price": s.price,
        }
        for s in db.query(Screening).order_by(Screening.start_time).all()
    ]


@router.post("/screenings", status_code=201)
def admin_create_screening(
    body: ScreeningBody, db: Session = Depends(get_db), admin: User = Depends(Admin)
):
    if db.query(Film).filter(Film.id == body.film_id).first() is None:
        raise HTTPException(status_code=404, detail="Film introuvable.")
    if db.query(Room).filter(Room.id == body.room_id).first() is None:
        raise HTTPException(status_code=404, detail="Salle introuvable.")
    screening = Screening(**body.model_dump())
    db.add(screening)
    db.commit()
    db.refresh(screening)
    return {"id": screening.id}


@router.delete("/screenings/{screening_id}")
def admin_delete_screening(
    screening_id: int, db: Session = Depends(get_db), admin: User = Depends(Admin)
):
    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if screening is None:
        raise HTTPException(status_code=404, detail="Séance introuvable.")
    db.delete(screening)
    db.commit()
    return {"detail": "Séance supprimée."}


@router.get("/bookings")
def admin_list_bookings(db: Session = Depends(get_db), admin: User = Depends(Admin)):
    reservations = (
        db.query(Reservation).order_by(Reservation.created_at.desc()).all()
    )
    return [_reservation_payload(r) for r in reservations]


@router.post("/bookings/{reservation_id}/cancel")
def admin_cancel_booking(
    reservation_id: int, db: Session = Depends(get_db), admin: User = Depends(Admin)
):
    reservation = (
        db.query(Reservation).filter(Reservation.id == reservation_id).first()
    )
    if reservation is None:
        raise HTTPException(status_code=404, detail="Réservation introuvable.")
    if reservation.status == "cancelled":
        raise HTTPException(status_code=400, detail="Réservation déjà annulée.")
    cancel_reservation(db, reservation)
    return {"detail": "Réservation annulée.", "id": reservation.id}
