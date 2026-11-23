"""Patrón State: el estado de salud de un microservicio.

Problema que resuelve: con un enum de dos valores (SALUDABLE / ALERTA) un servicio
cuya CPU oscila alrededor del umbral cambia de estado en cada ciclo y dispara
alertas sin parar (flapping). Para evitarlo hacen falta contadores de ciclos,
escalamiento y modo mantenimiento; con un enum eso termina en una cadena de
if/elif sobre el estado actual. Con State, cada estado es una clase que decide
su propia transición y qué alertas emite; agregar un estado no modifica a los demás.

Transiciones:
    Saludable  --alerta-->                     Degradado
    Degradado  --alerta x CYCLES_TO_CRITICAL-> Critico
    Degradado  --ciclo sano-->                 Saludable
    Critico    --ciclo sano x CYCLES_TO_RECOVER--> Saludable   (histéresis)
    Critico    --alerta-->                     Critico (reinicia el conteo de recuperación)
    Cualquiera --start_maintenance-->          Mantenimiento (suprime alertas)
    Mantenimiento --end_maintenance-->         Saludable
"""

from abc import ABC, abstractmethod
from dataclasses import replace

from domain.alert import Alert, Severity

CYCLES_TO_CRITICAL = 3
CYCLES_TO_RECOVER = 2


class ServiceState(ABC):
    """Estado abstracto. El Context es Microservice, que delega en su estado actual."""

    #: Severidad con la que este estado emite alertas; None = no emite.
    severidad: Severity | None = None

    @property
    @abstractmethod
    def nombre(self) -> str:
        """Nombre visible del estado."""

    @abstractmethod
    def on_cycle(self, alertas: list[Alert]) -> "ServiceState":
        """Retorna el estado siguiente según las alertas detectadas en este ciclo."""

    def emit(self, alertas: list[Alert]) -> list[Alert]:
        """Retorna las alertas que se deben notificar, con la severidad de este estado."""
        if self.severidad is None:
            return []
        return [replace(alerta, severidad=self.severidad) for alerta in alertas]

    def start_maintenance(self) -> "ServiceState":
        return MaintenanceState()

    def end_maintenance(self) -> "ServiceState":
        return self  # solo MaintenanceState sale de mantenimiento

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class HealthyState(ServiceState):
    nombre = "SALUDABLE"

    def on_cycle(self, alertas: list[Alert]) -> ServiceState:
        return DegradedState(ciclos_en_alerta=1) if alertas else self


class DegradedState(ServiceState):
    nombre = "DEGRADADO"
    severidad = Severity.WARNING

    def __init__(self, ciclos_en_alerta: int = 1) -> None:
        self.ciclos_en_alerta = ciclos_en_alerta

    def on_cycle(self, alertas: list[Alert]) -> ServiceState:
        if not alertas:
            return HealthyState()
        ciclos = self.ciclos_en_alerta + 1
        return CriticalState() if ciclos >= CYCLES_TO_CRITICAL else DegradedState(ciclos)

    def emit(self, alertas: list[Alert]) -> list[Alert]:
        """Avisa solo al entrar a Degradado; si ya estaba aquí no repite la advertencia."""
        if self.ciclos_en_alerta > 1:
            return []
        return super().emit(alertas)

    def __repr__(self) -> str:
        return f"DegradedState(ciclos_en_alerta={self.ciclos_en_alerta})"


class CriticalState(ServiceState):
    nombre = "CRITICO"
    severidad = Severity.CRITICAL

    def __init__(self, ciclos_sanos: int = 0) -> None:
        self.ciclos_sanos = ciclos_sanos

    def on_cycle(self, alertas: list[Alert]) -> ServiceState:
        if alertas:
            return CriticalState(ciclos_sanos=0)
        ciclos = self.ciclos_sanos + 1
        return HealthyState() if ciclos >= CYCLES_TO_RECOVER else CriticalState(ciclos)

    def __repr__(self) -> str:
        return f"CriticalState(ciclos_sanos={self.ciclos_sanos})"


class MaintenanceState(ServiceState):
    """Durante un mantenimiento programado las métricas se leen pero no se alerta."""

    nombre = "MANTENIMIENTO"

    def on_cycle(self, alertas: list[Alert]) -> ServiceState:
        return self

    def start_maintenance(self) -> ServiceState:
        return self

    def end_maintenance(self) -> ServiceState:
        return HealthyState()
