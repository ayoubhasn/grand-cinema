"""Application FastAPI Le Grand Cinéma."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, SessionLocal, engine
from app.main_helpers import static_dir
from app.routers import auth, films, pages
from app.seed import seed

app = FastAPI(
    title="Le Grand Cinéma",
    description=(
        "Application web de réservation de places : films, séances, "
        "réservations en ligne et billets dématérialisés."
    ),
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=str(static_dir())), name="static")
app.include_router(auth.router)
app.include_router(films.router)
app.include_router(pages.router)


@app.on_event("startup")
def startup() -> None:
    """Crée les tables et peuple la base de démonstration si besoin."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
