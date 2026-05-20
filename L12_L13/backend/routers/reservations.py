from __future__ import annotations

from datetime import date as DateValue
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

import database
from auth import require_manager_or_admin
from models import (
    Reservation,
    ReservationCreate,
    ReservationStatus,
    ReservationUpdate,
    User,
    utc_now,
)

router = APIRouter(prefix="/api/reservations", tags=["reservations"])


@router.get("", response_model=list[Reservation])
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


@router.get("/{reservation_id}", response_model=Reservation)
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


@router.patch("/{reservation_id}", response_model=Reservation)
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


@router.post("", response_model=Reservation, status_code=status.HTTP_201_CREATED)
def create_reservation(
    reservation_request: ReservationCreate,
    session: Session = Depends(database.get_session),
) -> Reservation:
    reservation = Reservation.model_validate(reservation_request)
    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    return reservation
