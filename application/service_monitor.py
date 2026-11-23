import logging

from domain.alert import Alert
from domain.metric_evaluator import MetricEvaluator
from domain.microservice import Microservice
from ports.alert_observer import AlertObserver
from ports.config_provider import ConfigProvider
from ports.metrics_provider import MetricsProvider

logger = logging.getLogger("monitoreo")


class ServiceMonitor:
    """Subject del Observer: monitorea un microservicio y notifica a los canales de alerta."""

    def __init__(
        self,
        servicio: Microservice,
        proveedor: MetricsProvider,
        config: ConfigProvider,
        evaluador: MetricEvaluator | None = None,
    ) -> None:
        self._servicio = servicio
        self._proveedor = proveedor
        self._evaluador = evaluador or MetricEvaluator(servicio.nombre)
        self._observadores: list[AlertObserver] = []
        self._config = config  # A1: inyectada, ya no se llama MonitoringConfig() aquí

    @property
    def service(self) -> Microservice:
        return self._servicio

    def attach(self, observador: AlertObserver) -> None:
        if observador not in self._observadores:
            self._observadores.append(observador)

    def detach(self, observador: AlertObserver) -> None:
        # A6: quitar un observador que no estaba suscrito no debe romper la ejecución.
        if observador in self._observadores:
            self._observadores.remove(observador)

    def notify(self, alerta: Alert) -> None:
        # A5: el fallo de un canal no debe impedir que los demás reciban la alerta.
        for observador in self._observadores:
            try:
                observador.update(alerta)
            except Exception:
                logger.exception(
                    "El canal %s falló al notificar la alerta", type(observador).__name__
                )

    def check(self) -> list[Alert]:
        """Un ciclo: lee métricas (Adapter), las evalúa (Strategy), actualiza el estado
        (State) y notifica a los canales (Observer) las alertas que el estado emite."""
        metricas = self._proveedor.get_metrics()
        detectadas = self._evaluador.evaluate(metricas, self._config.get_thresholds())
        alertas = self._servicio.record_cycle(detectadas)
        for alerta in alertas:
            self.notify(alerta)
        return alertas
