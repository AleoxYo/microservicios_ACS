"""Patrón Strategy: reglas intercambiables para decidir si una métrica está en alerta.

Problema que resuelve: la única regla era "valor actual > umbral". Un pico aislado
de un ciclo ya dispara alerta, y una subida brusca por debajo del umbral pasa
desapercibida. Agregar otra forma de evaluar obligaba a modificar
Microservice.evaluate() (violación de OCP) y a elegir la regla con if/elif.
Con Strategy, cada regla es una clase; se elige una por métrica al registrar el
servicio, y una regla nueva no toca el código existente.

Las reglas no guardan estado: reciben el historial de lecturas (lo mantiene
MetricEvaluator), así una misma instancia se puede compartir entre servicios.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

HISTORY_SIZE = 10  # lecturas que MetricEvaluator conserva por métrica


@dataclass(frozen=True)
class Violation:
    """Resultado de una regla incumplida: el valor evaluado y el límite que superó."""

    valor: float
    limite: float


class EvaluationRule(ABC):
    """Strategy abstracta."""

    @property
    @abstractmethod
    def criterio(self) -> str:
        """Descripción corta de qué se evalúa, para el mensaje de la alerta."""

    @abstractmethod
    def evaluate(self, historial: Sequence[float], umbral: float) -> Violation | None:
        """Evalúa el historial de lecturas (la última al final) contra el umbral.

        Retorna una Violation si la regla se incumple, o None si todo está bien.
        """


class ThresholdRule(EvaluationRule):
    """La lectura actual supera el umbral (comportamiento original del sistema)."""

    criterio = "valor actual"

    def evaluate(self, historial: Sequence[float], umbral: float) -> Violation | None:
        actual = historial[-1]
        return Violation(actual, umbral) if actual > umbral else None


class MovingAverageRule(EvaluationRule):
    """El promedio de las últimas `ventana` lecturas supera el umbral.

    Ignora picos aislados: solo alerta si la carga se sostiene. Mientras no haya
    `ventana` lecturas no evalúa, para no alertar con datos insuficientes.
    """

    def __init__(self, ventana: int = 3) -> None:
        if not 2 <= ventana <= HISTORY_SIZE:
            raise ValueError(f"La ventana debe estar entre 2 y {HISTORY_SIZE} lecturas")
        self._ventana = ventana

    @property
    def criterio(self) -> str:
        return f"promedio de {self._ventana} ciclos"

    def evaluate(self, historial: Sequence[float], umbral: float) -> Violation | None:
        if len(historial) < self._ventana:
            return None
        promedio = sum(historial[-self._ventana:]) / self._ventana
        return Violation(round(promedio, 1), umbral) if promedio > umbral else None


class SpikeRule(EvaluationRule):
    """La métrica subió más de `max_incremento` puntos entre dos ciclos seguidos.

    Detecta subidas bruscas aunque el valor siga por debajo del umbral. Usa su
    propio límite (max_incremento) en lugar del umbral configurado.
    """

    def __init__(self, max_incremento: float = 20.0) -> None:
        if max_incremento <= 0:
            raise ValueError("El incremento máximo debe ser positivo")
        self._max_incremento = max_incremento

    criterio = "subida en un ciclo"

    def evaluate(self, historial: Sequence[float], umbral: float) -> Violation | None:
        if len(historial) < 2:
            return None
        incremento = historial[-1] - historial[-2]
        if incremento > self._max_incremento:
            return Violation(round(incremento, 1), self._max_incremento)
        return None
