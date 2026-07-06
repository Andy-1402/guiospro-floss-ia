"""Catálogo GUIOSAD desde CSV hacia PostgreSQL."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import select

from db.models import Dimension, Factor, Subfactor
from db.session import get_session

_BASE = Path(__file__).resolve().parent.parent


def seed_catalog_if_empty() -> int:
    """Importa dimensiones, factores y subfactores si la BD está vacía."""
    with get_session() as session:
        if session.execute(select(Factor.id).limit(1)).first():
            return 0

        data = pd.read_csv(_BASE / "guiosad_data.csv", sep="\t")
        factors_csv = pd.read_csv(_BASE / "factors.csv", sep="\t")
        factor_meta = {
            row["Factor"]: (int(row["Sugerida"]), row["Alcance"])
            for _, row in factors_csv.iterrows()
        }

        dim_map: dict[str, Dimension] = {}
        factor_map: dict[str, Factor] = {}
        orden_f = 0

        for dim_name in data["Dimensión"].unique():
            dim = Dimension(nombre=dim_name)
            session.add(dim)
            session.flush()
            dim_map[dim_name] = dim

        for dim_name in data["Dimensión"].unique():
            df_dim = data[data["Dimensión"] == dim_name]
            for factor_name in df_dim["Factor"].unique():
                sug, alcance = factor_meta.get(factor_name, (1, "Interno"))
                factor = Factor(
                    dimension_id=dim_map[dim_name].id,
                    nombre=factor_name,
                    importancia_sugerida=sug,
                    alcance_catalogo=alcance,
                    orden=orden_f,
                )
                orden_f += 1
                session.add(factor)
                session.flush()
                factor_map[factor_name] = factor

                df_f = df_dim[df_dim["Factor"] == factor_name]
                for ord_s, desc in enumerate(df_f["Subfactor"].tolist()):
                    session.add(
                        Subfactor(
                            factor_id=factor.id,
                            descripcion=desc,
                            orden=ord_s,
                        )
                    )

        session.commit()
        return len(factor_map)
