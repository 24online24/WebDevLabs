from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import database
from auth import (
    INVALID_CREDENTIALS_DETAIL,
    build_user_response,
    create_user_session,
    get_current_user,
    get_current_user_session,
    get_user_by_email,
    revoke_user_session,
    verify_password,
)
from models import LoginRequest, SessionResponse, StaffUserRead, User, UserSession

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=SessionResponse)
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


@router.get("/me", response_model=StaffUserRead)
def get_authenticated_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> StaffUserRead:
    return build_user_response(current_user)


@router.post("/logout")
def logout(
    user_session: Annotated[UserSession, Depends(get_current_user_session)],
    session: Session = Depends(database.get_session),
) -> dict[str, str]:
    revoke_user_session(session, user_session)
    return {"status": "logged_out"}