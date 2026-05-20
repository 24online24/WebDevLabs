from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Session, select

import database
from auth import (
    AUTH_REQUIRED_DETAIL,
    FORBIDDEN_DETAIL,
    INITIAL_ADMIN_EMAIL,
    INITIAL_ADMIN_PASSWORD,
    INITIAL_MANAGER_EMAIL,
    INITIAL_MANAGER_PASSWORD,
    INVALID_CREDENTIALS_DETAIL,
    INVALID_SESSION_DETAIL,
    SESSION_HEADER_NAME,
)
from models import MenuItem, Reservation, ReservationStatus, User, UserRole
from routers import api_router
from seed import seed_menu_items, seed_staff_users

BASE_DIR = Path(__file__).resolve().parent
MENU_FILE = BASE_DIR / "menu.json"
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    SQLModel.metadata.create_all(database.engine)

    with Session(database.engine) as session:
        seed_menu_items(session, MENU_FILE)
        seed_staff_users(session)

    yield


app = FastAPI(
    title="Bean & Brew API",
    description="FastAPI example for serving menu data, reservations, and staff tools.",
    lifespan=lifespan,
)

# Browsers block cross-origin requests by default, so the frontend needs an
# explicit CORS rule before it can call the API from a different local port.
# These origins match the default Svelte dev and preview servers used in L10.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/api/status")
def get_status(session: Session = Depends(database.get_session)) -> dict[str, Any]:
    return {
        "status": "ok",
        "menu_count": len(session.exec(select(MenuItem)).all()),
        "reservation_count": len(session.exec(select(Reservation)).all()),
        "staff_user_count": len(session.exec(select(User)).all()),
    }


__all__ = [
    "app",
    "database",
    "MENU_FILE",
    "SESSION_HEADER_NAME",
    "INITIAL_ADMIN_EMAIL",
    "INITIAL_ADMIN_PASSWORD",
    "INITIAL_MANAGER_EMAIL",
    "INITIAL_MANAGER_PASSWORD",
    "INVALID_CREDENTIALS_DETAIL",
    "AUTH_REQUIRED_DETAIL",
    "INVALID_SESSION_DETAIL",
    "FORBIDDEN_DETAIL",
    "MenuItem",
    "Reservation",
    "ReservationStatus",
    "User",
    "UserRole",
]
