from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

import database
from auth import build_user_response, create_user, require_admin
from models import StaffUserCreate, StaffUserRead, StaffUserUpdate, User, UserRole, utc_now

router = APIRouter(prefix="/api/staff", tags=["staff"])


@router.get("/users", response_model=list[StaffUserRead])
def list_staff_users(
    _: Annotated[User, Depends(require_admin)],
    session: Session = Depends(database.get_session),
) -> list[StaffUserRead]:
    users = session.exec(select(User).order_by(User.id)).all()
    return [build_user_response(user) for user in users]


@router.post("/users", response_model=StaffUserRead, status_code=status.HTTP_201_CREATED)
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


@router.patch("/users/{user_id}", response_model=StaffUserRead)
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