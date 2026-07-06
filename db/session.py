from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from db.config import DATABASE_URL, is_sqlite
from db.models import Base

_connect_args = {"check_same_thread": False} if is_sqlite() else {}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=not is_sqlite(),
    connect_args=_connect_args,
)

# SQLite: claves foráneas activas
if is_sqlite():

    @event.listens_for(engine, "connect")
    def _sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session() -> Session:
    return SessionLocal()


def init_tables() -> None:
    Base.metadata.create_all(bind=engine)
