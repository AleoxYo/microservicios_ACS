"""Patrón Factory Method: construcción de canales, proveedores y reglas desde configuración.

Problema que resuelve (auditoría A7): main.py creaba cada objeto a mano. Para que
el sistema se arme desde un archivo de configuración hay que convertir el texto
"email" en un EmailAlert, "legacy" en un LegacyApiAdapter, etc. Hacerlo con
if/elif sobre el tipo obliga a modificar esa cadena con cada canal nuevo (OCP).

Solución: cada producto tiene su fábrica concreta, que sobrescribe el método
fábrica `create(parametros)`. Un FactoryRegistry asocia el nombre del tipo con
su fábrica y elige por búsqueda en un diccionario, sin condicionales. Un tipo
nuevo se agrega con `registry.register("teams", TeamsChannelFactory())`, sin
tocar este archivo.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from adapters.alert_channels import EmailAlert, LogAlert, SlackAlert
from adapters.external_apis import CloudMetricsApi, LegacyMonitoringApi
from adapters.metrics_adapters import CloudApiAdapter, LegacyApiAdapter
from domain.evaluation_rules import EvaluationRule, MovingAverageRule, SpikeRule, ThresholdRule
from ports.alert_observer import AlertObserver
from ports.metrics_provider import MetricsProvider

T = TypeVar("T")


class Factory(ABC, Generic[T]):
    """Creator abstracto: declara el método fábrica."""

    @abstractmethod
    def create(self, parametros: dict[str, Any]) -> T:
        """Construye el producto a partir de los parámetros de configuración."""


class FactoryRegistry(Generic[T]):
    """Asocia el nombre de un tipo ("email", "legacy"...) con la fábrica que lo construye."""

    def __init__(self, familia: str) -> None:
        self._familia = familia
        self._fabricas: dict[str, Factory[T]] = {}

    def register(self, tipo: str, fabrica: Factory[T]) -> None:
        self._fabricas[tipo] = fabrica

    def types(self) -> list[str]:
        return sorted(self._fabricas)

    def create(self, especificacion: dict[str, Any]) -> T:
        """Crea un producto a partir de {"tipo": ..., <parámetros>}."""
        parametros = dict(especificacion)
        tipo = parametros.pop("tipo", None)
        fabrica = self._fabricas.get(tipo)
        if fabrica is None:
            raise ValueError(
                f"Tipo de {self._familia} desconocido: {tipo!r}. Disponibles: {self.types()}"
            )
        try:
            return fabrica.create(parametros)
        except KeyError as error:
            raise ValueError(f"Falta el parámetro {error} para {self._familia} {tipo!r}") from None


# --- Canales de alerta ------------------------------------------------------------


class EmailChannelFactory(Factory[AlertObserver]):
    def create(self, parametros: dict[str, Any]) -> AlertObserver:
        return EmailAlert(parametros["destinatario"])


class SlackChannelFactory(Factory[AlertObserver]):
    def create(self, parametros: dict[str, Any]) -> AlertObserver:
        return SlackAlert(parametros["canal"])


class LogChannelFactory(Factory[AlertObserver]):
    def create(self, parametros: dict[str, Any]) -> AlertObserver:
        return LogAlert(parametros.get("logger", "monitoreo"))


# --- Proveedores de métricas (cada uno con su API externa y su Adapter) -------------


class LegacyProviderFactory(Factory[MetricsProvider]):
    def create(self, parametros: dict[str, Any]) -> MetricsProvider:
        return LegacyApiAdapter(LegacyMonitoringApi(muestras_cpu=parametros["muestras_cpu"]))


class CloudProviderFactory(Factory[MetricsProvider]):
    def create(self, parametros: dict[str, Any]) -> MetricsProvider:
        muestras = [tuple(muestra) for muestra in parametros["muestras"]]
        return CloudApiAdapter(CloudMetricsApi(muestras=muestras))


# --- Reglas de evaluación (Strategy) ------------------------------------------------


class ThresholdRuleFactory(Factory[EvaluationRule]):
    def create(self, parametros: dict[str, Any]) -> EvaluationRule:
        return ThresholdRule()


class MovingAverageRuleFactory(Factory[EvaluationRule]):
    def create(self, parametros: dict[str, Any]) -> EvaluationRule:
        return MovingAverageRule(ventana=parametros.get("ventana", 3))


class SpikeRuleFactory(Factory[EvaluationRule]):
    def create(self, parametros: dict[str, Any]) -> EvaluationRule:
        return SpikeRule(max_incremento=parametros.get("max_incremento", 20.0))


@dataclass
class Registries:
    canales: FactoryRegistry[AlertObserver]
    proveedores: FactoryRegistry[MetricsProvider]
    reglas: FactoryRegistry[EvaluationRule]


def default_registries() -> Registries:
    """Registros con todos los tipos que trae el sistema."""
    canales = FactoryRegistry[AlertObserver]("canal")
    canales.register("email", EmailChannelFactory())
    canales.register("slack", SlackChannelFactory())
    canales.register("log", LogChannelFactory())

    proveedores = FactoryRegistry[MetricsProvider]("proveedor")
    proveedores.register("legacy", LegacyProviderFactory())
    proveedores.register("cloud", CloudProviderFactory())

    reglas = FactoryRegistry[EvaluationRule]("regla")
    reglas.register("umbral", ThresholdRuleFactory())
    reglas.register("promedio", MovingAverageRuleFactory())
    reglas.register("pico", SpikeRuleFactory())

    return Registries(canales, proveedores, reglas)
