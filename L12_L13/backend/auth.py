from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import timedelta
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import func
from sqlmodel import Session, select

import database
from models import StaffUserRead, User, UserRole, UserSession, utc_now

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
