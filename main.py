"""Composition root: arma el sistema de monitoreo y demuestra cada patrón.

Es el único módulo que conoce las clases concretas de adapters/; las crea y se
las inyecta al núcleo (application/) a través de los puertos (ports/).
"""

import logging
import sys
from pathlib import Path

from adapters.alert_channels import LogAlert
from adapters.external_apis import CloudMetricsApi, LegacyMonitoringApi
from adapters.json_config_loader import JsonConfigLoader
from adapters.metrics_adapters import CloudApiAdapter, LegacyApiAdapter
from adapters.monitoring_config import MonitoringConfig
from application.monitoring_facade import MonitoringFacade
from domain.evaluation_rules import MovingAverageRule, SpikeRule, ThresholdRule

RUTA_CONFIGURACION = Path(__file__).parent / "config" / "servicios.json"


def print_title(titulo: str) -> None:
    """Imprime el encabezado de cada sección de la demostración."""
    print(f"\n=== {titulo} ===")


def print_status(monitoreo: MonitoringFacade) -> None:
    """Muestra el estado actual de cada servicio registrado en la fachada."""
    print(f"Estado de los servicios: {monitoreo.get_status()}")


def main() -> None:
    # El log sale por consola junto con los print, con el prefijo [LOG NIVEL].
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="  [LOG %(levelname)s] %(message)s")

    # Singleton: dos llamadas devuelven el mismo objeto, así un cambio hecho
    # desde una referencia se ve desde la otra.
    print_title("1. Singleton: configuración centralizada")
    configuracion_a = MonitoringConfig()
    configuracion_b = MonitoringConfig()
    print(f"configuracion_a is configuracion_b: {configuracion_a is configuracion_b}")
    configuracion_b.set_threshold("memoria", 85.0)  # nuevo tipo de métrica: solo necesita un umbral
    configuracion_b.check_interval_seconds = 0.5
    print(f"Umbrales vistos desde configuracion_a: {configuracion_a.get_thresholds()}")

    # Adapter: se compara la respuesta original de cada API con la versión
    # adaptada que consume el núcleo del sistema.
    print_title("2. Adapter: APIs externas heterogéneas")
    api_legada = LegacyMonitoringApi(muestras_cpu=[85])
    print(f"Respuesta original API legada: {api_legada.fetch_stats()}")
    print(f"get_metrics() adaptado: {LegacyApiAdapter(api_legada).get_metrics()}")
    api_nube = CloudMetricsApi(muestras=[(0.45, 0.70)])
    print(f"Respuesta original API nube: {api_nube.query()}")
    print(f"get_metrics() adaptado: {CloudApiAdapter(api_nube).get_metrics()}")

    # Factory Method + Facade + Observer: canales, servicios, proveedores y reglas
    # se leen de config/servicios.json; las fábricas los construyen sin if/elif
    # y aquí solo se conectan a la fachada. La configuración se inyecta por el
    # puerto ConfigProvider (la fachada no sabe que es un Singleton).
    print_title("3. Factory Method + Facade + Observer: sistema armado desde config/servicios.json")
    sistema = JsonConfigLoader(configuracion_a).load_file(RUTA_CONFIGURACION)
    print(f"Cargados {len(sistema.canales)} canales y {len(sistema.servicios)} servicios")
    monitoreo = MonitoringFacade(config=configuracion_a)
    for canal in sistema.canales:
        monitoreo.add_alert_channel(canal)
    for servicio in sistema.servicios:
        monitoreo.register_service(servicio.nombre, servicio.proveedor, servicio.reglas)
    alertas = monitoreo.run_monitoring(ciclos=2)
    print(f"Alertas generadas: {len(alertas)}")
    print_status(monitoreo)

    # Singleton en tiempo real: se modifica el umbral desde una referencia nueva
    # y los monitores ya creados lo aplican en el siguiente ciclo.
    print_title("4. Singleton: umbral modificado en tiempo real (cpu -> 95%)")
    MonitoringConfig().set_threshold("cpu", 95.0)
    alertas = monitoreo.run_monitoring(ciclos=1)
    print(f"Alertas generadas: {len(alertas)}")
    print_status(monitoreo)

    # State: el servicio escala de DEGRADADO a CRITICO tras 3 ciclos seguidos en
    # alerta y solo vuelve a SALUDABLE tras 2 ciclos sanos seguidos (histéresis).
    # El umbral de CPU sigue en 95%.
    print_title("5. State: escalamiento, histéresis y mantenimiento")
    inventario = MonitoringFacade(config=configuracion_a)
    inventario.add_alert_channel(LogAlert())
    muestras = [97, 98, 99, 60, 99, 60, 60, 99]
    inventario.register_service(
        "servicio-inventario", LegacyApiAdapter(LegacyMonitoringApi(muestras_cpu=muestras))
    )
    for muestra in muestras[:-1]:
        alertas = inventario.run_monitoring(ciclos=1)
        print(f"CPU {muestra}% -> {inventario.get_status()['servicio-inventario']} ({len(alertas)} alertas)")

    inventario.start_maintenance("servicio-inventario")
    alertas = inventario.run_monitoring(ciclos=1)
    print(f"CPU {muestras[-1]}% en mantenimiento -> {inventario.get_status()['servicio-inventario']} ({len(alertas)} alertas)")
    inventario.end_maintenance("servicio-inventario")
    print_status(inventario)

    # Strategy: tres servicios reciben exactamente las mismas lecturas de CPU, pero
    # cada uno evalúa con una regla distinta. Umbral de CPU: 95%. Sin canales, para
    # ver solo cuántas alertas detecta cada regla por ciclo.
    print_title("6. Strategy: la misma serie de CPU evaluada con tres reglas")
    reglas = {
        "umbral": ThresholdRule(),
        "promedio": MovingAverageRule(ventana=3),
        "pico": SpikeRule(max_incremento=20),
    }
    comparacion = MonitoringFacade(config=configuracion_a)
    serie = [60, 99, 70, 99, 99, 99]
    for nombre, regla in reglas.items():
        comparacion.register_service(
            nombre, LegacyApiAdapter(LegacyMonitoringApi(muestras_cpu=serie)), reglas={"cpu": regla}
        )
    for muestra in serie:
        alertas = comparacion.run_monitoring(ciclos=1)
        por_regla = {nombre: sum(a.nombre_servicio == nombre for a in alertas) for nombre in reglas}
        print(f"CPU {muestra}% -> alertas por regla: {por_regla}")
    print("  umbral: alerta al entrar a cada estado (Degradado no repite) | promedio: solo cuando la carga se sostiene | pico: en cada subida > 20 puntos")


if __name__ == "__main__":
    main()
