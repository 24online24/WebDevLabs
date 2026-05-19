from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from contextlib import asynccontextmanager
from datetime import UTC, date as DateValue, datetime, time as TimeValue, timedelta
from enum import Enum
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import EmailStr
from sqlalchemy import func
from sqlmodel import Field, SQLModel, Session, select

import database

BASE_DIR = Path(__file__).resolve().parent
MENU_FILE = BASE_DIR / "menu.json"
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]
SESSION_HEADER_NAME = "X-Session-Token"
SESSION_DURATION = timedelta(hours=int(os.getenv("SESSION_DURATION_HOURS", "8")))
INITIAL_ADMIN_EMAIL = os.getenv("INITIAL_ADMIN_EMAIL", "admin@example.com")
INITIAL_ADMIN_PASSWORD = os.getenv("INITIAL_ADMIN_PASSWORD", "adminpass123")
INITIAL_MANAGER_EMAIL = os.getenv("INITIAL_MANAGER_EMAIL", "manager@example.com")
INITIAL_MANAGER_PASSWORD = os.getenv("INITIAL_MANAGER_PASSWORD", "managerpass123")
INVALID_CREDENTIALS_DETAIL = "Invalid credentials."
AUTH_REQUIRED_DETAIL = "Authentication required."
INVALID_SESSION_DETAIL = "Session is invalid or expired."
FORBIDDEN_DETAIL = "You do not have permission to perform this action."


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"


class ReservationStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


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


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(MenuItemBase):
    pass


class ReservationBase(SQLModel):
    contact_name: str = Field(min_length=1, max_length=100)
    contact_email: EmailStr
    date: DateValue
    time: TimeValue
    guest_count: int = Field(ge=1, le=20)
    special_requests: str | None = Field(default=None, max_length=500)


class Reservation(ReservationBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: ReservationStatus = Field(default=ReservationStatus.pending, index=True)
    internal_notes: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    updated_by_id: int | None = Field(default=None, foreign_key="users.id")


class ReservationCreate(ReservationBase):
    pass


class ReservationUpdate(SQLModel):
    contact_name: str | None = Field(default=None, min_length=1, max_length=100)
    contact_email: EmailStr | None = None
    date: DateValue | None = None
    time: TimeValue | None = None
    guest_count: int | None = Field(default=None, ge=1, le=20)
    special_requests: str | None = Field(default=None, max_length=500)
    status: ReservationStatus | None = None
    internal_notes: str | None = Field(default=None, max_length=500)


class UserBase(SQLModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=100)
    role: UserRole = UserRole.manager
    is_active: bool = True


class User(UserBase, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class StaffUserCreate(SQLModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.manager


class StaffUserUpdate(SQLModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    role: UserRole | None = None
    is_active: bool | None = None


class StaffUserRead(UserBase):
    id: int
    created_at: datetime


class LoginRequest(SQLModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserSession(SQLModel, table=True):
    __tablename__ = "user_sessions"

    id: int | None = Field(default=None, primary_key=True)
    token: str = Field(index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    revoked_at: datetime | None = Field(default=None)


class SessionResponse(SQLModel):
    session_token: str
    user: StaffUserRead


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000,
    )
    return f"{salt.hex()}${derived_key.hex()}"


def verify_password(password: str, stored_password: str) -> bool:
    try:
        salt_hex, stored_hash = stored_password.split("$", maxsplit=1)
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000,
    )
    return hmac.compare_digest(derived_key.hex(), stored_hash)


def build_user_response(user: User) -> StaffUserRead:
    if user.id is None:
        raise ValueError("User ID must be set before serializing a user.")

    return StaffUserRead(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def get_user_by_email(session: Session, email: str) -> User | None:
    normalized_email = normalize_email(email)
    statement = select(User).where(func.lower(User.email) == normalized_email)
    return session.exec(statement).first()


def create_user(
    session: Session,
    *,
    email: str,
    display_name: str,
    password: str,
    role: UserRole,
) -> User:
    existing_user = get_user_by_email(session, email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with that email already exists.",
        )

    user = User(
        email=normalize_email(email),
        display_name=display_name.strip(),
        hashed_password=hash_password(password),
        role=role,
        updated_at=utc_now(),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_user_session(session: Session, user: User) -> UserSession:
    if user.id is None:
        raise ValueError("User ID must be set before creating a session.")

    user_session = UserSession(
        token=secrets.token_urlsafe(32),
        user_id=user.id,
        expires_at=utc_now() + SESSION_DURATION,
    )
    session.add(user_session)
    session.commit()
    session.refresh(user_session)
    return user_session


def revoke_user_session(session: Session, user_session: UserSession) -> None:
    user_session.revoked_at = utc_now()
    session.add(user_session)
    session.commit()


def get_session_token(
    x_session_token: Annotated[str | None, Header(alias=SESSION_HEADER_NAME)] = None,
) -> str:
    if x_session_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_REQUIRED_DETAIL,
        )

    return x_session_token


def get_current_user_session(
    session_token: Annotated[str, Depends(get_session_token)],
    session: Session = Depends(database.get_session),
) -> UserSession:
    statement = select(UserSession).where(UserSession.token == session_token)
    user_session = session.exec(statement).first()

    if user_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_SESSION_DETAIL,
        )

    if user_session.revoked_at is not None or user_session.expires_at <= utc_now():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_SESSION_DETAIL,
        )

    return user_session


def get_current_user(
    user_session: Annotated[UserSession, Depends(get_current_user_session)],
    session: Session = Depends(database.get_session),
) -> User:
    user = session.get(User, user_session.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_SESSION_DETAIL,
        )

    return user


def require_manager_or_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role not in {UserRole.admin, UserRole.manager}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=FORBIDDEN_DETAIL,
        )

    return current_user


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=FORBIDDEN_DETAIL,
        )

    return current_user


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


def seed_staff_users(session: Session) -> None:
    existing_user = session.exec(select(User).limit(1)).first()
    if existing_user is not None:
        return

    create_user(
        session,
        email=INITIAL_ADMIN_EMAIL,
        display_name="Administrator",
        password=INITIAL_ADMIN_PASSWORD,
        role=UserRole.admin,
    )
    create_user(
        session,
        email=INITIAL_MANAGER_EMAIL,
        display_name="Manager",
        password=INITIAL_MANAGER_PASSWORD,
        role=UserRole.manager,
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    SQLModel.metadata.create_all(database.engine)

    with Session(database.engine) as session:
        seed_menu_items(session)
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


@app.get("/api/status")
def get_status(session: Session = Depends(database.get_session)) -> dict[str, Any]:
    # FastAPI automatically serializes regular Python dictionaries into JSON.
    return {
        "status": "ok",
        "menu_count": len(session.exec(select(MenuItem)).all()),
        "reservation_count": len(session.exec(select(Reservation)).all()),
        "staff_user_count": len(session.exec(select(User)).all()),
    }


@app.post("/api/auth/login", response_model=SessionResponse)
def login(
    login_request: LoginRequest,
    session: Session = Depends(database.get_session),
) -> SessionResponse:
    user = get_user_by_email(session, str(login_request.email))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_DETAIL,
        )

    if not verify_password(login_request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_DETAIL,
        )

    user_session = create_user_session(session, user)
    return SessionResponse(
        session_token=user_session.token,
        user=build_user_response(user),
    )


@app.get("/api/auth/me", response_model=StaffUserRead)
def get_authenticated_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> StaffUserRead:
    return build_user_response(current_user)


@app.post("/api/auth/logout")
def logout(
    user_session: Annotated[UserSession, Depends(get_current_user_session)],
    session: Session = Depends(database.get_session),
) -> dict[str, str]:
    revoke_user_session(session, user_session)
    return {"status": "logged_out"}


@app.get("/api/staff/users", response_model=list[StaffUserRead])
def list_staff_users(
    _: Annotated[User, Depends(require_admin)],
    session: Session = Depends(database.get_session),
) -> list[StaffUserRead]:
    users = session.exec(select(User).order_by(User.id)).all()
    return [build_user_response(user) for user in users]


@app.post(
    "/api/staff/users",
    response_model=StaffUserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_staff_user(
    user_request: StaffUserCreate,
    _: Annotated[User, Depends(require_admin)],
    session: Session = Depends(database.get_session),
) -> StaffUserRead:
    user = create_user(
        session,
        email=str(user_request.email),
        display_name=user_request.display_name,
        password=user_request.password,
        role=user_request.role,
    )
    return build_user_response(user)


@app.patch("/api/staff/users/{user_id}", response_model=StaffUserRead)
def update_staff_user(
    user_id: int,
    user_request: StaffUserUpdate,
    current_user: Annotated[User, Depends(require_admin)],
    session: Session = Depends(database.get_session),
) -> StaffUserRead:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff user not found.",
        )

    if user.id == current_user.id:
        if user_request.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own account.",
            )

        if user_request.role is not None and user_request.role != UserRole.admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot remove your own admin role.",
            )

    if user_request.display_name is not None:
        user.display_name = user_request.display_name.strip()

    if user_request.role is not None:
        user.role = user_request.role

    if user_request.is_active is not None:
        user.is_active = user_request.is_active

    user.updated_at = utc_now()
    session.add(user)
    session.commit()
    session.refresh(user)
    return build_user_response(user)


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


@app.post("/api/menu", response_model=MenuItem, status_code=status.HTTP_201_CREATED)
def create_menu_item(
    menu_item_request: MenuItemCreate,
    _: Annotated[User, Depends(require_admin)],
    session: Session = Depends(database.get_session),
) -> MenuItem:
    menu_item = MenuItem.model_validate(menu_item_request)
    session.add(menu_item)
    session.commit()
    session.refresh(menu_item)
    return menu_item


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


@app.put("/api/menu/{item_id}", response_model=MenuItem)
def update_menu_item(
    item_id: int,
    menu_item_request: MenuItemUpdate,
    _: Annotated[User, Depends(require_admin)],
    session: Session = Depends(database.get_session),
) -> MenuItem:
    menu_item = session.get(MenuItem, item_id)
    if menu_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found.",
        )

    for field_name, value in menu_item_request.model_dump().items():
        setattr(menu_item, field_name, value)

    session.add(menu_item)
    session.commit()
    session.refresh(menu_item)
    return menu_item


@app.delete("/api/menu/{item_id}")
def delete_menu_item(
    item_id: int,
    _: Annotated[User, Depends(require_admin)],
    session: Session = Depends(database.get_session),
) -> dict[str, str]:
    menu_item = session.get(MenuItem, item_id)
    if menu_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found.",
        )

    session.delete(menu_item)
    session.commit()
    return {"status": "deleted"}


@app.get("/api/reservations", response_model=list[Reservation])
def list_reservations(
    reservation_date: DateValue | None = Query(default=None, alias="date"),
    reservation_status: ReservationStatus | None = Query(default=None, alias="status"),
    _: Annotated[User, Depends(require_manager_or_admin)] = None,
    session: Session = Depends(database.get_session),
) -> list[Reservation]:
    statement = select(Reservation).order_by(
        Reservation.date,
        Reservation.time,
        Reservation.id,
    )

    if reservation_date is not None:
        statement = statement.where(Reservation.date == reservation_date)

    if reservation_status is not None:
        statement = statement.where(Reservation.status == reservation_status)

    return list(session.exec(statement).all())


@app.get("/api/reservations/{reservation_id}", response_model=Reservation)
def get_reservation(
    reservation_id: int,
    _: Annotated[User, Depends(require_manager_or_admin)],
    session: Session = Depends(database.get_session),
) -> Reservation:
    reservation = session.get(Reservation, reservation_id)
    if reservation is not None:
        return reservation

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Reservation not found.",
    )


@app.patch("/api/reservations/{reservation_id}", response_model=Reservation)
def update_reservation(
    reservation_id: int,
    reservation_request: ReservationUpdate,
    current_user: Annotated[User, Depends(require_manager_or_admin)],
    session: Session = Depends(database.get_session),
) -> Reservation:
    reservation = session.get(Reservation, reservation_id)
    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found.",
        )

    update_data = reservation_request.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(reservation, field_name, value)

    reservation.updated_at = utc_now()
    reservation.updated_by_id = current_user.id

    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    return reservation


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
