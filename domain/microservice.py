from domain.alert import Alert
from domain.service_state import HealthyState, ServiceState


class Microservice:
    """Context del patrón State: microservicio monitoreado y su estado de salud actual.

    Auditoría A3: ya no compara métricas (eso lo hace MetricEvaluator con Strategy);
    solo recibe las alertas detectadas en un ciclo y delega la transición a su estado.
    """

    def __init__(self, nombre: str) -> None:
        self.nombre = nombre
        self._estado: ServiceState = HealthyState()

    @property
    def estado(self) -> ServiceState:
        return self._estado

    def record_cycle(self, detectadas: list[Alert]) -> list[Alert]:
        """Aplica el resultado de un ciclo y retorna las alertas que el nuevo estado emite."""
        self._estado = self._estado.on_cycle(detectadas)
        return self._estado.emit(detectadas)

    def start_maintenance(self) -> None:
        self._estado = self._estado.start_maintenance()

    def end_maintenance(self) -> None:
        self._estado = self._estado.end_maintenance()
