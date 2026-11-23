from abc import ABC, abstractmethod


class ConfigProvider(ABC):
    """Puerto de salida: de dónde lee el núcleo los umbrales y el intervalo de monitoreo.

    Auditoría A1: antes ServiceMonitor y MonitoringFacade llamaban MonitoringConfig()
    por dentro (dependencia oculta a una clase concreta, violación de DIP). Ahora
    dependen de esta abstracción y la configuración concreta se inyecta desde main.py.
    """

    @abstractmethod
    def get_thresholds(self) -> dict[str, float]:
        """Retorna una copia de los umbrales por métrica, en porcentaje."""

    @property
    @abstractmethod
    def check_interval_seconds(self) -> float:
        """Segundos de espera entre ciclos de monitoreo."""
