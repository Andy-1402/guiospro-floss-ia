"""Componentes UI reutilizables — estilo ejecutivo."""

from __future__ import annotations

import streamlit as st

from auth.service import AuthUser
from services.evaluation_repo import list_evaluations


def render_sidebar_brand() -> None:
    st.markdown(
        """
        <p class="exec-brand">GUIOSPRO</p>
        <p class="exec-brand-sub">Adopción FLOSS · GUIOSAD</p>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_user(user: AuthUser) -> None:
    rol_label = {"decisor": "Decisor", "consultor": "Consultor", "admin": "Administrador"}.get(
        user.rol, user.rol
    )
    st.markdown(
        f"""
        <div class="exec-user-card">
            <div class="exec-user-name">{user.nombre_completo or user.username}</div>
            <div style="color:#94a3b8;font-size:0.8rem;margin-top:2px;">{user.organizacion_nombre}</div>
            <span class="exec-user-role">{rol_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_org_stats(org_id: int) -> dict:
    items = list_evaluations(org_id)
    total = len(items)
    completadas = sum(1 for i in items if i["estado"] == "completada")
    borradores = sum(1 for i in items if i["estado"] == "borrador")
    adoptar = sum(1 for i in items if i.get("decision_adoptar") is True)
    ultimo = items[0]["software_nombre"] if items else "—"
    return {
        "total": total,
        "completadas": completadas,
        "borradores": borradores,
        "adoptar": adoptar,
        "ultimo_software": ultimo,
        "items": items,
    }


def render_dashboard_kpis(stats: dict) -> None:
    st.markdown(
        """
        <div class="dash-hero">
            <h1>Panel ejecutivo</h1>
            <p>Visión general de evaluaciones de adopción FLOSS en su organización</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4, c5 = st.columns(5)
    kpis = [
        (str(stats["total"]), "Evaluaciones totales", ""),
        (str(stats["completadas"]), "Completadas", ""),
        (str(stats["borradores"]), "En borrador", ""),
        (str(stats["adoptar"]), "Recomendación adoptar", ""),
        (stats["ultimo_software"][:18] + ("…" if len(stats["ultimo_software"]) > 18 else ""), "Último software", ""),
    ]
    for col, (val, label, delta) in zip([c1, c2, c3, c4, c5], kpis):
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-value">{val}</div>
                    <div class="kpi-label">{label}</div>
                    {f'<div class="kpi-delta">{delta}</div>' if delta else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_recent_evaluations(items: list, limit: int = 5) -> None:
    st.markdown("#### Actividad reciente")
    if not items:
        st.markdown(
            '<div class="action-panel"><p style="color:#64748b;margin:0;">'
            "Aún no hay evaluaciones. Cree la primera desde el panel lateral o abra el historial."
            "</p></div>",
            unsafe_allow_html=True,
        )
        return
    for it in items[:limit]:
        estado = it["estado"]
        badge_class = "badge-completada" if estado == "completada" else "badge-borrador"
        fecha = it["updated_at"].strftime("%d/%m/%Y %H:%M") if it.get("updated_at") else ""
        st.markdown(
            f"""
            <div class="hist-row">
                <strong style="color:#0c1222;">{it['software_nombre']}</strong>
                <span style="color:#64748b;"> — {it['nombre_proyecto']}</span><br>
                <span class="{badge_class}">{estado}</span>
                <span style="color:#94a3b8;font-size:0.85rem;"> · Re-eval. #{it['numero_reevaluacion']} · {fecha}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
