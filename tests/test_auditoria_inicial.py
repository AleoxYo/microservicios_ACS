"""Pruebas de las correcciones de la auditoría inicial (A1, A2, A4, A5, A6)."""

import threading

import pytest

from adapters.monitoring_config import MonitoringConfig
from application.monitoring_facade import MonitoringFacade
from application.service_monitor import ServiceMonitor
from domain.alert import Alert
from domain.microservice import Microservice
from ports.alert_observer import AlertObserver
from ports.config_provider import ConfigProvider
from ports.metrics_provider import MetricsProvider


class ConfigFija(ConfigProvider):
    """Doble de prueba: posible solo porque el núcleo depende del puerto (A1)."""

    def __init__(self, umbrales: dict[str, float]) -> None:
        self._umbrales = umbrales

    def get_thresholds(self) -> dict[str, float]:
        return dict(self._umbrales)

    @property
    def check_interval_seconds(self) -> float:
        return 0.0


class ProveedorSoloMemoria(MetricsProvider):
    """Un proveedor sin CPU: antes de A2 no se podía implementar sin inventar un valor."""

    def get_metrics(self) -> dict[str, float]:
        return {"memoria": 95.0}


class CanalRoto(AlertObserver):
    def update(self, alerta: Alert) -> None:
        raise ConnectionError("SMTP caído")


class CanalMemoria(AlertObserver):
    def __init__(self) -> None:
        self.recibidas: list[Alert] = []

    def update(self, alerta: Alert) -> None:
        self.recibidas.append(alerta)


def test_a1_a2_fachada_funciona_con_config_inyectada_y_proveedor_sin_cpu() -> None:
    fachada = MonitoringFacade(config=ConfigFija({"memoria": 90.0}))
    canal = CanalMemoria()
    fachada.add_alert_channel(canal)
    fachada.register_service("reportes", ProveedorSoloMemoria())

    alertas = fachada.run_monitoring(ciclos=1)

    assert len(alertas) == 1 and canal.recibidas == alertas
    assert fachada.get_status()["reportes"] == "DEGRADADO"


def test_a4_escrituras_concurrentes_no_pierden_umbrales() -> None:
    config = MonitoringConfig()
    hilos = [
        threading.Thread(target=config.set_threshold, args=(f"metrica_{i}", 50.0))
        for i in range(200)
    ]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()
    umbrales = config.get_thresholds()
    assert all(f"metrica_{i}" in umbrales for i in range(200))


def test_a5_un_canal_que_falla_no_impide_notificar_a_los_demas() -> None:
    monitor = ServiceMonitor(Microservice("pagos"), ProveedorSoloMemoria(), ConfigFija({"memoria": 90.0}))
    canal_ok = CanalMemoria()
    monitor.attach(CanalRoto())
    monitor.attach(canal_ok)

    monitor.check()

    assert len(canal_ok.recibidas) == 1


def test_a6_detach_de_un_canal_no_suscrito_no_lanza_error() -> None:
    monitor = ServiceMonitor(Microservice("pagos"), ProveedorSoloMemoria(), ConfigFija({}))
    monitor.detach(CanalMemoria())  # no debe lanzar ValueError


def test_singleton_sigue_siendo_unico() -> None:
    assert MonitoringConfig() is MonitoringConfig()


def test_umbral_fuera_de_rango_se_rechaza() -> None:
    with pytest.raises(ValueError):
        MonitoringConfig().set_threshold("cpu", 150.0)
