from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import date, time
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import EmailStr
from sqlalchemy import func
from sqlmodel import Field, SQLModel, Session, select

import database

BASE_DIR = Path(__file__).resolve().parent
MENU_FILE = BASE_DIR / "menu.json"


class MenuItemBase(SQLModel):
    name: str
    category: str
    price: float
    description: str
    image: str
    alt: str
    isFeatured: bool = False


class MenuItem(MenuItemBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ReservationBase(SQLModel):
    contact_name: str = Field(min_length=1, max_length=100)
    contact_email: EmailStr
    date: date
    time: time
    guest_count: int = Field(ge=1, le=20)
    special_requests: str | None = Field(default=None, max_length=500)


class Reservation(ReservationBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ReservationCreate(ReservationBase):
    pass


def read_json_file(path: Path, default_value: Any | None = None) -> Any:
    if not path.exists():
        if default_value is None:
            raise FileNotFoundError(f"Expected data file at {path}")

        path.write_text(json.dumps(default_value, indent=2) + "\n", encoding="utf-8")
        return default_value

    return json.loads(path.read_text(encoding="utf-8"))


def seed_menu_items(session: Session) -> None:
    existing_item = session.exec(select(MenuItem).limit(1)).first()
    if existing_item is not None:
        return

    raw_items = read_json_file(MENU_FILE)
    menu_items = [MenuItem.model_validate(item) for item in raw_items]
    session.add_all(menu_items)
    session.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    SQLModel.metadata.create_all(database.engine)

    with Session(database.engine) as session:
        seed_menu_items(session)

    yield


app = FastAPI(
    title="Bean & Brew API",
    description="FastAPI example for serving menu data and reservations.",
    lifespan=lifespan,
)

# Browsers block cross-origin requests by default, so the frontend needs an
# explicit CORS rule before it can call the API from a different local port.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status")
def get_status(session: Session = Depends(database.get_session)) -> dict[str, Any]:
    # FastAPI automatically serializes regular Python dictionaries into JSON.
    return {
        "status": "ok",
        "menu_count": len(session.exec(select(MenuItem)).all()),
        "reservation_count": len(session.exec(select(Reservation)).all()),
    }


@app.get("/api/menu", response_model=list[MenuItem])
def get_menu(
    category: str | None = Query(default=None),
    session: Session = Depends(database.get_session),
) -> list[MenuItem]:
    statement = select(MenuItem).order_by(MenuItem.id)

    if category is None:
        return list(session.exec(statement).all())

    normalized_category = category.strip().casefold()
    filtered_statement = statement.where(
        func.lower(MenuItem.category) == normalized_category
    )
    return list(session.exec(filtered_statement).all())


@app.get("/api/menu/{item_id}", response_model=MenuItem)
def get_menu_item(
    item_id: int,
    session: Session = Depends(database.get_session),
) -> MenuItem:
    item = session.get(MenuItem, item_id)
    if item is not None:
        return item

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Menu item not found.",
    )


@app.post(
    "/api/reservations",
    response_model=Reservation,
    status_code=status.HTTP_201_CREATED,
)
def create_reservation(
    reservation_request: ReservationCreate,
    session: Session = Depends(database.get_session),
) -> Reservation:
    # FastAPI validates the incoming JSON against ReservationCreate before this
    # function runs, so invalid payloads return a 422 response automatically.
    reservation = Reservation.model_validate(reservation_request)
    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    return reservation
