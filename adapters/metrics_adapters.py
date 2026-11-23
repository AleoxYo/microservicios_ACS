from adapters.external_apis import CloudMetricsApi, LegacyMonitoringApi
from ports.metrics_provider import MetricsProvider


class LegacyApiAdapter(MetricsProvider):
    """Adapter: traduce LegacyMonitoringApi ({"cpu_usage_percent": 85}) a MetricsProvider."""

    def __init__(self, api: LegacyMonitoringApi) -> None:
        self._api = api

    def get_metrics(self) -> dict[str, float]:
        return {"cpu": float(self._api.fetch_stats()["cpu_usage_percent"])}


class CloudApiAdapter(MetricsProvider):
    """Adapter: traduce CloudMetricsApi (fracciones) a MetricsProvider (porcentajes)."""

    def __init__(self, api: CloudMetricsApi) -> None:
        self._api = api

    def get_metrics(self) -> dict[str, float]:
        datos = self._api.query()["data"]
        return {
            "cpu": round(datos["cpuLoad"] * 100, 1),
            "memoria": round(datos["memoryLoad"] * 100, 1),
        }
