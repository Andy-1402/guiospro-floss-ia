"""
GUIOSPRO — Evaluación de adopción FLOSS con login, persistencia local e informes.
Ejecutar: streamlit run app.py
"""

from __future__ import annotations

import os

import streamlit as st
from sqlalchemy import select

from auth.service import AuthUser, authenticate, hash_password
from db.models import Organizacion, Usuario
from db.session import get_session
from engine import EvaluationEngine
from guiosad import Guiosad
from services.evaluation_repo import (
    create_evaluation,
    engine_from_evaluation,
    get_evaluation_detail,
    list_evaluations,
    save_engine_to_db,
)
from services.export_report import export_excel, export_pdf
from db.bootstrap import ensure_database_ready
from ui.components import (
    get_org_stats,
    render_dashboard_kpis,
    render_recent_evaluations,
    render_sidebar_brand,
    render_sidebar_user,
)
from ui.styles import CUSTOM_CSS


def _load_runtime_secrets() -> None:
    try:
        secrets = st.secrets
    except Exception:
        return

    for key in (
        "GUIOSPRO_DEMO_USERNAME",
        "GUIOSPRO_DEMO_PASSWORD",
        "GUIOSPRO_DEMO_ROLE",
        "GUIOSPRO_DEMO_NAME",
        "GUIOSPRO_DEMO_EMAIL",
        "GUIOSPRO_USER_COMPANERO_USERNAME",
        "GUIOSPRO_USER_COMPANERO_PASSWORD",
        "GUIOSPRO_USER_COMPANERO_ROLE",
        "GUIOSPRO_USER_COMPANERO_NAME",
        "GUIOSPRO_USER_COMPANERO_EMAIL",
    ):
        value = secrets.get(key)
        if value is not None and not os.getenv(key):
            os.environ[key] = str(value).strip()


_load_runtime_secrets()


def _ensure_users_from_secrets() -> None:
    try:
        secrets = st.secrets
    except Exception:
        return

    user_specs = []

    demo_username = str(secrets.get("GUIOSPRO_DEMO_USERNAME", "")).strip()
    if demo_username:
        user_specs.append(
            {
                "username": demo_username,
                "password": str(secrets.get("GUIOSPRO_DEMO_PASSWORD", "")).strip(),
                "rol": str(secrets.get("GUIOSPRO_DEMO_ROLE", "decisor")).strip().lower() or "decisor",
                "nombre": str(secrets.get("GUIOSPRO_DEMO_NAME", demo_username)).strip() or demo_username,
                "email": str(secrets.get("GUIOSPRO_DEMO_EMAIL", f"{demo_username}@demo.guiospro.local")).strip()
                or f"{demo_username}@demo.guiospro.local",
            }
        )

    companion_username = str(secrets.get("GUIOSPRO_USER_COMPANERO_USERNAME", "")).strip()
    if companion_username:
        user_specs.append(
            {
                "username": companion_username,
                "password": str(secrets.get("GUIOSPRO_USER_COMPANERO_PASSWORD", "")).strip(),
                "rol": str(secrets.get("GUIOSPRO_USER_COMPANERO_ROLE", "decisor")).strip().lower() or "decisor",
                "nombre": str(secrets.get("GUIOSPRO_USER_COMPANERO_NAME", companion_username)).strip() or companion_username,
                "email": str(secrets.get("GUIOSPRO_USER_COMPANERO_EMAIL", f"{companion_username}@demo.guiospro.local")).strip()
                or f"{companion_username}@demo.guiospro.local",
            }
        )

    if not user_specs:
        return

    with get_session() as session:
        org = session.execute(select(Organizacion).where(Organizacion.nombre == "Empresa Demo S.A.")).scalar_one_or_none()
        if not org:
            org = Organizacion(nombre="Empresa Demo S.A.")
            session.add(org)
            session.flush()

        for user_data in user_specs:
            username = user_data["username"]
            existing_user = session.execute(select(Usuario).where(Usuario.username == username)).scalar_one_or_none()
            if existing_user:
                continue

            session.add(
                Usuario(
                    organizacion_id=org.id,
                    username=username,
                    email=user_data["email"],
                    password_hash=hash_password(user_data["password"]),
                    rol=user_data["rol"],
                    nombre_completo=user_data["nombre"],
                    activo=True,
                )
            )

        session.commit()


st.set_page_config(
    page_title="GUIOSPRO | Adopción FLOSS",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def _init_storage() -> str:
    return ensure_database_ready()


def page_login(storage_mode: str) -> None:
    st.markdown(
        """
        <div class="login-hero">
            <h1>GUIOSPRO</h1>
            <p style="margin-top:0.75rem;opacity:0.9;">Plataforma ejecutiva de evaluación de adopción FLOSS</p>
            <p style="font-size:0.85rem;opacity:0.7;margin-top:0.5rem;">Método GUIOSAD · v0.1.2</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        st.markdown("##### Acceso corporativo")
        with st.form("login"):
            user = st.text_input("Usuario")
            pwd = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Ingresar al sistema", type="primary", use_container_width=True)
        if submitted:
            auth = authenticate(user.strip(), pwd)
            if auth:
                st.session_state.user = auth
                st.session_state.page = "Dashboard"
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")
        


def get_user() -> AuthUser:
    return st.session_state.user


def get_engine() -> EvaluationEngine | None:
    eid = st.session_state.get("evaluacion_id")
    if not eid:
        return None
    if st.session_state.get("_engine_cache_id") != eid:
        engine, ev = engine_from_evaluation(eid)
        st.session_state.engine = engine
        st.session_state._engine_cache_id = eid
        st.session_state.project_name = ev.nombre_proyecto
        st.session_state.software_name = ev.software_nombre
    return st.session_state.engine


def invalidate_engine_cache() -> None:
    st.session_state.pop("_engine_cache_id", None)
    st.session_state.pop("engine", None)


def render_eval_context_bar(engine: EvaluationEngine) -> None:
    user = get_user()
    meta = get_evaluation_detail(st.session_state.evaluacion_id) or {}
    counts = engine.summary_counts()
    evaluated = sum(1 for s in engine.factor_states if s.evaluated)
    relevant = len(engine.relevant_factor_indices())

    st.markdown(
        f"""
        <div class="eval-header">
            <h2>{meta.get('software_nombre', 'Evaluación activa')}</h2>
            <p>{meta.get('nombre_proyecto', '')} · Re-evaluación #{meta.get('numero_reevaluacion', 1)}
            · {user.organizacion_nombre}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Factores", len(engine.factor_names))
    c2.metric("Relevantes", relevant)
    c3.metric("Evaluados", f"{evaluated}/{relevant or '—'}")
    c4.metric("Fort. + Oport.", counts["Fortaleza"] + counts["Oportunidad"])
    c5.metric("Deb. + Amen.", counts["Debilidad"] + counts["Amenaza"])


def can_edit() -> bool:
    return get_user().puede_editar and st.session_state.get("evaluacion_estado") == "borrador"


def page_dashboard() -> None:
    user = get_user()
    stats = get_org_stats(user.organizacion_id)

    render_dashboard_kpis(stats)

    st.markdown("---")
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("#### Acciones rápidas")
        if user.puede_editar:
            with st.container(border=True):
                st.markdown("**Nueva evaluación**")
                c1, c2 = st.columns(2)
                with c1:
                    proj = st.text_input("Proyecto", value="Evaluación FLOSS", key="dash_proj")
                with c2:
                    sw = st.text_input("Software FLOSS", placeholder="Ej. Odoo", key="dash_sw")
                if st.button("Iniciar evaluación", type="primary", use_container_width=True) and sw:
                    eid = create_evaluation(user, proj, sw.strip())
                    st.session_state.evaluacion_id = eid
                    st.session_state.evaluacion_estado = "borrador"
                    invalidate_engine_cache()
                    st.session_state.page = "Paso 1-2"
                    st.rerun()
        else:
            st.info("Su rol permite consultar evaluaciones e informes.")

        if st.button("Ver historial de consultas", use_container_width=True, type="secondary"):
            st.session_state.page = "Historial"
            st.rerun()

    with col_right:
        render_recent_evaluations(stats["items"])


def page_historial() -> None:
    user = get_user()

    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("← Dashboard", use_container_width=True):
            st.session_state.page = "Dashboard"
            st.rerun()
    with col_title:
        st.markdown(
            """
            <div class="hist-panel" style="margin-bottom:1rem;padding:1rem 1.5rem;">
                <h2 style="margin:0;color:#0c1222;font-size:1.5rem;">Historial de consultas</h2>
                <p style="margin:0.35rem 0 0 0;color:#64748b;">Evaluaciones, informes y re-evaluaciones por software</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="hist-panel">', unsafe_allow_html=True)

    filtro = st.text_input("Buscar software", placeholder="Filtrar por nombre…", label_visibility="collapsed")
    items = list_evaluations(user.organizacion_id, filtro or None)

    if not items:
        st.info("No hay evaluaciones registradas.")
    else:
        for it in items:
            estado = it["estado"]
            badge = "badge-completada" if estado == "completada" else "badge-borrador"
            fecha = it["updated_at"].strftime("%d/%m/%Y %H:%M") if it.get("updated_at") else ""
            col_a, col_b, col_c = st.columns([4, 2, 2])
            with col_a:
                st.markdown(
                    f'<div class="hist-row"><strong>{it["software_nombre"]}</strong> — {it["nombre_proyecto"]}<br>'
                    f'<span class="{badge}">{estado}</span> '
                    f'<span style="color:#94a3b8;font-size:0.85rem;">Re-eval. #{it["numero_reevaluacion"]} · {fecha}</span></div>',
                    unsafe_allow_html=True,
                )
            with col_b:
                if it.get("decision_adoptar") is not None:
                    st.caption("✓ Adoptar" if it["decision_adoptar"] else "✗ Revisar / No adoptar")
            with col_c:
                if st.button("Abrir", key=f"open_{it['id']}", use_container_width=True):
                    st.session_state.evaluacion_id = it["id"]
                    st.session_state.evaluacion_estado = it["estado"]
                    invalidate_engine_cache()
                    st.session_state.page = "Paso 1-2" if it["estado"] == "borrador" else "Paso 5-6"
                    st.rerun()
                if it["estado"] == "completada":
                    try:
                        pdf = export_pdf(it["id"])
                        st.download_button("PDF", pdf, file_name=f"informe_{it['id']}.pdf",
                                           mime="application/pdf", key=f"dl_{it['id']}")
                    except Exception:
                        pass

    st.markdown("</div>", unsafe_allow_html=True)

    if user.puede_editar:
        st.markdown("---")
        st.markdown("#### Re-evaluación")
        completadas = [i for i in items if i["estado"] == "completada"]
        if completadas:
            opts = {
                f"{i['software_nombre']} (#{i['id']}, re-eval. {i['numero_reevaluacion']})": i["id"]
                for i in completadas
            }
            sel = st.selectbox("Basada en evaluación anterior", list(opts.keys()))
            if st.button("Crear re-evaluación"):
                padre_id = opts[sel]
                padre = next(i for i in completadas if i["id"] == padre_id)
                eid = create_evaluation(
                    user,
                    f"{padre['nombre_proyecto']} — Re-evaluación",
                    padre["software_nombre"],
                    evaluacion_padre_id=padre_id,
                )
                st.session_state.evaluacion_id = eid
                st.session_state.evaluacion_estado = "borrador"
                invalidate_engine_cache()
                st.session_state.page = "Paso 1-2"
                st.rerun()


def _save_draft() -> None:
    engine = get_engine()
    if engine and st.session_state.evaluacion_id:
        save_engine_to_db(st.session_state.evaluacion_id, engine, get_user(), completar=False)
        invalidate_engine_cache()
        st.toast("Borrador guardado.")


def page_factores() -> None:
    engine = get_engine()
    if not engine:
        st.warning("Seleccione una evaluación desde el historial o cree una nueva.")
        return
    edit = can_edit()
    st.markdown(
        '<div class="step-card"><h3>Paso 1 y 2 — Factores relevantes</h3>'
        "<p>Importancia del decisor y alcance interno/externo.</p></div>",
        unsafe_allow_html=True,
    )
    for i, name in enumerate(engine.factor_names):
        factor = engine.model.factors[i]
        state = engine.factor_states[i]
        rel_label, is_relevant = engine.relative_importance(i)
        raw_scope = engine.raw_scope(i)
        with st.expander(f"{name} — {rel_label}" + (" · Relevante" if is_relevant else "")):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.caption("Dimensión")
                st.write(getattr(factor.dimension, "name", "—"))
                st.write(engine.suggested_label(i))
            with c2:
                if edit:
                    state.decisor_importance = st.select_slider(
                        "Decisor", options=[1, 2, 3, 4], value=state.decisor_importance,
                        format_func=lambda v: Guiosad.levels_lbls[v - 1],
                        key=f"dec_{i}_{st.session_state.evaluacion_id}",
                    )
                else:
                    st.write(Guiosad.levels_lbls[state.decisor_importance - 1])
            with c3:
                st.markdown(f"**{rel_label}**")
            with c4:
                if raw_scope in ("Interno", "Externo"):
                    state.scope = raw_scope
                    st.write(raw_scope)
                elif edit:
                    state.scope = st.radio("Alcance", ["Interno", "Externo"],
                        index=0 if state.scope == "Interno" else 1,
                        key=f"sc_{i}_{st.session_state.evaluacion_id}", horizontal=True)
                else:
                    st.write(state.scope)
    if edit and st.button("Guardar borrador", type="primary"):
        _save_draft()


def page_subfactores() -> None:
    engine = get_engine()
    if not engine:
        return
    edit = can_edit()
    relevant = engine.relevant_factor_indices()
    if not relevant:
        st.warning("No hay factores relevantes. Complete el Paso 1-2.")
        return
    st.markdown(
        '<div class="step-card"><h3>Paso 3 y 4 — Subfactores</h3>'
        "<p>Cumplimiento de cada criterio.</p></div>",
        unsafe_allow_html=True,
    )
    names = [engine.factor_names[i] for i in relevant]
    selected = st.selectbox("Factor", names)
    idx = engine.factor_names.index(selected)
    state = engine.factor_states[idx]
    subs = engine.model.subfactors_list[idx]
    new_values: list[int] = []
    for j, sf_name in enumerate(subs):
        col_a, col_b = st.columns([3, 2])
        with col_a:
            st.markdown(f"**{j + 1}.** {sf_name}")
        with col_b:
            if edit:
                val = st.select_slider(
                    "Cumplimiento", options=[1, 2, 3, 4],
                    value=state.subfactor_values[j] if j < len(state.subfactor_values) else 1,
                    format_func=lambda v: Guiosad.sub_levels_lbls[v - 1],
                    key=f"sub_{idx}_{j}_{st.session_state.evaluacion_id}",
                    label_visibility="collapsed",
                )
            else:
                val = state.subfactor_values[j] if j < len(state.subfactor_values) else 1
                st.write(Guiosad.sub_levels_lbls[val - 1])
            new_values.append(val)
    if edit and st.button("Guardar factor y borrador", type="primary"):
        engine.save_subfactors(idx, new_values)
        _save_draft()
        st.success(f"Ponderación {state.global_weight:.1f} · FODA: {state.foda}")


def page_foda() -> None:
    engine = get_engine()
    if not engine:
        return
    edit = can_edit()
    eid = st.session_state.evaluacion_id
    rows = []
    for i, name in enumerate(engine.factor_names):
        status = engine.foda_row_status(i)
        state = engine.factor_states[i]
        rel_label, _ = engine.relative_importance(i)
        foda_txt = state.foda if status == "done" else ("Pendiente" if status == "pending" else "No relevante")
        rows.append({
            "Factor": name, "Importancia relativa": rel_label,
            "Ponderación": f"{state.global_weight:.1f}" if state.global_weight else "—",
            "Alcance": state.scope, "FODA": foda_txt,
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
    counts = engine.summary_counts()
    cols = st.columns(4)
    for col, label in zip(cols, ["Fortaleza", "Oportunidad", "Debilidad", "Amenaza"]):
        col.metric(label, counts[label])
    st.divider()
    meta = get_evaluation_detail(eid) or {}
    if edit and st.button("Completar evaluación", type="primary"):
        text, style = engine.compute_recommendation()
        save_engine_to_db(eid, engine, get_user(), completar=True)
        st.session_state.evaluacion_estado = "completada"
        st.session_state.recommendation = text
        st.session_state.recommendation_style = style
        invalidate_engine_cache()
        st.rerun()
    rec = st.session_state.get("recommendation") or meta.get("recomendacion_texto")
    style = st.session_state.get("recommendation_style") or meta.get("recomendacion_tipo") or "neutral"
    if rec:
        css = {"success": "rec-success", "warning": "rec-warning", "error": "rec-error"}.get(style, "step-card")
        st.markdown(f'<div class="{css}"><strong>Recomendación</strong><br><br>{rec}</div>', unsafe_allow_html=True)
    if meta.get("estado") == "completada" or st.session_state.evaluacion_estado == "completada":
        st.markdown("#### Informe para el cliente")
        try:
            pdf = export_pdf(eid)
            xlsx = export_excel(eid)
            c1, c2 = st.columns(2)
            sw = meta.get("software_nombre", "software")
            rev = meta.get("numero_reevaluacion", 1)
            c1.download_button("PDF", pdf, file_name=f"Informe_{sw}_v{rev}.pdf", mime="application/pdf", use_container_width=True)
            c2.download_button("Excel", xlsx, file_name=f"Informe_{sw}_v{rev}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        except Exception as ex:
            st.error(str(ex))


def render_sidebar(user: AuthUser, storage_mode: str) -> None:
    render_sidebar_brand()
    render_sidebar_user(user)
    if user.solo_lectura:
        st.caption("Modo consulta — solo lectura")

    st.markdown("---")
    st.markdown('<p style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.12em;color:#94a3b8;">Navegación</p>', unsafe_allow_html=True)

    if st.button("Panel ejecutivo", use_container_width=True,
                 type="primary" if st.session_state.page == "Dashboard" else "secondary"):
        st.session_state.page = "Dashboard"
        st.rerun()

    if st.button("Historial de consultas", use_container_width=True,
                 type="primary" if st.session_state.page == "Historial" else "secondary"):
        st.session_state.page = "Historial"
        st.rerun()

    if st.session_state.get("evaluacion_id"):
        st.markdown("---")
        st.markdown('<p style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.12em;color:#94a3b8;">Evaluación activa</p>', unsafe_allow_html=True)
        step_labels = {
            "Paso 1-2": "① Factores",
            "Paso 3-4": "② Subfactores",
            "Paso 5-6": "③ FODA e informe",
        }
        steps = ["Paso 1-2", "Paso 3-4", "Paso 5-6"]
        current = st.session_state.page if st.session_state.page in steps else "Paso 1-2"
        choice = st.radio(
            "Pasos",
            steps,
            format_func=lambda p: step_labels[p],
            index=steps.index(current),
            label_visibility="collapsed",
        )
        if choice != st.session_state.page:
            st.session_state.page = choice
            st.rerun()

        if user.puede_editar:
            if st.button("Guardar borrador", use_container_width=True):
                eng = get_engine()
                if eng:
                    save_engine_to_db(st.session_state.evaluacion_id, eng, user, completar=False)
                    invalidate_engine_cache()
                    st.toast("Guardado.")

    st.markdown("---")
    st.caption(f"◆ {storage_mode}")
    if st.button("Cerrar sesión", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


def main() -> None:
    try:
        storage_mode = _init_storage()
        _ensure_users_from_secrets()
    except Exception as e:
        st.error(f"Error de almacenamiento: {e}")
        st.stop()

    if "user" not in st.session_state:
        page_login(storage_mode)
        st.stop()

    user = get_user()
    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"

    with st.sidebar:
        render_sidebar(user, storage_mode)

    page = st.session_state.page

    if page == "Dashboard":
        page_dashboard()
    elif page == "Historial":
        page_historial()
    elif page in ("Paso 1-2", "Paso 3-4", "Paso 5-6"):
        eng = get_engine()
        if not st.session_state.get("evaluacion_id"):
            st.warning("Seleccione una evaluación o cree una nueva desde el Dashboard.")
        elif eng:
            render_eval_context_bar(eng)
            if page == "Paso 1-2":
                page_factores()
            elif page == "Paso 3-4":
                page_subfactores()
            else:
                page_foda()
    else:
        st.session_state.page = "Dashboard"
        st.rerun()


if __name__ == "__main__":
    main()
