"""Adaptador de entrada: lee la configuración del sistema desde un archivo JSON.

Construye los objetos con las fábricas (Factory Method) y aplica umbrales e
intervalo a MonitoringConfig. No conoce la fachada (adapters/ no puede importar
application/): entrega una SystemDefinition y main.py hace el cableado.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from adapters.factories import Registries, default_registries
from adapters.monitoring_config import MonitoringConfig
from domain.evaluation_rules import EvaluationRule
from ports.alert_observer import AlertObserver
from ports.metrics_provider import MetricsProvider


@dataclass
class ServiceDefinition:
    nombre: str
    proveedor: MetricsProvider
    reglas: dict[str, EvaluationRule] = field(default_factory=dict)


@dataclass
class SystemDefinition:
    canales: list[AlertObserver]
    servicios: list[ServiceDefinition]


class JsonConfigLoader:
    def __init__(self, config: MonitoringConfig, registros: Registries | None = None) -> None:
        self._config = config
        self._registros = registros or default_registries()

    def load_file(self, ruta: Path) -> SystemDefinition:
        return self.load(json.loads(Path(ruta).read_text(encoding="utf-8")))

    def load(self, datos: dict[str, Any]) -> SystemDefinition:
        monitoreo = datos.get("monitoreo", {})
        for metrica, porcentaje in monitoreo.get("umbrales", {}).items():
            self._config.set_threshold(metrica, float(porcentaje))
        if "intervalo_segundos" in monitoreo:
            self._config.check_interval_seconds = float(monitoreo["intervalo_segundos"])

        canales = [self._registros.canales.create(spec) for spec in datos.get("canales", [])]
        servicios = [self._service(spec) for spec in datos.get("servicios", [])]
        return SystemDefinition(canales, servicios)

    def _service(self, spec: dict[str, Any]) -> ServiceDefinition:
        reglas = {
            metrica: self._registros.reglas.create(regla)
            for metrica, regla in spec.get("reglas", {}).items()
        }
        return ServiceDefinition(
            nombre=spec["nombre"],
            proveedor=self._registros.proveedores.create(spec["proveedor"]),
            reglas=reglas,
        )
