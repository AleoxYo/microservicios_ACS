"""Pruebas del patrón State (fase 3)."""

import pytest

from domain.alert import Alert, Severity
from domain.microservice import Microservice
from domain.service_state import (
    CriticalState,
    DegradedState,
    HealthyState,
    MaintenanceState,
    ServiceState,
)

ALTA = {"cpu": 95.0}
NORMAL = {"cpu": 50.0}
ALERTA = [Alert("svc", "cpu", 95.0, 80.0)]


def detectar(metricas: dict[str, float]) -> list[Alert]:
    """Simula lo que detectaría MetricEvaluator con umbral de CPU en 80%."""
    return ALERTA if metricas["cpu"] > 80.0 else []


def recorrer(servicio: Microservice, lecturas: list[dict[str, float]]) -> list[str]:
    nombres = []
    for metricas in lecturas:
        servicio.record_cycle(detectar(metricas))
        nombres.append(servicio.estado.nombre)
    return nombres


def test_escala_a_critico_tras_tres_ciclos_en_alerta() -> None:
    estados = recorrer(Microservice("svc"), [ALTA, ALTA, ALTA])
    assert estados == ["DEGRADADO", "DEGRADADO", "CRITICO"]


def test_degradado_vuelve_a_saludable_con_un_ciclo_sano() -> None:
    assert recorrer(Microservice("svc"), [ALTA, NORMAL]) == ["DEGRADADO", "SALUDABLE"]


def test_histeresis_critico_necesita_dos_ciclos_sanos_seguidos() -> None:
    estados = recorrer(Microservice("svc"), [ALTA, ALTA, ALTA, NORMAL, ALTA, NORMAL, NORMAL])
    assert estados[3:] == ["CRITICO", "CRITICO", "CRITICO", "SALUDABLE"]


def test_severidad_la_asigna_el_estado() -> None:
    servicio = Microservice("svc")
    primera = servicio.record_cycle(detectar(ALTA))
    servicio.record_cycle(detectar(ALTA))
    critica = servicio.record_cycle(detectar(ALTA))
    assert primera[0].severidad is Severity.WARNING
    assert critica[0].severidad is Severity.CRITICAL


def test_ciclo_sano_en_critico_no_emite_alertas() -> None:
    servicio = Microservice("svc")
    recorrer(servicio, [ALTA, ALTA, ALTA])
    assert servicio.record_cycle(detectar(NORMAL)) == []


def test_mantenimiento_suprime_alertas_y_al_salir_queda_saludable() -> None:
    servicio = Microservice("svc")
    recorrer(servicio, [ALTA, ALTA, ALTA])
    servicio.start_maintenance()
    assert servicio.record_cycle(detectar(ALTA)) == []
    assert servicio.estado.nombre == "MANTENIMIENTO"
    servicio.end_maintenance()
    assert servicio.estado.nombre == "SALUDABLE"


def test_end_maintenance_fuera_de_mantenimiento_no_cambia_estado() -> None:
    servicio = Microservice("svc")
    servicio.record_cycle(detectar(ALTA))
    servicio.end_maintenance()
    assert servicio.estado.nombre == "DEGRADADO"


@pytest.mark.parametrize(
    "estado", [HealthyState(), DegradedState(2), CriticalState(1), MaintenanceState()]
)
def test_lsp_todos_los_estados_son_intercambiables(estado: ServiceState) -> None:
    """Cualquier estado responde al mismo contrato y siempre devuelve otro ServiceState."""
    for alertas in ([], ALERTA):
        assert isinstance(estado.on_cycle(alertas), ServiceState)
        assert isinstance(estado.emit(alertas), list)
    assert isinstance(estado.start_maintenance(), MaintenanceState)
    assert isinstance(estado.end_maintenance(), ServiceState)
