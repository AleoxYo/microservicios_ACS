from threading import Lock

from ports.config_provider import ConfigProvider


class MonitoringConfig(ConfigProvider):
    """Adaptador de configuración en memoria (Singleton).

    Toda llamada a MonitoringConfig() devuelve la misma instancia, así todos
    los monitores leen y modifican los mismos umbrales en tiempo real.

    Se movió de domain/ a adapters/: guardar la configuración es un detalle de
    infraestructura; el núcleo solo conoce el puerto ConfigProvider (A1).
    """

    _instancia: "MonitoringConfig | None" = None
    _candado_creacion = Lock()

    def __new__(cls) -> "MonitoringConfig":
        with cls._candado_creacion:
            if cls._instancia is None:
                instancia = super().__new__(cls)
                instancia._umbrales = {"cpu": 80.0}
                instancia._intervalo_segundos = 1.0
                # A4: antes el lock solo protegía la creación; las lecturas y
                # escrituras de umbrales quedaban expuestas a condiciones de carrera.
                instancia._candado_datos = Lock()
                cls._instancia = instancia
        return cls._instancia

    def get_threshold(self, metrica: str) -> float | None:
        with self._candado_datos:
            return self._umbrales.get(metrica)

    def set_threshold(self, metrica: str, porcentaje: float) -> None:
        if not 0 <= porcentaje <= 100:
            raise ValueError("El umbral debe ser un porcentaje entre 0 y 100")
        with self._candado_datos:
            self._umbrales[metrica] = porcentaje

    def get_thresholds(self) -> dict[str, float]:
        with self._candado_datos:
            return dict(self._umbrales)

    @property
    def check_interval_seconds(self) -> float:
        with self._candado_datos:
            return self._intervalo_segundos

    @check_interval_seconds.setter
    def check_interval_seconds(self, segundos: float) -> None:
        if segundos < 0:
            raise ValueError("El intervalo no puede ser negativo")
        with self._candado_datos:
            self._intervalo_segundos = segundos
