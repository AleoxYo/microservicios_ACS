# Bitácora de uso de IA

**Herramienta:** Claude Code (modelo Claude Opus 5.5), usado como asistente / par programador.
**Regla de trabajo:** toda propuesta de la IA se revisa antes de aceptarla. Cada entrada registra el prompt literal,
lo que propuso la IA, los problemas que yo (el estudiante) detecté y la corrección manual aplicada.
Cuando hay código, se hace un commit con la versión de la IA y otro con la corrección, para que el `git diff` sirva de evidencia.

**Categorías de problema:** `Violación de capa` · `SOLID` · `Patrón mal aplicado` · `Bug` · `Concurrencia` · `Sobre-ingeniería`

---

## Entrada 01 — Elección del proyecto

- **Fecha:** 2026-11-22
- **Objetivo:** decidir entre Proyecto Final 1 (estilos/SOLID/GoF) y Proyecto Final 2 (servidor concurrente).
- **Prompt (literal):**
  > lee el documento que esta en la carpeta (ProyectoFinalRubirca.pdf) y dime de las dos opciones de proyecto cual es mas facil de resolver y de sustentar ? para la primera opcion se podria utilizar un proyecto que ya se tenga y aplicar lo que se menciona en e lpdf, pero no sé, si esa es la opcion mas facil, que tan viable sea coger un proyecto anterior o empezar uno
- **Qué propuso la IA:** Proyecto 1, reutilizando el ejercicio 2 (sistema de monitoreo), que ya tenía capas y 4 patrones GoF.
- **Auditoría del estudiante:** _(completar: ¿estoy de acuerdo? ¿qué riesgos veo? ¿consulté al profesor sobre reutilizar el ejercicio?)_
- **Decisión final:** _(completar)_

## Entrada 02 — Plan de trabajo

- **Fecha:** 2026-11-22
- **Prompt (literal):**
  > sí, arma el plan sobre el ejercicio 2
- **Qué propuso la IA:** estilo Hexagonal; auditoría inicial A1–A7; nuevos patrones State, Strategy y Factory Method
  (Decorator opcional); test de arquitectura; plan por fases (ver [PLAN.md](PLAN.md)).
- **Auditoría del estudiante:** _(completar: ¿algún patrón propuesto es forzado? ¿Hexagonal o Capas? justificar)_

## Entrada 03 — Fases 0, 1 y 2: migración a Hexagonal y correcciones A1, A2, A4, A5, A6

- **Fecha:** 2026-11-22
- **Prompt (literal):**
  > ok entonces empieza con las primeras fases
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
- **Auditoría del estudiante:** _(completar. Puntos sugeridos para revisar tú mismo:)_
  - ¿Es correcto que el Singleton viva en `adapters/` y no en `domain/`? ¿Qué responderías si el profesor lo cuestiona?
  - ¿La prueba de A4 demuestra de verdad una condición de carrera, o pasaría también sin el lock?
  - ¿Capturar `Exception` en `notify()` es demasiado amplio?
  - ¿Eliminar `get_cpu_usage()` rompe algo que pedía el enunciado original?
- **Corrección manual:** _(completar con lo que cambies y el hash de los commits antes/después)_

## Entrada 04 — Fase 3: patrón State (corrige parte de A3)

- **Fecha:** 2026-11-22
- **Prompt (literal):**
  > sigue con la fase 3
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
- **Auditoría del estudiante:** _(completar. Puntos sugeridos para revisar tú mismo:)_
  - ¿El State elimina de verdad el *flapping*? Revisa qué pasa con las alertas mientras el servicio sigue en DEGRADADO varios ciclos.
  - Cada estado sigue teniendo un `if alertas`. ¿Eso contradice "eliminar condicionales", o es aceptable? ¿Cuál es la diferencia con un `if` sobre el *tipo* de estado?
  - `ServiceState.emit()` decide con `if self.severidad is None`. ¿Debería ser polimorfismo (sobrescribir `emit` en cada estado)?
  - `nombre` está declarado como propiedad abstracta, pero las subclases lo definen como atributo de clase. ¿Es correcto o confuso?
  - `CYCLES_TO_CRITICAL` y `CYCLES_TO_RECOVER` son constantes fijas. ¿Deberían venir de la configuración (`ConfigProvider`)?
  - Se crea un objeto de estado nuevo en cada transición. ¿Es un problema o una ventaja (inmutabilidad)?
- **Corrección manual:** _(completar)_

## Entrada 05 — Fase 4: patrón Strategy (cierra A3)

- **Fecha:** 2026-11-22
- **Prompt (literal):**
  > sigue con la fase 4
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
- **Auditoría del estudiante:** _(completar. Puntos sugeridos para revisar tú mismo:)_
  - `SpikeRule` recibe `umbral` pero lo ignora y usa su propio límite. ¿Eso respeta LSP o el contrato de `evaluate()` está mal definido?
  - Para que `SpikeRule` evalúe una métrica, esa métrica igual necesita un umbral configurado (`MetricEvaluator` salta las que no lo tienen). ¿Es coherente?
  - El campo `Alert.umbral` ahora a veces guarda un incremento, no un umbral; y el mensaje de pico muestra "35.0%" cuando son *puntos*. ¿Renombrar el campo / ajustar el mensaje?
  - `MovingAverageRule.criterio` es una propiedad y en `ThresholdRule`/`SpikeRule` es atributo de clase. ¿Unificar?
  - `ServiceMonitor` crea un `MetricEvaluator` por defecto si no se lo pasan (`evaluador or MetricEvaluator(...)`). ¿Es una dependencia oculta como la de A1?
- **Corrección manual:** _(completar)_

## Entrada 06 — Fase 5: Factory Method + configuración JSON (cierra A7)

- **Fecha:** 2026-11-22
- **Prompt (literal):**
  > vale, sigamos con la fase 5
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
- **Auditoría del estudiante:** _(completar. Puntos sugeridos para revisar tú mismo:)_
  - **¿Es realmente Factory Method?** En GoF, el Creator tiene una operación propia que *usa* el método fábrica y las subclases deciden qué se crea. Aquí `Factory` solo tiene `create()` y se elige por un registro. ¿Es Factory Method, "Simple Factory + registro" u otra cosa? Prepara la respuesta: el profesor puede preguntarlo.
  - Las pruebas comparten el Singleton: `test_carga_el_json...` cambia el intervalo y los umbrales globales, y `test_a4` agrega 200 métricas. ¿Pueden afectar a otras pruebas según el orden? ¿Cómo aislarlas?
  - `JsonConfigLoader.load()` construye objetos **y** modifica la configuración global (efecto secundario). ¿Viola SRP?
  - `FactoryRegistry.create()` convierte cualquier `KeyError` en "Falta el parámetro". ¿Puede ocultar un `KeyError` que venga de otro lado?
  - Si el JSON trae dos servicios con el mismo nombre, el segundo reemplaza al primero sin avisar. ¿Validarlo?
- **Corrección manual:** _(completar)_

## Entrada 07 — Fase 6: diagramas UML, documento de arquitectura y README

- **Fecha:** 2026-11-22
- **Prompt (literal):**
  > sigue con la fase 6
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
- **Auditoría del estudiante:** _(completar. Puntos sugeridos para revisar tú mismo:)_
  - ¿Los diagramas de clases coinciden con el código real (nombres, métodos, multiplicidades)? La rúbrica penaliza un UML "desacoplado de la implementación".
  - ¿La justificación de por qué **no** se eligió arquitectura dirigida por eventos es convincente? (Hiciste una exposición sobre ese estilo; el profesor puede preguntarlo.)
  - ¿Las relaciones del diagrama (composición `*--` vs agregación `o--`) son correctas? Por ejemplo, ¿`Microservice o-- ServiceState` debería ser composición?
  - ¿Algo en `docs/arquitectura.md` afirma algo que el código no cumple?
- **Corrección manual:** _(completar)_

## Entrada 08 — Fase 7: guía de sustentación

- **Fecha:** 2026-11-22
- **Prompt (literal):**
  > sigue con la fase 7
- **Qué propuso la IA:** `docs/defensa.md` con un guion de 10 minutos, 4 demos preparadas (incluida romper la
  arquitectura en vivo), preguntas probables con respuestas cortas para cada criterio de la rúbrica, una tabla con los
  problemas detectados en el código de la IA (entradas 03–06) que quedan por corregir y un checklist de entrega.
- **Auditoría del estudiante:** _(completar: ¿alguna respuesta de la guía es incorrecta o no la entiendo bien? ¿cuáles
  de los problemas de la tabla corregí?)_

---

<!-- Plantilla para nuevas entradas
## Entrada NN — Título
- **Fecha:**
- **Objetivo:**
- **Prompt (literal):**
- **Qué propuso la IA:**
- **Problemas detectados:** (qué, dónde, categoría)
- **Corrección manual:** (qué cambié y por qué)
- **Commits:** `abc123` (IA) → `def456` (corrección)
-->
