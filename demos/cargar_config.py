"""Demo: cambiar el comportamiento del sistema solo con el archivo JSON, sin tocar código.

Arma el sistema desde el archivo indicado (Factory Method) y ejecuta 3 ciclos de
monitoreo. Comparar la salida de dos archivos muestra que el cambio está solo en
la configuración.

Uso, desde la carpeta del proyecto:
    python -m demos.cargar_config config/servicios.json
    python -m demos.cargar_config demos/config/regla_promedio.json
    python -m demos.cargar_config demos/config/canal_desconocido.json
"""

import logging
import sys
from pathlib import Path

from adapters.json_config_loader import JsonConfigLoader
from adapters.monitoring_config import MonitoringConfig
from application.monitoring_facade import MonitoringFacade


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python -m demos.cargar_config <archivo.json>")
        sys.exit(1)
    ruta = Path(sys.argv[1])
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="  [LOG %(levelname)s] %(message)s")

    print(f"=== Sistema armado desde {ruta} ===")
    config = MonitoringConfig()
    try:
        sistema = JsonConfigLoader(config).load_file(ruta)
    except ValueError as error:
        print(f"Error en la configuración: {error}")
        sys.exit(1)

    config.check_interval_seconds = 0  # sin esperas entre ciclos durante la demo
    monitoreo = MonitoringFacade(config=config)
    for canal in sistema.canales:
        monitoreo.add_alert_channel(canal)
    for servicio in sistema.servicios:
        monitoreo.register_service(servicio.nombre, servicio.proveedor, servicio.reglas)

    alertas = monitoreo.run_monitoring(ciclos=3)
    print(f"\nAlertas generadas en 3 ciclos: {len(alertas)}")
    print(f"Estado final: {monitoreo.get_status()}")


if __name__ == "__main__":
    main()
