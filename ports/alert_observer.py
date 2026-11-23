from abc import ABC, abstractmethod

from domain.alert import Alert


class AlertObserver(ABC):
    """Puerto de salida (Observer): cualquier canal de alerta (email, Slack, SMS, Teams...)."""

    @abstractmethod
    def update(self, alerta: Alert) -> None:
        """Recibe una alerta notificada por un monitor."""
