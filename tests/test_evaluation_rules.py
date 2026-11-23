"""Pruebas del patrón Strategy (fase 4)."""

from collections.abc import Sequence

import pytest

from domain.evaluation_rules import (
    EvaluationRule,
    MovingAverageRule,
    SpikeRule,
    ThresholdRule,
    Violation,
)
from domain.metric_evaluator import MetricEvaluator

# --- Cada estrategia por separado ---------------------------------------------------


def test_threshold_alerta_solo_si_el_valor_actual_supera_el_umbral() -> None:
    regla = ThresholdRule()
    assert regla.evaluate([50, 85], 80) == Violation(85, 80)
    assert regla.evaluate([85, 80], 80) is None  # igual al umbral no alerta


def test_promedio_movil_ignora_un_pico_aislado() -> None:
    regla = MovingAverageRule(ventana=3)
    assert regla.evaluate([70, 70, 99], 80) is None  # promedio 79.7
    assert regla.evaluate([85, 90, 95], 80) == Violation(90.0, 80)


def test_promedio_movil_no_evalua_sin_suficientes_lecturas() -> None:
    assert MovingAverageRule(ventana=3).evaluate([99, 99], 80) is None


def test_pico_detecta_subida_brusca_aunque_este_bajo_el_umbral() -> None:
    regla = SpikeRule(max_incremento=20)
    assert regla.evaluate([40, 75], 95) == Violation(35, 20)
    assert regla.evaluate([40, 55], 95) is None
    assert regla.evaluate([75], 95) is None  # con una sola lectura no hay subida


@pytest.mark.parametrize("crear", [lambda: MovingAverageRule(1), lambda: SpikeRule(0)])
def test_parametros_invalidos_se_rechazan(crear) -> None:
    with pytest.raises(ValueError):
        crear()


# --- LSP: todas las estrategias cumplen el mismo contrato ----------------------------


@pytest.mark.parametrize("regla", [ThresholdRule(), MovingAverageRule(3), SpikeRule(20)])
def test_lsp_todas_las_reglas_son_intercambiables(regla: EvaluationRule) -> None:
    assert isinstance(regla.criterio, str) and regla.criterio
    for historial in ([10], [10, 99], [99, 99, 99, 99]):
        resultado = regla.evaluate(historial, 80)
        assert resultado is None or isinstance(resultado, Violation)


# --- Context: MetricEvaluator ------------------------------------------------------


def test_evaluador_usa_threshold_por_defecto_y_regla_propia_por_metrica() -> None:
    evaluador = MetricEvaluator("svc", reglas={"memoria": MovingAverageRule(3)})
    alertas = evaluador.evaluate({"cpu": 90, "memoria": 99}, {"cpu": 80, "memoria": 80})
    assert [a.metrica for a in alertas] == ["cpu"]  # memoria aún no tiene 3 lecturas
    assert alertas[0].criterio == "valor actual"


def test_evaluador_guarda_historial_entre_ciclos() -> None:
    evaluador = MetricEvaluator("svc", reglas={"cpu": MovingAverageRule(3)})
    for valor in (85, 90):
        assert evaluador.evaluate({"cpu": valor}, {"cpu": 80}) == []
    alertas = evaluador.evaluate({"cpu": 95}, {"cpu": 80})
    assert alertas[0].valor == 90.0 and alertas[0].criterio == "promedio de 3 ciclos"


def test_evaluador_ignora_metricas_sin_umbral() -> None:
    assert MetricEvaluator("svc").evaluate({"disco": 99}, {"cpu": 80}) == []


def test_ocp_una_regla_nueva_funciona_sin_modificar_el_codigo_existente() -> None:
    """Se agrega una estrategia desde fuera; ni MetricEvaluator ni las reglas cambian."""

    class BelowRule(EvaluationRule):
        criterio = "por debajo del mínimo"

        def evaluate(self, historial: Sequence[float], umbral: float) -> Violation | None:
            return Violation(historial[-1], umbral) if historial[-1] < umbral else None

    evaluador = MetricEvaluator("svc", reglas={"disponibilidad": BelowRule()})
    alertas = evaluador.evaluate({"disponibilidad": 90}, {"disponibilidad": 99})
    assert alertas[0].criterio == "por debajo del mínimo"
