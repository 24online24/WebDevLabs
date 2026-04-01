from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import date, time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

BASE_DIR = Path(__file__).resolve().parent
MENU_FILE = BASE_DIR / "menu.json"
RESERVATIONS_FILE = BASE_DIR / "reservations.json"


class MenuItem(BaseModel):
    id: int
    name: str
    category: str
    price: float
    description: str
    image: str
    alt: str
    isFeatured: bool = False


class ReservationRequest(BaseModel):
    contact_name: str = Field(min_length=1, max_length=100)
    contact_email: EmailStr
    date: date
    time: time
    guest_count: int = Field(ge=1, le=20)
    special_requests: str | None = Field(default=None, max_length=500)


class ReservationRecord(ReservationRequest):
    id: int


menu_items: list[MenuItem] = []
reservations: list[ReservationRecord] = []


def read_json_file(path: Path, default_value: Any | None = None) -> Any:
    if not path.exists():
        if default_value is None:
            raise FileNotFoundError(f"Expected data file at {path}")

        path.write_text(json.dumps(default_value, indent=2) + "\n", encoding="utf-8")
        return default_value

    return json.loads(path.read_text(encoding="utf-8"))


def load_menu_items() -> list[MenuItem]:
    raw_items = read_json_file(MENU_FILE)
    return [MenuItem.model_validate(item) for item in raw_items]


def load_reservations() -> list[ReservationRecord]:
    raw_reservations = read_json_file(RESERVATIONS_FILE, default_value=[])
    return [ReservationRecord.model_validate(item) for item in raw_reservations]


def save_reservations() -> None:
    serializable_reservations = [
        reservation.model_dump(mode="json") for reservation in reservations
    ]
    RESERVATIONS_FILE.write_text(
        json.dumps(serializable_reservations, indent=2) + "\n",
        encoding="utf-8",
    )


def load_app_data() -> None:
    global menu_items, reservations
    menu_items = load_menu_items()
    reservations = load_reservations()


def next_reservation_id() -> int:
    if not reservations:
        return 1

    return max(reservation.id for reservation in reservations) + 1


@asynccontextmanager
async def lifespan(_: FastAPI):
    load_app_data()
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
def get_status() -> dict[str, Any]:
    # FastAPI automatically serializes regular Python dictionaries into JSON.
    return {
        "status": "ok",
        "menu_count": len(menu_items),
        "reservation_count": len(reservations),
    }


@app.get("/api/menu", response_model=list[MenuItem])
def get_menu(category: str | None = Query(default=None)) -> list[MenuItem]:
    if category is None:
        return menu_items

    normalized_category = category.strip().casefold()
    return [
        item
        for item in menu_items
        if item.category.strip().casefold() == normalized_category
    ]


@app.get("/api/menu/{item_id}", response_model=MenuItem)
def get_menu_item(item_id: int) -> MenuItem:
    for item in menu_items:
        if item.id == item_id:
            return item

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found.")


@app.post(
    "/api/reservations",
    response_model=ReservationRecord,
    status_code=status.HTTP_201_CREATED,
)
def create_reservation(reservation_request: ReservationRequest) -> ReservationRecord:
    # FastAPI validates the incoming JSON against ReservationRequest before this
    # function runs, so invalid payloads return a 422 response automatically.
    reservation = ReservationRecord(
        id=next_reservation_id(),
        **reservation_request.model_dump(),
    )
    reservations.append(reservation)
    save_reservations()
    return reservation
