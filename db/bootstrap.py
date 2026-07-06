"""Inicializa almacenamiento local o PostgreSQL (tablas + datos demo)."""

from __future__ import annotations

import os

from auth.service import hash_password
from db.config import storage_label
from db.models import Organizacion, Usuario
from db.session import get_session, init_tables
from services.catalog import seed_catalog_if_empty
from sqlalchemy import select

_bootstrapped = False
_bootstrapped_signature: tuple[str, ...] | None = None


DEFAULT_USERS = [
    ("decisor", "Decisor2025!", "decisor", "Jefferson Zambrano", "decisor@demo.guiospro.local"),
    ("jzambrano", "123456", "decisor", "Jefferson Zambrano", "jzambrano@guiospro.local"),
    ("consultor", "Consultor2025!", "consultor", "Luis Pérez — Consultor", "consultor@demo.guiospro.local"),
    ("admin", "Admin2025!", "admin", "Admin Sistema", "admin@demo.guiospro.local"),
]


def _upsert_user(session, org: Organizacion, username: str, password: str, rol: str, nombre: str, email: str) -> None:
    user = session.execute(select(Usuario).where(Usuario.username == username)).scalar_one_or_none()
    password_hash = hash_password(password)
    if user:
        user.organizacion_id = org.id
        user.email = email
        user.password_hash = password_hash
        user.rol = rol
        user.nombre_completo = nombre
        user.activo = True
        return

    session.add(
        Usuario(
            organizacion_id=org.id,
            username=username,
            email=email,
            password_hash=password_hash,
            rol=rol,
            nombre_completo=nombre,
        )
    )


def seed_users() -> None:
    with get_session() as session:
        org = session.execute(
            select(Organizacion).where(Organizacion.nombre == "Empresa Demo S.A.")
        ).scalar_one_or_none()
        if not org:
            org = Organizacion(nombre="Empresa Demo S.A.")
            session.add(org)
            session.flush()

        demo_username = os.getenv("GUIOSPRO_DEMO_USERNAME", "").strip()
        demo_password = os.getenv("GUIOSPRO_DEMO_PASSWORD", "").strip()
        if demo_username and demo_password:
            demo_role = os.getenv("GUIOSPRO_DEMO_ROLE", "decisor").strip().lower() or "decisor"
            demo_name = os.getenv("GUIOSPRO_DEMO_NAME", "").strip() or demo_username
            demo_email = os.getenv("GUIOSPRO_DEMO_EMAIL", "").strip() or f"{demo_username}@demo.guiospro.local"
            _upsert_user(session, org, demo_username, demo_password, demo_role, demo_name, demo_email)

        for username, password, rol, nombre, email in DEFAULT_USERS:
            _upsert_user(session, org, username, password, rol, nombre, email)

        session.commit()


def _current_signature() -> tuple[str, ...]:
    return (
        os.getenv("GUIOSPRO_DEMO_USERNAME", "").strip(),
        os.getenv("GUIOSPRO_DEMO_PASSWORD", "").strip(),
        os.getenv("GUIOSPRO_DEMO_ROLE", "").strip().lower(),
        os.getenv("GUIOSPRO_DEMO_NAME", "").strip(),
        os.getenv("GUIOSPRO_DEMO_EMAIL", "").strip(),
    )


def ensure_database_ready() -> str:
    """
    Crea tablas y datos iniciales si hace falta.
    Devuelve etiqueta del modo de almacenamiento.
    """
    global _bootstrapped
    global _bootstrapped_signature
    signature = _current_signature()
    if _bootstrapped and _bootstrapped_signature == signature:
        return storage_label()

    init_tables()
    seed_catalog_if_empty()
    seed_users()
    _bootstrapped = True
    _bootstrapped_signature = signature
    return storage_label()
