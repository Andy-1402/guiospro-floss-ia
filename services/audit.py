"""Registro de auditoría."""

from __future__ import annotations

from typing import Any

from db.models import Auditoria
from db.session import get_session


def log_action(
    usuario_id: int | None,
    accion: str,
    evaluacion_id: int | None = None,
    entidad: str | None = None,
    entidad_id: int | None = None,
    detalle: dict[str, Any] | None = None,
) -> None:
    with get_session() as session:
        session.add(
            Auditoria(
                usuario_id=usuario_id,
                evaluacion_id=evaluacion_id,
                accion=accion,
                entidad=entidad,
                entidad_id=entidad_id,
                detalle=detalle,
            )
        )
        session.commit()
