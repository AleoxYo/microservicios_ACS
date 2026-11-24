# Bitácora de uso de IA

**Herramienta:** Claude Code (modelo Claude Opus 5.5), usado como asistente / par programador.
**Regla de trabajo:** toda propuesta de la IA se revisa antes de aceptarla. Cada entrada registra el prompt,
lo que propuso la IA, la auditoría del estudiante, la decisión final y, cuando hace falta, la corrección aplicada.
El commit inicial contiene la versión de la IA; cada corrección va en un commit propio, para que el `git diff`
sirva de evidencia del antes y el después.

**Categorías de problema:** `Violación de capa` · `SOLID` · `Patrón mal aplicado` · `Bug` · `Concurrencia` · `Sobre-ingeniería`

---

## Entrada 01 — División del proyecto en fases

- **Fecha:** 2026-11-22
- **Objetivo:** organizar el Proyecto Final 1 sobre el ejercicio 2 (sistema de monitoreo de microservicios) en fases
  progresivas, para avanzar y verificar una cosa a la vez.
- **Prompt:**
  > Divide el proyecto en 7 fases a partir del ejercicio 2 de microservicios, donde cada fase realice una acción progresiva: primero auditar el código existente y migrarlo a arquitectura hexagonal, luego agregar un patrón GoF por fase, y al final la documentación y los diagramas UML.
- **Qué propuso la IA:** 7 fases (0 a 6):

  | Fase | Contenido |
  |---|---|
  | 0 | Copiar el ejercicio 2, `.gitignore` y bitácora |
  | 1 | Corregir los problemas de la auditoría inicial (A1, A2, A4, A5, A6) |
  | 2 | Capas hexagonales y test de arquitectura |
  | 3 | Patrón State |
  | 4 | Patrón Strategy |
  | 5 | Factory Method y configuración en JSON |
  | 6 | UML, documento de arquitectura y README |

- **Auditoría del estudiante:**
  - Cada fase deja el proyecto funcionando y se puede verificar por separado con las pruebas y la demo, así que si
    algo falla se sabe en qué fase se introdujo.
  - Riesgo: poner "un patrón por fase" puede llevar a agregar patrones solo para cumplir; la rúbrica baja a 75 % si
    alguno resulta forzado. Cada patrón tiene que eliminar un problema real del sistema.
  - El plan no tenía tiempos ni fechas.
  - La IA no puede saber si el profesor acepta reutilizar un ejercicio del curso.
- **Decisión final:** se aceptan las 7 fases. El profesor confirmó que se puede reutilizar el ejercicio 2.

## Entrada 02 — Plan de trabajo

- **Fecha:** 2026-11-22
- **Prompt:**
  > Ahora arma el plan detallado de esas fases: qué archivos se crean o modifican en cada una, qué problema de la auditoría corrige, qué patrón aplica y qué pruebas lo verifican.
- **Qué propuso la IA:** estilo Hexagonal; auditoría inicial A1–A7; nuevos patrones State, Strategy y Factory Method
  (Decorator opcional); test de arquitectura; plan por fases (ver [PLAN.md](PLAN.md)).
- **Auditoría del estudiante:**
  - Se comprobó que cada patrón nuevo tiene un problema concreto: State elimina el `if/elif` sobre el estado,
    Strategy el `if` por tipo de regla y Factory Method el `if/elif` al construir desde la configuración.
  - Hexagonal encaja porque el ejercicio ya tenía `interfaces/` (puertos) e `infrastructure/` (adaptadores).
  - El Singleton se suele considerar un antipatrón (estado global, difícil de probar).
- **Decisión final:** se descarta el Decorator opcional para no agregar complejidad innecesaria. El Singleton se
  mantiene, pero se inyecta por el puerto `ConfigProvider` (A1) en vez de llamarse de forma global.

## Entrada 03 — Fases 0, 1 y 2: migración a Hexagonal y correcciones A1, A2, A4, A5, A6

- **Fecha:** 2026-11-22
- **Prompt:**
  > Ahora reorganiza el proyecto en capas hexagonales (domain, ports, application, adapters), agrega un test que verifique automáticamente la regla de dependencias, y corrige los problemas de la auditoría: la dependencia oculta a la configuración, la interfaz con métodos obligatorios innecesarios, la falta de protección entre hilos en el Singleton, los canales que fallan y el detach de observadores no registrados.
- **Qué propuso la IA (resumen de cambios):**

  | Cambio | Archivos |
  |---|---|
  | Carpetas renombradas a `domain / ports / application / adapters` | toda la estructura |
  | **A1** Puerto nuevo `ConfigProvider`; la config se inyecta por constructor en vez de llamar `MonitoringConfig()` por dentro | `ports/config_provider.py`, `application/*.py`, `main.py` |
  | `MonitoringConfig` (Singleton) movido de `domain/` a `adapters/` e implementa `ConfigProvider` | `adapters/monitoring_config.py` |
  | **A2** `MetricsProvider` solo exige `get_metrics()`; se elimina `get_cpu_usage()` | `ports/metrics_provider.py`, `adapters/metrics_adapters.py` |
  | **A4** Lock también en lecturas/escrituras de umbrales e intervalo | `adapters/monitoring_config.py` |
  | **A5** `notify()` captura el error de cada canal y lo registra en el log | `application/service_monitor.py` |
  | **A6** `detach()` ignora observadores no suscritos | `application/service_monitor.py` |
  | Test de arquitectura (regla de dependencias) + pruebas de A1–A6 | `tests/` |

  A3 (separar evaluación y estado) queda para las fases 3–4 (State/Strategy) y A7 (if/switch al construir) para la fase 5 (Factory).

- **Verificación:** `python -m pytest` → 10 pruebas pasan. Se comprobó que el test de arquitectura **falla** si se agrega
  un import prohibido (`domain` → `adapters`). `python main.py` produce el mismo resultado que el ejercicio 2.
- **Auditoría del estudiante:**
  - **Test de arquitectura:** se agregó `import adapters.monitoring_config` en `domain/alert.py` y la prueba falló con
    `domainlert.py importa ['adapters']`. La regla de capas sí se verifica sola.
  - **La prueba de A4 no demuestra la condición de carrera.** Se quitaron todos los `with self._candado_datos:` de
    `adapters/monitoring_config.py` y las 6 pruebas de `test_auditoria_inicial.py` **siguieron pasando**. En CPython
    asignar una clave de un diccionario ya es atómico por el GIL, así que la prueba da una falsa sensación de seguridad.
  - El Singleton en `adapters/` es correcto: guardar la configuración es un detalle de infraestructura y el núcleo
    solo necesita leer umbrales por el puerto.
  - `except Exception` en `notify()` es amplio, pero no oculta el error porque lo registra con `logger.exception`.
  - Quitar `get_cpu_usage()` elimina un método que pedía el ejercicio original; se acepta porque obligaba a todo
    proveedor a tener CPU (ISP).
- **Decisión final:** el lock se queda (protege lecturas compuestas, como copiar el diccionario). La prueba de A4 se
  renombra para que no prometa algo que no verifica.
- **Corrección:** el código lo implementó la IA, a pedido del estudiante y siguiendo su decisión.
  - **Qué estaba mal:** `test_a4_escrituras_concurrentes_no_pierden_umbrales` aparentaba probar el lock, pero sin el
    lock también pasaba.
  - **Cambio:** se renombró a `test_a4_escrituras_concurrentes_no_se_pierden` y se le agregó un comentario que explica
    qué verifica y qué no (`tests/test_auditoria_inicial.py`). No se intentó forzar una condición de carrera porque en
    CPython depende del GIL y daría una prueba inestable.

## Entrada 04 — Fase 3: patrón State (corrige parte de A3)

- **Fecha:** 2026-11-22
- **Prompt:**
  > Ahora implementa el patrón State para el estado de salud de cada microservicio (saludable, degradado, crítico y mantenimiento), con escalamiento tras varios ciclos en alerta e histéresis para la recuperación, de modo que no haya condicionales sobre el estado actual.
- **Problema que se buscaba resolver:** el enum `ServiceStatus` (SALUDABLE/ALERTA) no permite escalamiento,
  histéresis ni mantenimiento sin llenar `Microservice` de `if/elif` sobre el estado actual.
- **Qué propuso la IA (resumen de cambios):**

  | Cambio | Archivos |
  |---|---|
  | Clase abstracta `ServiceState` + `HealthyState`, `DegradedState`, `CriticalState`, `MaintenanceState`. Cada una decide su transición en `on_cycle()` y qué emite en `emit()` | `domain/service_state.py` |
  | `Microservice` pasa a ser el Context: delega en el estado actual; se elimina el enum `ServiceStatus` | `domain/microservice.py` |
  | `Alert` gana `severidad` (`Severity.WARNING` / `CRITICAL`), asignada por el estado | `domain/alert.py` |
  | Fachada: `get_status()` devuelve nombres de estado; nuevos `start_maintenance()` / `end_maintenance()` | `application/monitoring_facade.py` |
  | Demo sección 5 y 11 pruebas nuevas (transiciones, histéresis, severidad, mantenimiento, LSP) | `main.py`, `tests/test_service_state.py` |

  Reglas: 3 ciclos seguidos en alerta → CRITICO; desde CRITICO se necesitan 2 ciclos sanos seguidos para volver a SALUDABLE.

- **Verificación:** `python -m pytest` → 21 pruebas pasan (incluido el test de arquitectura: `service_state.py`
  solo importa de `domain`). La demo muestra 97→98→99% = DEGRADADO, DEGRADADO, CRITICO; un 60% aislado no lo saca de CRITICO.
- **Auditoría del estudiante:**
  - **DEGRADADO repetía la advertencia en cada ciclo**, así que el *flapping* no quedaba resuelto (ver Corrección).
  - Cada estado tiene un `if alertas`, pero eso pregunta por el **dato** del ciclo, no por el **tipo** de estado; el
    `if/elif` sobre el estado actual sí desapareció de `Microservice`.
  - `ServiceState.emit()` decide con `if self.severidad is None` en vez de que cada estado sobrescriba `emit()`.
  - `CYCLES_TO_CRITICAL = 3` y `CYCLES_TO_RECOVER = 2` están fijos en el código; no se pueden configurar.
  - Crear un objeto de estado nuevo en cada transición se acepta: los estados son casi inmutables y fáciles de probar.
- **Corrección:** el código lo implementó la IA, a pedido del estudiante y siguiendo su decisión.
  - **Qué estaba mal:** DEGRADADO enviaba una advertencia en **cada** ciclo con la métrica alta, no solo al entrar.
    Era el mismo aviso repetido, así que el *flapping* no quedaba resuelto.
  - **Evidencia antes del cambio:**
    - Demo, sección 5: `CPU 98% -> DEGRADADO (1 alertas)`. El servicio ya estaba en DEGRADADO y volvió a avisar.
    - Prueba nueva `test_degradado_avisa_solo_al_entrar`: falló con `AssertionError: assert [Alert(...)] == []`.
  - **Cambio:** `DegradedState` sobrescribe `emit()` y devuelve `[]` cuando `ciclos_en_alerta > 1`
    (`domain/service_state.py`). No se tocó `Microservice` ni los otros estados: el cambio queda dentro del estado,
    que es lo que permite el patrón State.
  - **Evidencia después:** 45 pruebas pasan. En la sección 5 la línea queda `CPU 98% -> DEGRADADO (0 alertas)`.
    En la sección 6, la regla `umbral` baja de 4 a 3 alertas, porque esa demo también pasa por los estados.
  - **Decisión del estudiante:** CRITICO **sigue avisando en cada ciclo** con la métrica alta. Un servicio crítico
    debe seguir avisando hasta que alguien lo atienda.

## Entrada 05 — Fase 4: patrón Strategy (cierra A3)

- **Fecha:** 2026-11-22
- **Prompt:**
  > Ahora implementa el patrón Strategy para que cada métrica pueda evaluarse con una regla distinta (valor actual, promedio móvil o subida brusca), y separa la evaluación de métricas de la gestión del estado del servicio.
- **Problema que se buscaba resolver:** la única regla era "valor actual > umbral" y estaba dentro de
  `Microservice.evaluate()`, junto con el cambio de estado (SRP). Un pico aislado ya alertaba y una subida brusca
  bajo el umbral pasaba desapercibida; agregar otra regla obligaba a modificar esa clase (OCP).
- **Qué propuso la IA (resumen de cambios):**

  | Cambio | Archivos |
  |---|---|
  | Strategy abstracta `EvaluationRule` + `ThresholdRule`, `MovingAverageRule(ventana)`, `SpikeRule(max_incremento)`; resultado `Violation(valor, limite)` | `domain/evaluation_rules.py` |
  | `MetricEvaluator` (Context del Strategy): guarda el historial por métrica (máx. 10 lecturas) y aplica la regla de cada métrica; `ThresholdRule` por defecto | `domain/metric_evaluator.py` |
  | **A3 cerrado:** `Microservice.evaluate()` se reemplaza por `record_cycle(detectadas)`; ya solo maneja estado | `domain/microservice.py` |
  | `ServiceMonitor.check()` coordina: Adapter → Strategy → State → Observer | `application/service_monitor.py` |
  | `register_service(..., reglas={"cpu": MovingAverageRule(3)})` en la fachada | `application/monitoring_facade.py` |
  | `Alert` gana `criterio` (lo pone la regla); el mensaje dice "supera el límite" | `domain/alert.py` |
  | Demo sección 6 (misma serie de CPU con 3 reglas) y 13 pruebas nuevas, incluida una regla creada dentro del test para demostrar OCP | `main.py`, `tests/test_evaluation_rules.py` |

- **Verificación:** `python -m pytest` → 34 pruebas pasan. En la demo, con la serie 60, 99, 70, 99, 99, 99 y umbral 95%:
  `umbral` alerta 4 veces, `promedio` solo 1 (cuando la carga se sostiene) y `pico` 2 (en las subidas de 60→99 y 70→99).
- **Auditoría del estudiante:**
  - Se calculó a mano la sección 6 con umbral 95 %: el promedio de (99, 70, 99) es 89,3 y no alerta; el de
    (99, 99, 99) es 99 y sí alerta. Coincide con la demo (`promedio`: 1 alerta).
  - **`ServiceMonitor` vuelve a crear una dependencia por dentro:** `evaluador or MetricEvaluator(servicio.nombre)`
    (`application/service_monitor.py:25`). Es el mismo problema que se corrigió en A1.
  - **El mensaje de la regla de pico es engañoso:** `cpu (subida en un ciclo) en 39.0% supera el límite de 20.0%`.
    Son 39 **puntos** de subida, no un porcentaje; además el campo `Alert.umbral` guarda un incremento.
  - `SpikeRule.evaluate()` recibe `umbral` y no lo usa; es dudoso frente a LSP, porque el contrato de `evaluate()`
    dice que evalúa contra un umbral.
- **Decisión final:** hacer obligatorio el parámetro `evaluador`. El mensaje de la regla de pico queda como limitación
  documentada.
- **Corrección:** el código lo implementó la IA, a pedido del estudiante y siguiendo su decisión.
  - **Qué estaba mal:** `ServiceMonitor` creaba su propio `MetricEvaluator` si no se lo pasaban
    (`evaluador or MetricEvaluator(...)`): una dependencia oculta, el mismo error que se había corregido en A1.
  - **Evidencia antes del cambio:** la prueba nueva `test_monitor_exige_que_le_inyecten_el_evaluador` falló con
    `Failed: DID NOT RAISE <class 'TypeError'>`, es decir, el monitor se creaba sin evaluador.
  - **Cambio:** `evaluador` pasa a ser un parámetro obligatorio de `ServiceMonitor.__init__`
    (`application/service_monitor.py`). La fachada ya lo pasaba, así que no cambió; las pruebas de A5 y A6 ahora lo
    inyectan explícitamente.
  - **Evidencia después:** 46 pruebas pasan y la salida de `main.py` no cambia.

## Entrada 06 — Fase 5: Factory Method + configuración JSON (cierra A7)

- **Fecha:** 2026-11-22
- **Prompt:**
  > Ahora implementa Factory Method para crear canales de alerta, proveedores de métricas y reglas de evaluación a partir de un archivo JSON, usando un registro de fábricas en vez de cadenas de if/elif por tipo.
- **Problema que se buscaba resolver:** `main.py` construía cada canal, API, adapter y regla a mano. Para armar el
  sistema desde un archivo hay que traducir `"email"` → `EmailAlert`, `"legacy"` → `LegacyApiAdapter`, etc.;
  hacerlo con `if/elif` sobre el tipo obliga a modificar esa cadena con cada tipo nuevo (OCP).
- **Qué propuso la IA (resumen de cambios):**

  | Cambio | Archivos |
  |---|---|
  | Creator abstracto `Factory[T]` con el método fábrica `create(parametros)`; 8 fábricas concretas (3 canales, 2 proveedores, 3 reglas) | `adapters/factories.py` |
  | `FactoryRegistry[T]`: asocia nombre de tipo → fábrica (búsqueda en diccionario, sin `if/elif`); errores claros para tipo desconocido o parámetro faltante | `adapters/factories.py` |
  | `JsonConfigLoader`: lee el JSON, aplica umbrales/intervalo a la config y devuelve una `SystemDefinition` (no importa `application/`; el cableado lo hace `main.py`) | `adapters/json_config_loader.py` |
  | Archivo de configuración del sistema | `config/servicios.json` |
  | La sección 3 de la demo se arma desde el JSON | `main.py` |
  | 10 pruebas nuevas, incluida una que registra un canal "teams" nuevo sin tocar las fábricas (OCP) | `tests/test_factories.py` |

- **Verificación:** `python -m pytest` → 44 pruebas pasan (el test de arquitectura confirma que el cargador no importa
  `application/`). La salida de la sección 3 es idéntica a la versión armada a mano.
- **Auditoría del estudiante:**
  - Se cambió un canal a `"tipo": "sms"` y apareció el error con los tipos disponibles; no hay `elif` en el código
    de `domain/`, `application/` ni `adapters/`.
  - **¿Es Factory Method?** En GoF el Creator tiene una operación propia que usa el método fábrica. Aquí `Factory`
    solo tiene `create()` y se elige por un registro, así que se parece más a una "Simple Factory con registro".
  - **Pruebas y Singleton:** las pruebas comparten la instancia. Se ejecutaron en otro orden y archivo por archivo
    y todas pasaron, pero el aislamiento depende de que no reutilicen los mismos umbrales.
  - `JsonConfigLoader.load()` construye objetos **y** modifica la configuración global: son dos responsabilidades (SRP).
  - `FactoryRegistry.create()` convierte cualquier `KeyError` en "Falta el parámetro", y dos servicios con el mismo
    nombre se reemplazan sin avisar.
- **Decisión final:** se mantiene y se justifica como Factory Method: `Factory[T]` es el Creator abstracto que declara
  el método fábrica `create()`, y cada fábrica concreta (ConcreteCreator) decide qué producto crea. La diferencia con
  el GoF clásico es que el Creator no tiene una operación propia que use `create()`; agregarla solo para cumplir la
  forma sería complejidad innecesaria. No es Abstract Factory porque no crea familias de productos relacionados.
  Los demás puntos quedan como limitaciones documentadas.
- **Corrección:** no aplica. Se decidió mantener el diseño y justificarlo (ver decisión final).

## Entrada 07 — Fase 6: diagramas UML, documento de arquitectura y README

- **Fecha:** 2026-11-22
- **Prompt:**
  > Ahora crea los diagramas UML en Mermaid (componentes, clases, secuencia de un ciclo y estados del servicio), el documento de arquitectura con la justificación del estilo, los patrones, SOLID y las decisiones de diseño, y actualiza el README.
- **Qué propuso la IA (resumen de cambios):**

  | Cambio | Archivos |
  |---|---|
  | Diagrama de componentes (hexágono, puertos y dirección de dependencias) | `docs/uml/componentes.mmd` |
  | Diagramas de clases: núcleo (domain/ports/application) y adaptadores/fábricas, con el rol de cada clase como estereotipo | `docs/uml/clases_nucleo.mmd`, `docs/uml/clases_adaptadores.mmd` |
  | Diagrama de secuencia de un ciclo (Facade → Adapter → Strategy → State → Observer) | `docs/uml/secuencia_ciclo.mmd` |
  | Diagrama de estados del patrón State | `docs/uml/estados_servicio.mmd` |
  | Documento de arquitectura: problema, justificación de Hexagonal frente a Capas / Eventos / Microservicios, flujo de datos, tabla de patrones, SOLID con evidencia, decisiones de diseño, limitaciones. Incluye los 5 diagramas | `docs/arquitectura.md` |
  | README final: ejecución, estructura, formato del JSON, cómo extender | `README.md` |

- **Verificación:** los diagramas **no se pudieron renderizar localmente** (la ejecución de `mermaid-cli` vía `npx` no
  fue autorizada), así que su sintaxis no está validada con una herramienta. Hay que revisarlos en GitHub o en
  https://mermaid.live antes de la entrega.
- **Auditoría del estudiante:**
  - Se compararon los nombres de clases y métodos de `clases_nucleo.mmd` con el código y coinciden.
  - `Microservice o-- ServiceState` está como agregación, pero el estado lo crea y lo reemplaza el propio servicio:
    debería ser composición (`*--`).
  - La sintaxis de los diagramas no se validó con una herramienta. Se revisaron en GitHub y los 5 diagramas se dibujan correctamente.
  - La justificación de por qué no se eligió arquitectura dirigida por eventos hay que poder explicarla en la defensa.
- **Decisión final:** cambiar la relación a composición.
- **Corrección:** el cambio lo implementó la IA, a pedido del estudiante y siguiendo su decisión.
  - **Qué estaba mal:** `Microservice o-- ServiceState` estaba dibujado como agregación, pero el estado no existe
    por fuera del servicio: `Microservice` lo crea al iniciar y lo reemplaza en cada transición.
  - **Cambio:** la relación pasa a composición (`*--`) en `docs/uml/clases_nucleo.mmd` y en `docs/arquitectura.md`.

---

<!-- Plantilla para nuevas entradas
## Entrada NN — Título
- **Fecha:**
- **Objetivo:**
- **Prompt:**
- **Qué propuso la IA:**
- **Problemas detectados:** (qué, dónde, categoría)
- **Corrección manual:** (qué cambié y por qué)
- **Commits:** `abc123` (IA) → `def456` (corrección)
-->
