import logging
import time

from application.service_monitor import ServiceMonitor
from domain.alert import Alert
from domain.evaluation_rules import EvaluationRule
from domain.metric_evaluator import MetricEvaluator
from domain.microservice import Microservice
from ports.alert_observer import AlertObserver
from ports.config_provider import ConfigProvider
from ports.metrics_provider import MetricsProvider

logger = logging.getLogger("monitoreo")


class MonitoringFacade:
    """Facade: punto único de entrada (puerto de entrada) para los equipos de operaciones.

    Oculta cómo se crean y coordinan los monitores, los proveedores de
    métricas, los umbrales y los canales de alerta.
    """

    def __init__(self, config: ConfigProvider) -> None:
        self._monitores: dict[str, ServiceMonitor] = {}
        self._canales: list[AlertObserver] = []
        self._config = config  # A1: inyectada desde el composition root (main.py)

    def add_alert_channel(self, canal: AlertObserver) -> None:
        self._canales.append(canal)
        for monitor in self._monitores.values():
            monitor.attach(canal)

    def register_service(
        self,
        nombre: str,
        proveedor: MetricsProvider,
        reglas: dict[str, EvaluationRule] | None = None,
    ) -> None:
        """Registra un servicio. `reglas` asigna una regla de evaluación por métrica;
        las métricas sin regla usan ThresholdRule (valor actual > umbral)."""
        evaluador = MetricEvaluator(nombre, reglas)
        monitor = ServiceMonitor(Microservice(nombre), proveedor, self._config, evaluador)
        for canal in self._canales:
            monitor.attach(canal)
        self._monitores[nombre] = monitor

    def run_monitoring(self, ciclos: int = 1) -> list[Alert]:
        """Ejecuta el monitoreo periódico, esperando el intervalo configurado entre ciclos."""
        alertas: list[Alert] = []
        for ciclo in range(1, ciclos + 1):
            logger.info("Ciclo de monitoreo %d", ciclo)
            for monitor in self._monitores.values():
                alertas.extend(monitor.check())
            if ciclo < ciclos:
                time.sleep(self._config.check_interval_seconds)
        return alertas

    def get_status(self) -> dict[str, str]:
        return {nombre: monitor.service.estado.nombre for nombre, monitor in self._monitores.items()}

    def start_maintenance(self, nombre: str) -> None:
        """Pone un servicio en mantenimiento programado: se monitorea pero no alerta."""
        self._monitores[nombre].service.start_maintenance()

    def end_maintenance(self, nombre: str) -> None:
        self._monitores[nombre].service.end_maintenance()
