"""Modèles de données (SQLAlchemy).

Socle de la branche ``main`` : utilisateurs, films, salles, séances.
Les modèles de réservation (Reservation, ReservationSeat, Ticket) sont
ajoutés sur la branche ``feature/reservation``.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """Utilisateur de la plateforme (rôle ``user`` ou ``admin``)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(20), default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Film(Base):
    """Film à l'affiche."""

    __tablename__ = "films"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    genre: Mapped[str] = mapped_column(String(100), default="")
    duration_min: Mapped[int] = mapped_column(Integer, default=0)
    synopsis: Mapped[str] = mapped_column(Text, default="")
    director: Mapped[str] = mapped_column(String(255), default="")
    release_year: Mapped[int] = mapped_column(Integer, default=0)
    poster: Mapped[str] = mapped_column(String(255), default="")

    screenings: Mapped[list["Screening"]] = relationship(
        "Screening", back_populates="film", cascade="all, delete-orphan"
    )


class Room(Base):
    """Salle du cinéma (capacité découpée en rangées x sièges)."""

    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    room_type: Mapped[str] = mapped_column(String(50), default="Standard")
    capacity: Mapped[int] = mapped_column(Integer)
    rows: Mapped[int] = mapped_column(Integer)
    cols: Mapped[int] = mapped_column(Integer)

    screenings: Mapped[list["Screening"]] = relationship(
        "Screening", back_populates="room", cascade="all, delete-orphan"
    )


class Screening(Base):
    """Séance : un film, dans une salle, à une date et un prix."""

    __tablename__ = "screenings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    film_id: Mapped[int] = mapped_column(ForeignKey("films.id"))
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"))
    start_time: Mapped[datetime] = mapped_column(DateTime)
    price: Mapped[float] = mapped_column(Float, default=11.0)

    film: Mapped[Film] = relationship("Film", back_populates="screenings")
    room: Mapped[Room] = relationship("Room", back_populates="screenings")
