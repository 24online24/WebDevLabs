from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlmodel import Session, create_engine

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE_FILE = BASE_DIR / "coffee_shop.db"


def build_database_url(database_file: Path) -> str:
    return f"sqlite:///{database_file}"


DATABASE_FILE = DEFAULT_DATABASE_FILE
DATABASE_URL = build_database_url(DATABASE_FILE)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


def configure_engine(database_file: Path | None = None) -> None:
    global DATABASE_FILE, DATABASE_URL, engine

    engine.dispose()
    DATABASE_FILE = database_file or DEFAULT_DATABASE_FILE
    DATABASE_URL = build_database_url(DATABASE_FILE)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
