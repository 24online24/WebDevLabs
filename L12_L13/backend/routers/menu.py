from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, select

import database
from auth import require_admin
from models import MenuItem, MenuItemCreate, MenuItemUpdate, User

router = APIRouter(prefix="/api/menu", tags=["menu"])


@router.get("", response_model=list[MenuItem])
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


@router.post("", response_model=MenuItem, status_code=status.HTTP_201_CREATED)
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


@router.get("/{item_id}", response_model=MenuItem)
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


@router.put("/{item_id}", response_model=MenuItem)
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


@router.delete("/{item_id}")
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