from abc import ABC, abstractmethod


class MetricsProvider(ABC):
    """Puerto de salida: contrato uniforme con el que el núcleo lee métricas (Target del Adapter).

    Auditoría A2: antes el método abstracto era get_cpu_usage(), lo que obligaba a
    todo proveedor a exponer CPU (violación de ISP/LSP). Ahora el único contrato
    es get_metrics(); cada adaptador expone las métricas que realmente tiene.
    """

    @abstractmethod
    def get_metrics(self) -> dict[str, float]:
        """Retorna las métricas soportadas por nombre, en porcentaje (0-100)."""
