from collections import defaultdict, deque

from domain.alert import Alert
from domain.evaluation_rules import HISTORY_SIZE, EvaluationRule, ThresholdRule


class MetricEvaluator:
    """Context del patrón Strategy: aplica la regla de cada métrica sobre su historial.

    Auditoría A3: esta responsabilidad antes estaba dentro de Microservice.evaluate(),
    mezclada con el cambio de estado. Ahora MetricEvaluator solo detecta alertas y
    Microservice solo gestiona su estado (SRP).
    """

    def __init__(
        self,
        nombre_servicio: str,
        reglas: dict[str, EvaluationRule] | None = None,
        regla_por_defecto: EvaluationRule | None = None,
    ) -> None:
        self._nombre_servicio = nombre_servicio
        self._reglas = dict(reglas or {})
        self._regla_por_defecto = regla_por_defecto or ThresholdRule()
        self._historial: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=HISTORY_SIZE))

    def rule_for(self, metrica: str) -> EvaluationRule:
        return self._reglas.get(metrica, self._regla_por_defecto)

    def evaluate(self, metricas: dict[str, float], umbrales: dict[str, float]) -> list[Alert]:
        """Registra las lecturas y retorna las alertas detectadas en este ciclo.

        Las métricas sin umbral configurado se registran pero no se evalúan.
        """
        alertas: list[Alert] = []
        for metrica, valor in metricas.items():
            self._historial[metrica].append(valor)
            if metrica not in umbrales:
                continue
            regla = self.rule_for(metrica)
            violacion = regla.evaluate(tuple(self._historial[metrica]), umbrales[metrica])
            if violacion is not None:
                alertas.append(
                    Alert(
                        self._nombre_servicio,
                        metrica,
                        violacion.valor,
                        violacion.limite,
                        criterio=regla.criterio,
                    )
                )
        return alertas
