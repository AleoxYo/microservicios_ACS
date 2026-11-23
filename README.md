# Sistema de Monitoreo de Microservicios

**Proyecto Final 1 — IS294 Arquitectura Cliente Servidor** · Estilos Arquitectónicos, SOLID y Patrones GoF
(desarrollo asistido por IA).

Plataforma que lee métricas de microservicios desde APIs externas con formatos distintos, las evalúa con reglas
configurables por métrica, mantiene el estado de salud de cada servicio (con escalamiento e histéresis) y envía alertas
por varios canales. Todo el sistema se arma desde un archivo JSON.

- **Estilo arquitectónico:** Hexagonal (Puertos y Adaptadores), verificado automáticamente con un test de arquitectura.
- **Patrones GoF:** Adapter, Facade, Observer, Singleton, State, Strategy y Factory Method.
- **Documentación completa:** [docs/arquitectura.md](docs/arquitectura.md) (justificación, diagramas UML, SOLID, decisiones).

## Ejecución

Requiere Python 3.10+ (solo librería estándar); `pytest` para las pruebas.

```bash
python main.py          # demostración de los 7 patrones (6 secciones)
python -m pytest        # 44 pruebas, incluido el test de arquitectura
```

## Estructura

```
domain/        Núcleo del negocio. No depende de nada.
  alert.py               Alert, Severity
  service_state.py       ServiceState + 4 estados              (State)
  microservice.py        Microservice: Context del State
  evaluation_rules.py    EvaluationRule + 3 reglas, Violation  (Strategy)
  metric_evaluator.py    MetricEvaluator: Context del Strategy
ports/         Contratos que define el núcleo.
  metrics_provider.py    MetricsProvider                       (Target del Adapter)
  alert_observer.py      AlertObserver                         (Observer)
  config_provider.py     ConfigProvider
application/   Casos de uso.
  service_monitor.py     ServiceMonitor: un ciclo de monitoreo (Subject del Observer)
  monitoring_facade.py   MonitoringFacade: punto único de entrada (Facade)
adapters/      Conexión con el exterior.
  external_apis.py       APIs externas simuladas               (Adaptees)
  metrics_adapters.py    LegacyApiAdapter, CloudApiAdapter      (Adapter)
  alert_channels.py      EmailAlert, SlackAlert, LogAlert       (Concrete Observers)
  monitoring_config.py   MonitoringConfig                      (Singleton)
  factories.py           Factory, FactoryRegistry, 8 fábricas  (Factory Method)
  json_config_loader.py  JsonConfigLoader: arma el sistema desde JSON
config/servicios.json  Umbrales, intervalo, canales, servicios y reglas.
main.py        Composition root: único lugar que conoce las clases concretas.
tests/         Pruebas por patrón + test_arquitectura.py.
docs/          Arquitectura, UML (docs/uml/*.mmd), plan y bitácora de IA.
```

Regla de dependencias: `domain` ← `ports` ← `application`; `adapters` implementa los `ports` y nunca importa
`application`. Si se rompe, `tests/test_arquitectura.py` falla.

## Configuración

`config/servicios.json` define todo el sistema:

```json
{
  "monitoreo": { "intervalo_segundos": 0.5, "umbrales": { "cpu": 80, "memoria": 85 } },
  "canales": [
    { "tipo": "email", "destinatario": "ops@fintech.com" },
    { "tipo": "log" }
  ],
  "servicios": [
    {
      "nombre": "servicio-autenticacion",
      "proveedor": { "tipo": "cloud", "muestras": [[0.45, 0.70], [0.82, 0.91]] },
      "reglas": { "memoria": { "tipo": "promedio", "ventana": 3 } }
    }
  ]
}
```

| Familia | Tipos disponibles | Parámetros |
|---|---|---|
| Canales | `email`, `slack`, `log` | `destinatario` · `canal` · `logger` (opcional) |
| Proveedores | `legacy`, `cloud` | `muestras_cpu` · `muestras` (pares cpu/memoria en fracción) |
| Reglas | `umbral`, `promedio`, `pico` | — · `ventana` (2–10) · `max_incremento` |

Las métricas sin regla usan `umbral` (valor actual > umbral).

## Cómo extender sin modificar código existente

Ejemplo, un canal de Microsoft Teams:

1. Crear `TeamsAlert(AlertObserver)` en `adapters/alert_channels.py` con su `update()`.
2. Crear `TeamsChannelFactory(Factory[AlertObserver])` con su `create()`.
3. Registrar: `registros.canales.register("teams", TeamsChannelFactory())`.
4. Usarlo en el JSON: `{ "tipo": "teams", "webhook": "..." }`.

Lo mismo aplica para una regla de evaluación nueva (`EvaluationRule`), un proveedor nuevo (`MetricsProvider`) o un
estado nuevo (`ServiceState`). Las pruebas `test_ocp_*` lo demuestran.

## Documentación

- [Arquitectura: estilo, patrones, SOLID, diagramas UML y decisiones](docs/arquitectura.md)
- [Diagramas UML fuente (Mermaid)](docs/uml/)
- [Bitácora de uso de IA](docs/bitacora_ia.md)
- [Plan y estado de avance](docs/PLAN.md)
- [Guía de sustentación](docs/defensa.md)
