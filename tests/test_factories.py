"""Pruebas del patrón Factory Method y la carga desde JSON (fase 5)."""

from pathlib import Path
from typing import Any

import pytest

from adapters.alert_channels import EmailAlert, LogAlert, SlackAlert
from adapters.factories import Factory, default_registries
from adapters.json_config_loader import JsonConfigLoader
from adapters.metrics_adapters import CloudApiAdapter, LegacyApiAdapter
from adapters.monitoring_config import MonitoringConfig
from domain.alert import Alert
from domain.evaluation_rules import MovingAverageRule, SpikeRule, ThresholdRule
from ports.alert_observer import AlertObserver

RUTA_JSON = Path(__file__).resolve().parent.parent / "config" / "servicios.json"


@pytest.mark.parametrize(
    ("especificacion", "clase"),
    [
        ({"tipo": "email", "destinatario": "a@b.co"}, EmailAlert),
        ({"tipo": "slack", "canal": "#x"}, SlackAlert),
        ({"tipo": "log"}, LogAlert),
    ],
)
def test_crea_cada_canal_segun_su_tipo(especificacion: dict, clase: type) -> None:
    assert isinstance(default_registries().canales.create(especificacion), clase)


def test_crea_proveedores_que_entregan_metricas_normalizadas() -> None:
    proveedores = default_registries().proveedores
    legacy = proveedores.create({"tipo": "legacy", "muestras_cpu": [85]})
    cloud = proveedores.create({"tipo": "cloud", "muestras": [[0.5, 0.25]]})
    assert isinstance(legacy, LegacyApiAdapter) and legacy.get_metrics() == {"cpu": 85.0}
    assert isinstance(cloud, CloudApiAdapter) and cloud.get_metrics() == {"cpu": 50.0, "memoria": 25.0}


def test_crea_reglas_con_sus_parametros() -> None:
    reglas = default_registries().reglas
    assert isinstance(reglas.create({"tipo": "umbral"}), ThresholdRule)
    assert reglas.create({"tipo": "promedio", "ventana": 5}).criterio == "promedio de 5 ciclos"
    assert isinstance(reglas.create({"tipo": "pico", "max_incremento": 10}), SpikeRule)


def test_tipo_desconocido_da_error_claro_con_los_disponibles() -> None:
    with pytest.raises(ValueError, match=r"desconocido: 'sms'.*\['email', 'log', 'slack'\]"):
        default_registries().canales.create({"tipo": "sms"})


def test_parametro_faltante_da_error_claro() -> None:
    with pytest.raises(ValueError, match="Falta el parámetro 'destinatario'"):
        default_registries().canales.create({"tipo": "email"})


def test_ocp_un_tipo_nuevo_se_registra_sin_modificar_las_fabricas() -> None:
    class TeamsAlert(AlertObserver):
        def __init__(self, webhook: str) -> None:
            self.webhook = webhook

        def update(self, alerta: Alert) -> None:
            pass

    class TeamsChannelFactory(Factory[AlertObserver]):
        def create(self, parametros: dict[str, Any]) -> AlertObserver:
            return TeamsAlert(parametros["webhook"])

    registros = default_registries()
    registros.canales.register("teams", TeamsChannelFactory())
    canal = registros.canales.create({"tipo": "teams", "webhook": "https://hook"})
    assert isinstance(canal, TeamsAlert) and canal.webhook == "https://hook"


def test_carga_el_json_del_proyecto_y_aplica_la_configuracion() -> None:
    config = MonitoringConfig()
    sistema = JsonConfigLoader(config).load_file(RUTA_JSON)

    assert len(sistema.canales) == 3
    assert [s.nombre for s in sistema.servicios] == ["servicio-pagos", "servicio-autenticacion"]
    assert config.get_threshold("memoria") == 85.0
    assert config.check_interval_seconds == 0.5


def test_carga_reglas_por_metrica_desde_datos() -> None:
    datos = {
        "servicios": [
            {
                "nombre": "svc",
                "proveedor": {"tipo": "legacy", "muestras_cpu": [50]},
                "reglas": {"cpu": {"tipo": "promedio", "ventana": 4}},
            }
        ]
    }
    sistema = JsonConfigLoader(MonitoringConfig()).load(datos)
    regla = sistema.servicios[0].reglas["cpu"]
    assert isinstance(regla, MovingAverageRule) and regla.criterio == "promedio de 4 ciclos"
