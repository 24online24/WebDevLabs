from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from auth import (
    INITIAL_ADMIN_EMAIL,
    INITIAL_ADMIN_PASSWORD,
    INITIAL_MANAGER_EMAIL,
    INITIAL_MANAGER_PASSWORD,
    create_user,
)
from models import MenuItem, User, UserRole


def read_json_file(path: Path, default_value: Any | None = None) -> Any:
    if not path.exists():
        if default_value is None:
            raise FileNotFoundError(f"Expected data file at {path}")

        path.write_text(json.dumps(default_value, indent=2) + "\n", encoding="utf-8")
        return default_value

    return json.loads(path.read_text(encoding="utf-8"))


def seed_menu_items(session: Session, menu_file: Path) -> None:
    existing_item = session.exec(select(MenuItem).limit(1)).first()
    if existing_item is not None:
        return

    raw_items = read_json_file(menu_file)
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
