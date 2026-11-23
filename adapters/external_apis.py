"""APIs externas de monitoreo simuladas, con formatos de datos heterogéneos.

El sistema no las modifica; los adapters traducen sus respuestas.
Cada llamada retorna la siguiente muestra para simular lecturas que cambian en el tiempo.
"""

from itertools import cycle


class LegacyMonitoringApi:
    """API legada que retorna {"cpu_usage_percent": 85}."""

    def __init__(self, muestras_cpu: list[int]) -> None:
        self._muestras = cycle(muestras_cpu)

    def fetch_stats(self) -> dict:
        return {"cpu_usage_percent": next(self._muestras)}


class CloudMetricsApi:
    """API en la nube que retorna cargas como fracciones: {"data": {"cpuLoad": 0.45, ...}}."""

    def __init__(self, muestras: list[tuple[float, float]]) -> None:
        self._muestras = cycle(muestras)

    def query(self) -> dict:
        carga_cpu, carga_memoria = next(self._muestras)
        return {"data": {"cpuLoad": carga_cpu, "memoryLoad": carga_memoria}}
