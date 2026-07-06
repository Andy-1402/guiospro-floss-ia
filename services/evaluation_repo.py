"""Persistencia de evaluaciones en PostgreSQL."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, desc, select
from sqlalchemy.orm import joinedload

from auth.service import AuthUser
from db.models import Evaluacion, EvaluacionFactor, EvaluacionSubfactor, Factor, Subfactor
from db.session import get_session
from engine import EvaluationEngine, FactorState
from guiosad import Guiosad
from services.audit import log_action


class DbGuiosadModel:
    """Adaptador del catálogo en BD con la interfaz que espera EvaluationEngine."""

    levels_lbls = Guiosad.levels_lbls
    sub_levels_lbls = Guiosad.sub_levels_lbls

    def __init__(self, factors: list[Factor]):
        self.factors = []
        self.factors_lbls = []
        self.subfactors_list = []
        self._db_factors = factors
        for f in factors:
            self.factors_lbls.append(f.nombre)
            class _F:
                pass

            fo = _F()
            fo.name = f.nombre
            fo.suggested_importance = f.importancia_sugerida
            fo.scope = f.alcance_catalogo
            fo.dimension = type("D", (), {"name": f.dimension.nombre})()
            fo.subfactors = []
            subs = sorted(f.subfactores, key=lambda s: s.orden)
            self.subfactors_list.append([s.descripcion for s in subs])
            for s in subs:
                sf = type("S", (), {"name": s.descripcion})()
                fo.subfactors.append(sf)
            self.factors.append(fo)


def _load_factors_ordered(session) -> list[Factor]:
    return list(
        session.execute(
            select(Factor)
            .options(
                joinedload(Factor.dimension),
                joinedload(Factor.subfactores),
            )
            .order_by(Factor.orden, Factor.id)
        )
        .scalars()
        .unique()
        .all()
    )


def create_engine_from_db() -> EvaluationEngine:
    with get_session() as session:
        factors = _load_factors_ordered(session)
    model = DbGuiosadModel(factors)
    return EvaluationEngine(model=model)


def engine_from_evaluation(evaluacion_id: int) -> tuple[EvaluationEngine, Evaluacion]:
    with get_session() as session:
        ev = session.get(
            Evaluacion,
            evaluacion_id,
            options=[
                joinedload(Evaluacion.factores_resp),
                joinedload(Evaluacion.subfactores_resp),
            ],
        )
        if not ev:
            raise ValueError("Evaluación no encontrada")
        factors = _load_factors_ordered(session)
        model = DbGuiosadModel(factors)
        engine = EvaluationEngine(model=model)

        factor_id_to_idx = {f.id: i for i, f in enumerate(factors)}
        sub_id_to_val = {r.subfactor_id: r.valor for r in ev.subfactores_resp}

        for fr in ev.factores_resp:
            idx = factor_id_to_idx.get(fr.factor_id)
            if idx is None:
                continue
            st = engine.factor_states[idx]
            st.decisor_importance = fr.importancia_decisor
            st.scope = fr.alcance
            st.global_weight = float(fr.ponderacion_global) if fr.ponderacion_global else None
            st.foda = fr.foda or ""
            st.evaluated = fr.evaluado
            db_factor = factors[idx]
            st.subfactor_values = []
            for sf in sorted(db_factor.subfactores, key=lambda x: x.orden):
                st.subfactor_values.append(sub_id_to_val.get(sf.id, 1))

        return engine, ev


def create_evaluation(
    user: AuthUser,
    nombre_proyecto: str,
    software_nombre: str,
    evaluacion_padre_id: int | None = None,
) -> int:
    with get_session() as session:
        numero = 1
        if evaluacion_padre_id:
            padre = session.get(Evaluacion, evaluacion_padre_id)
            if padre:
                numero = padre.numero_reevaluacion + 1

        ev = Evaluacion(
            organizacion_id=user.organizacion_id,
            creado_por=user.id,
            nombre_proyecto=nombre_proyecto,
            software_nombre=software_nombre,
            estado="borrador",
            numero_reevaluacion=numero,
            evaluacion_padre_id=evaluacion_padre_id,
        )
        session.add(ev)
        session.flush()

        factors = _load_factors_ordered(session)
        for f in factors:
            alcance = f.alcance_catalogo if f.alcance_catalogo != "Ambos" else "Interno"
            session.add(
                EvaluacionFactor(
                    evaluacion_id=ev.id,
                    factor_id=f.id,
                    importancia_decisor=1,
                    alcance=alcance,
                )
            )
        session.commit()
        log_action(
            user.id,
            "crear_evaluacion",
            ev.id,
            "evaluacion",
            ev.id,
            {"software": software_nombre, "reevaluacion": numero},
        )
        return ev.id


def save_engine_to_db(
    evaluacion_id: int,
    engine: EvaluationEngine,
    user: AuthUser,
    completar: bool = False,
) -> None:
    with get_session() as session:
        ev = session.get(
            Evaluacion,
            evaluacion_id,
            options=[joinedload(Evaluacion.factores_resp)],
        )
        if not ev:
            raise ValueError("Evaluación no encontrada")

        factors = _load_factors_ordered(session)
        factor_id_by_idx = {i: f.id for i, f in enumerate(factors)}
        sub_ids_by_idx = {
            i: [s.id for s in sorted(f.subfactores, key=lambda x: x.orden)]
            for i, f in enumerate(factors)
        }

        fr_map = {r.factor_id: r for r in ev.factores_resp}

        for i, st in enumerate(engine.factor_states):
            fid = factor_id_by_idx[i]
            rel_label, _ = engine.relative_importance(i)
            fr = fr_map.get(fid)
            if not fr:
                fr = EvaluacionFactor(evaluacion_id=ev.id, factor_id=fid)
                session.add(fr)
                fr_map[fid] = fr
            fr.importancia_decisor = st.decisor_importance
            fr.importancia_relativa = rel_label
            fr.alcance = st.scope
            fr.ponderacion_global = st.global_weight
            fr.foda = st.foda or None
            fr.evaluado = st.evaluated

        session.execute(
            delete(EvaluacionSubfactor).where(EvaluacionSubfactor.evaluacion_id == ev.id)
        )

        for i, st in enumerate(engine.factor_states):
            for sid, val in zip(sub_ids_by_idx[i], st.subfactor_values):
                session.add(
                    EvaluacionSubfactor(
                        evaluacion_id=ev.id,
                        subfactor_id=sid,
                        valor=val,
                    )
                )

        if completar:
            text, style = engine.compute_recommendation()
            ev.recomendacion_texto = text
            ev.recomendacion_tipo = style
            ev.decision_adoptar = style == "success"
            ev.estado = "completada"
            ev.completed_at = datetime.now(timezone.utc)

        session.commit()
        log_action(
            user.id,
            "completar_evaluacion" if completar else "guardar_borrador",
            ev.id,
            "evaluacion",
            ev.id,
        )


def list_evaluations(org_id: int, software: str | None = None) -> list[dict]:
    with get_session() as session:
        q = select(Evaluacion).where(Evaluacion.organizacion_id == org_id)
        if software:
            q = q.where(Evaluacion.software_nombre.ilike(f"%{software}%"))
        q = q.order_by(desc(Evaluacion.updated_at))
        rows = session.execute(q).scalars().all()
        return [
            {
                "id": e.id,
                "nombre_proyecto": e.nombre_proyecto,
                "software_nombre": e.software_nombre,
                "estado": e.estado,
                "numero_reevaluacion": e.numero_reevaluacion,
                "evaluacion_padre_id": e.evaluacion_padre_id,
                "recomendacion_tipo": e.recomendacion_tipo,
                "decision_adoptar": e.decision_adoptar,
                "updated_at": e.updated_at,
                "completed_at": e.completed_at,
            }
            for e in rows
        ]


def get_evaluation_detail(evaluacion_id: int) -> dict | None:
    with get_session() as session:
        ev = session.get(Evaluacion, evaluacion_id)
        if not ev:
            return None
        return {
            "id": ev.id,
            "nombre_proyecto": ev.nombre_proyecto,
            "software_nombre": ev.software_nombre,
            "estado": ev.estado,
            "numero_reevaluacion": ev.numero_reevaluacion,
            "recomendacion_texto": ev.recomendacion_texto,
            "recomendacion_tipo": ev.recomendacion_tipo,
            "decision_adoptar": ev.decision_adoptar,
        }
