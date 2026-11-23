"""Canales de alerta concretos (Observers). El envío se simula en consola."""

import logging

from domain.alert import Alert
from ports.alert_observer import AlertObserver


class EmailAlert(AlertObserver):
    def __init__(self, destinatario: str) -> None:
        self._destinatario = destinatario

    def update(self, alerta: Alert) -> None:
        print(f"  [EMAIL -> {self._destinatario}] {alerta.message()}")


class SlackAlert(AlertObserver):
    def __init__(self, canal: str) -> None:
        self._canal = canal

    def update(self, alerta: Alert) -> None:
        print(f"  [SLACK -> {self._canal}] {alerta.message()}")


class LogAlert(AlertObserver):
    """Registra las alertas en el log de la aplicación."""

    def __init__(self, nombre_logger: str = "monitoreo") -> None:
        self._logger = logging.getLogger(nombre_logger)

    def update(self, alerta: Alert) -> None:
        self._logger.warning(alerta.message())
