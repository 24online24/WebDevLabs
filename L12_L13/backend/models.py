from __future__ import annotations

from datetime import UTC, date as DateValue, datetime, time as TimeValue
from enum import Enum

from pydantic import EmailStr, field_validator
from sqlmodel import Field, SQLModel


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
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0)
    description: str = Field(min_length=1, max_length=500)
    image: str = Field(min_length=1, max_length=500)
    alt: str = Field(min_length=1, max_length=200)
    isFeatured: bool = False

    @field_validator("name", "category", "description", "image", "alt")
    @classmethod
    def validate_non_blank_text(cls, value: str) -> str:
        trimmed_value = value.strip()
        if not trimmed_value:
            raise ValueError("Value cannot be blank.")

        return trimmed_value


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
