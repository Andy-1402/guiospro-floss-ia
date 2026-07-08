"""Lógica de evaluación GUIOSAD (sin dependencia de UI)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np

from guiosad import Guiosad


@dataclass
class FactorState:
    decisor_importance: int = 1
    scope: str = "Interno"
    subfactor_values: list[int] = field(default_factory=list)
    global_weight: float | None = None
    foda: str = ""
    evaluated: bool = False


class EvaluationEngine:
    FODA_THRESHOLD = 3
    MODEL_PATH = Path(__file__).resolve().parent / "modelo_importancia_floss.pkl"

    RECOMMENDATION_A = (
        "Recomendación A: Adoptar. Todos los factores han sido identificados como "
        "Oportunidades y/o Fortalezas. La organización cumple satisfactoriamente con "
        "la mayoría de requisitos para adoptar la solución FLOSS."
    )
    RECOMMENDATION_B = (
        "Recomendación B: Es posible adoptar. Se detectaron amenazas y/o debilidades "
        "en factores cuya importancia relativa es opcional; se sugiere revisar los "
        "criterios que no cumplen con lo mínimo requerido."
    )
    RECOMMENDATION_C = (
        "Recomendación C: La organización debe proporcionar los recursos necesarios "
        "para una adopción satisfactoria. Factores internos: mejorar en la "
        "organización; factores externos: dedicar recursos de ingeniería al software."
    )

    def __init__(self, model: Guiosad | None = None):
        self.model = model or Guiosad()
        self.factor_states: list[FactorState] = []
        self._classifier = self._load_classifier()
        self._init_states()

    def _init_states(self) -> None:
        self.factor_states = []
        for factor in self.model.factors:
            scope = factor.scope
            if scope == "Ambos":
                scope = "Interno"
            sub_vals = [1] * len(factor.subfactors)
            self.factor_states.append(
                FactorState(
                    decisor_importance=1,
                    scope=scope,
                    subfactor_values=sub_vals,
                )
            )

    @property
    def factor_names(self) -> list[str]:
        return self.model.factors_lbls

    def _load_classifier(self):
        if not self.MODEL_PATH.exists():
            return None
        try:
            return joblib.load(self.MODEL_PATH)
        except Exception:
            return None

    def _build_features(self, suggested_importance: int, decisor_importance: int, weight: float | None) -> np.ndarray:
        suggested = max(1, min(4, int(suggested_importance)))
        decisor = max(1, min(4, int(decisor_importance)))
        if weight is None:
            weight = (suggested + decisor) / 2
        weight = max(1.0, min(4.0, float(weight)))
        return np.array([[suggested, decisor, weight]], dtype=float)

    def _fallback_label(self, suggested_importance: int, decisor_importance: int, weight: float | None) -> str:
        suggested_idx = max(1, min(4, int(suggested_importance))) - 1
        decisor_idx = max(1, min(4, int(decisor_importance))) - 1
        raw_idx = (suggested_idx + decisor_idx) // 2
        return Guiosad.levels_lbls[raw_idx]

    def _predict_label(self, suggested_importance: int, decisor_importance: int, weight: float | None) -> str:
        if self._classifier is None:
            return self._fallback_label(suggested_importance, decisor_importance, weight)
        try:
            features = self._build_features(suggested_importance, decisor_importance, weight)
            prediction = self._classifier.predict(features)

            if isinstance(prediction, np.ndarray):
                # Normalizar casos donde predict devuelve [[valor1, valor2]]
                if prediction.ndim > 1 and prediction.shape[0] == 1:
                    prediction = prediction[0]
                if isinstance(prediction, np.ndarray) and prediction.size == 1:
                    prediction = prediction.item()
                elif isinstance(prediction, np.ndarray):
                    prediction = prediction[0]

            if isinstance(prediction, np.generic):
                prediction = prediction.item()

            label = str(prediction)
            if label in Guiosad.levels_lbls:
                return label
        except Exception:
            pass
        return self._fallback_label(suggested_importance, decisor_importance, weight)

    def suggested_label(self, index: int) -> str:
        factor = self.model.factors[index]
        state = self.factor_states[index]
        suggested_importance = getattr(factor, "suggested_importance", 1)
        decisor_importance = getattr(state, "decisor_importance", 1)
        return self._predict_label(suggested_importance, decisor_importance, state.global_weight)

    def suggested_index(self, index: int) -> int:
        return Guiosad.levels_lbls.index(self.suggested_label(index))

    def raw_scope(self, index: int) -> str:
        return self.model.factors[index].scope

    def _priority_rank(self, label: str) -> int:
        return {"Irrelevante": 0, "Opcional": 1, "Importante": 2, "Fundamental": 3}.get(label, 1)

    def relative_importance(self, index: int) -> tuple[str, bool]:
        label = self.suggested_label(index)
        relevant = self._priority_rank(label) > 0
        return label, relevant

    def relevant_factor_indices(self) -> list[int]:
        return [i for i in range(len(self.factor_states)) if self.relative_importance(i)[1]]

    def relevant_factor_names(self) -> list[str]:
        return [self.factor_names[i] for i in self.relevant_factor_indices()]

    def save_subfactors(self, index: int, values: list[int]) -> None:
        state = self.factor_states[index]
        state.subfactor_values = values[:]
        if not values:
            return
        state.global_weight = sum(values) / len(values)
        state.evaluated = True
        state.foda = self.compute_foda(state.scope, state.global_weight)

    def compute_foda(self, scope: str, global_weight: float) -> str:
        if scope == "Interno":
            return "Fortaleza" if global_weight >= self.FODA_THRESHOLD else "Debilidad"
        return "Oportunidad" if global_weight >= self.FODA_THRESHOLD else "Amenaza"

    def foda_row_status(self, index: int) -> str:
        _, relevant = self.relative_importance(index)
        state = self.factor_states[index]
        if not relevant:
            return "no_relevant"
        if not state.evaluated:
            return "pending"
        return "done"

    def compute_recommendation(self) -> tuple[str, str]:
        """
        Devuelve (texto_recomendación, estilo: success | warning | error | neutral).
        """
        relative_list: list[str] = []
        foda_list: list[str] = []

        for i, state in enumerate(self.factor_states):
            status = self.foda_row_status(i)
            if status != "done":
                continue
            rel_label, _ = self.relative_importance(i)
            relative_list.append(rel_label)
            foda_list.append(state.foda)

        if not foda_list:
            return "", "neutral"

        good = sum(1 for f in foda_list if f in ("Fortaleza", "Oportunidad"))
        bad = sum(1 for f in foda_list if f in ("Debilidad", "Amenaza"))

        has_critical = False
        has_optional_risk = False
        for rel, foda in zip(relative_list, foda_list):
            rel_rank = self._priority_rank(rel)
            if foda in ("Amenaza", "Debilidad") and rel_rank >= 2:
                has_critical = True
            elif foda in ("Amenaza", "Debilidad") and rel_rank == 1:
                has_optional_risk = True

        if has_critical:
            return self.RECOMMENDATION_C, "error"
        if has_optional_risk:
            return self.RECOMMENDATION_B, "warning"
        if good > bad:
            return self.RECOMMENDATION_A, "success"
        if good < bad:
            return (
                f"No adoptar: {bad} factores como Debilidad/Amenaza frente a "
                f"{good} como Fortaleza/Oportunidad.",
                "error",
            )
        return (
            f"Empate ({good} vs {bad}). Considerar factores no analizados por GUIOSAD.",
            "warning",
        )

    def summary_counts(self) -> dict[str, int]:
        counts = {
            "Fortaleza": 0,
            "Oportunidad": 0,
            "Debilidad": 0,
            "Amenaza": 0,
            "Pendiente": 0,
            "No relevante": 0,
        }
        for i in range(len(self.factor_states)):
            status = self.foda_row_status(i)
            if status == "no_relevant":
                counts["No relevante"] += 1
            elif status == "pending":
                counts["Pendiente"] += 1
            else:
                counts[self.factor_states[i].foda] += 1
        return counts
