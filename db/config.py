import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

load_dotenv(BASE_DIR / ".env")

# local = SQLite en data/ (por defecto, sin Docker ni PostgreSQL)
# postgres = PostgreSQL (cuando esté listo: GUIOSPRO_DB_MODE=postgres en .env)
DB_MODE = os.getenv("GUIOSPRO_DB_MODE", "local").lower().strip()

if DB_MODE in ("postgres", "postgresql", "pg"):
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://guiospro:guiospro_secret@localhost:5432/guiospro",
    )
else:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db_file = (DATA_DIR / "guiospro.db").resolve()
    DATABASE_URL = f"sqlite:///{db_file.as_posix()}"


def is_sqlite() -> bool:
    return DATABASE_URL.startswith("sqlite")


def is_postgresql() -> bool:
    return DATABASE_URL.startswith("postgresql")


def storage_label() -> str:
    if is_sqlite():
        return "Local (SQLite)"
    if is_postgresql():
        return "PostgreSQL"
    return "Base de datos"
