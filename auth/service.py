"""Autenticación de usuarios."""

from __future__ import annotations

from dataclasses import dataclass

import bcrypt
from sqlalchemy import select

from db.models import Usuario
from db.session import get_session


@dataclass
class AuthUser:
    id: int
    username: str
    rol: str
    organizacion_id: int
    organizacion_nombre: str
    nombre_completo: str | None

    @property
    def puede_editar(self) -> bool:
        return self.rol in ("admin", "decisor")

    @property
    def solo_lectura(self) -> bool:
        return self.rol == "consultor"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def authenticate(username: str, password: str) -> AuthUser | None:
    with get_session() as session:
        user = session.execute(
            select(Usuario).where(Usuario.username == username, Usuario.activo.is_(True))
        ).scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            return None
        org = user.organizacion
        return AuthUser(
            id=user.id,
            username=user.username,
            rol=user.rol,
            organizacion_id=user.organizacion_id,
            organizacion_nombre=org.nombre,
            nombre_completo=user.nombre_completo,
        )
