#!/usr/bin/env python3
"""
Crea o actualiza un usuario en GUIOSPRO.
Uso:
  python scripts/create_user.py jzambrano 123456 --nombre "Jefferson Zambrano"
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from auth.service import hash_password
from db.models import Organizacion, Usuario
from db.session import get_session, init_tables
from sqlalchemy import select


def create_or_update_user(
    username: str,
    password: str,
    rol: str = "decisor",
    nombre_completo: str | None = None,
    organizacion: str = "Empresa Demo S.A.",
    email: str | None = None,
) -> None:
    init_tables()

    with get_session() as session:
        org = session.execute(
            select(Organizacion).where(Organizacion.nombre == organizacion)
        ).scalar_one_or_none()
        if not org:
            org = Organizacion(nombre=organizacion)
            session.add(org)
            session.flush()

        user = session.execute(
            select(Usuario).where(Usuario.username == username)
        ).scalar_one_or_none()

        pwd_hash = hash_password(password)
        display = nombre_completo or username
        mail = email or f"{username}@guiospro.local"

        if user:
            user.password_hash = pwd_hash
            user.rol = rol
            user.nombre_completo = display
            user.email = mail
            user.activo = True
            action = "actualizado"
        else:
            session.add(
                Usuario(
                    organizacion_id=org.id,
                    username=username,
                    email=mail,
                    password_hash=pwd_hash,
                    rol=rol,
                    nombre_completo=display,
                    activo=True,
                )
            )
            action = "creado"

        session.commit()
        print(f"Usuario {action}: {username} ({display}) · rol: {rol}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crear usuario GUIOSPRO")
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("--rol", default="decisor", choices=["decisor", "consultor", "admin"])
    parser.add_argument("--nombre", default=None, help="Nombre completo")
    parser.add_argument("--org", default="Empresa Demo S.A.")
    args = parser.parse_args()

    create_or_update_user(
        username=args.username,
        password=args.password,
        rol=args.rol,
        nombre_completo=args.nombre,
        organizacion=args.org,
    )
