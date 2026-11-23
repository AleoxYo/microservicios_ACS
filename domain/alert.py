from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    WARNING = "ADVERTENCIA"
    CRITICAL = "CRITICA"


@dataclass(frozen=True)
class Alert:
    """Evento que se genera cuando una métrica supera su umbral configurado.

    La severidad la asigna el estado del microservicio (patrón State) al emitir la alerta.
    """

    nombre_servicio: str
    metrica: str
    valor: float
    umbral: float
    severidad: Severity = Severity.WARNING
    criterio: str = "valor actual"  # lo asigna la regla de evaluación (patrón Strategy)

    def message(self) -> str:
        return (
            f"[{self.severidad.value}] {self.nombre_servicio}: {self.metrica} ({self.criterio}) "
            f"en {self.valor:.1f}% supera el límite de {self.umbral:.1f}%"
        )
