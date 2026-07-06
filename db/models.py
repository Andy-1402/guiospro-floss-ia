"""Modelos SQLAlchemy para GUIOSPRO."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Organizacion(Base):
    __tablename__ = "organizaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="organizacion")
    evaluaciones: Mapped[list["Evaluacion"]] = relationship(back_populates="organizacion")


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    organizacion_id: Mapped[int] = mapped_column(ForeignKey("organizaciones.id"))
    username: Mapped[str] = mapped_column(String(80), unique=True)
    email: Mapped[str | None] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(String(20))
    nombre_completo: Mapped[str | None] = mapped_column(String(200))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organizacion: Mapped["Organizacion"] = relationship(back_populates="usuarios")


class Dimension(Base):
    __tablename__ = "dimensiones"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    factores: Mapped[list["Factor"]] = relationship(back_populates="dimension")


class Factor(Base):
    __tablename__ = "factores"

    id: Mapped[int] = mapped_column(primary_key=True)
    dimension_id: Mapped[int] = mapped_column(ForeignKey("dimensiones.id"))
    nombre: Mapped[str] = mapped_column(String(150))
    importancia_sugerida: Mapped[int] = mapped_column(SmallInteger)
    alcance_catalogo: Mapped[str] = mapped_column(String(20))
    orden: Mapped[int] = mapped_column(SmallInteger, default=0)

    dimension: Mapped["Dimension"] = relationship(back_populates="factores")
    subfactores: Mapped[list["Subfactor"]] = relationship(back_populates="factor")

    __table_args__ = (UniqueConstraint("dimension_id", "nombre"),)


class Subfactor(Base):
    __tablename__ = "subfactores"

    id: Mapped[int] = mapped_column(primary_key=True)
    factor_id: Mapped[int] = mapped_column(ForeignKey("factores.id"))
    descripcion: Mapped[str] = mapped_column(Text)
    orden: Mapped[int] = mapped_column(SmallInteger, default=0)

    factor: Mapped["Factor"] = relationship(back_populates="subfactores")


class Evaluacion(Base):
    __tablename__ = "evaluaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    organizacion_id: Mapped[int] = mapped_column(ForeignKey("organizaciones.id"))
    creado_por: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    nombre_proyecto: Mapped[str] = mapped_column(String(200))
    software_nombre: Mapped[str] = mapped_column(String(200))
    estado: Mapped[str] = mapped_column(String(20), default="borrador")
    numero_reevaluacion: Mapped[int] = mapped_column(Integer, default=1)
    evaluacion_padre_id: Mapped[int | None] = mapped_column(ForeignKey("evaluaciones.id"))
    recomendacion_texto: Mapped[str | None] = mapped_column(Text)
    recomendacion_tipo: Mapped[str | None] = mapped_column(String(20))
    decision_adoptar: Mapped[bool | None] = mapped_column(Boolean)
    notas: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    organizacion: Mapped["Organizacion"] = relationship(back_populates="evaluaciones")
    factores_resp: Mapped[list["EvaluacionFactor"]] = relationship(
        back_populates="evaluacion", cascade="all, delete-orphan"
    )
    subfactores_resp: Mapped[list["EvaluacionSubfactor"]] = relationship(
        back_populates="evaluacion", cascade="all, delete-orphan"
    )


class EvaluacionFactor(Base):
    __tablename__ = "evaluacion_factores"

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluacion_id: Mapped[int] = mapped_column(ForeignKey("evaluaciones.id", ondelete="CASCADE"))
    factor_id: Mapped[int] = mapped_column(ForeignKey("factores.id"))
    importancia_decisor: Mapped[int] = mapped_column(SmallInteger, default=1)
    importancia_relativa: Mapped[str | None] = mapped_column(String(30))
    alcance: Mapped[str] = mapped_column(String(20), default="Interno")
    ponderacion_global: Mapped[float | None] = mapped_column(Numeric(4, 2))
    foda: Mapped[str | None] = mapped_column(String(30))
    evaluado: Mapped[bool] = mapped_column(Boolean, default=False)

    evaluacion: Mapped["Evaluacion"] = relationship(back_populates="factores_resp")
    factor: Mapped["Factor"] = relationship()

    __table_args__ = (UniqueConstraint("evaluacion_id", "factor_id"),)


class EvaluacionSubfactor(Base):
    __tablename__ = "evaluacion_subfactores"

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluacion_id: Mapped[int] = mapped_column(ForeignKey("evaluaciones.id", ondelete="CASCADE"))
    subfactor_id: Mapped[int] = mapped_column(ForeignKey("subfactores.id"))
    valor: Mapped[int] = mapped_column(SmallInteger, default=1)

    evaluacion: Mapped["Evaluacion"] = relationship(back_populates="subfactores_resp")
    subfactor: Mapped["Subfactor"] = relationship()

    __table_args__ = (UniqueConstraint("evaluacion_id", "subfactor_id"),)


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    evaluacion_id: Mapped[int | None] = mapped_column(ForeignKey("evaluaciones.id", ondelete="SET NULL"))
    accion: Mapped[str] = mapped_column(String(50))
    entidad: Mapped[str | None] = mapped_column(String(50))
    entidad_id: Mapped[int | None] = mapped_column(Integer)
    detalle: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
