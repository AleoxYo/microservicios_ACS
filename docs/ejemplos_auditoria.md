# Ejemplos de "Auditoría del estudiante" (generados por la IA como guía)

> **Esto es un modelo de cómo se escribe una auditoría, no tu auditoría.** Lo generó la IA para mostrar la forma.
> Antes de pasar algo a `bitacora_ia.md`:
> 1. **Haz de verdad cada verificación** que se menciona (ejecutar el comando, mirar la salida, probar el cambio).
>    No escribas "comprobé X" si no lo comprobaste: el profesor puede pedirte que lo repitas en la defensa.
> 2. **Reemplaza lo que está entre `[corchetes]`** con lo que viste y con tu opinión real.
> 3. **Cambia lo que no compartas.** Si no estás de acuerdo con un punto, eso también es auditoría, y vale más.
> 4. **Escríbelo con tus palabras.** Si es la primera vez que ves un problema, está bien decir "la IA lo señaló y lo verifiqué así".
>
> Decide si este archivo va en el repositorio que entregas o lo sacas antes.

Patrón de cada ejemplo:
1. **Cómo lo revisé**
2. **Qué acepté y por qué**
3. **Qué está mal o qué me genera duda**
4. **Decisión**

---

## Entrada 01 — Elección del proyecto

- **Cómo lo revisé:** leí las dos rúbricas del PDF y comparé los criterios. El Proyecto 2 pide sockets, concurrencia,
  manejo de señales y pruebas de carga en vivo; el Proyecto 1 pide estilo, SOLID y patrones. Revisé el ejercicio 2
  para confirmar lo que dijo la IA: tiene carpetas separadas y 4 patrones (Singleton, Adapter, Facade, Observer).
- **Qué acepté y por qué:** el Proyecto 1 partiendo del ejercicio 2. Ya conozco ese código, y la defensa del
  Proyecto 2 incluye preguntas sobre el kernel y las colas de conexión, que [domino menos / no vimos a fondo].
- **Qué está mal o qué me genera duda:**
  - La IA no sabía si el profesor acepta reutilizar un ejercicio del curso; lo mencionó, pero no lo puede resolver.
  - El ejercicio era pequeño (unas 376 líneas), así que había que ampliarlo bastante para un proyecto final.
  - La IA comparó solo por facilidad; no consideró cuál me sirve más para aprender.
- **Decisión:** Proyecto 1. [Consulté al profesor el día ___ y respondió ___ / Lo consultaré antes de la entrega.]

## Entrada 02 — Plan de trabajo

- **Cómo lo revisé:** puse cada fase del plan junto al criterio de la rúbrica que ataca, y verifiqué que cada patrón
  nuevo tuviera un problema concreto del sistema y no fuera "para cumplir".
- **Qué acepté y por qué:** el estilo Hexagonal, porque el ejercicio ya tenía `interfaces/` (que son los puertos) e
  `infrastructure/` (que son los adaptadores); solo había que formalizarlo. Acepté State, Strategy y Factory Method
  porque cada uno elimina un `if/elif` real.
- **Qué está mal o qué me genera duda:**
  - Con 7 patrones existe el riesgo de que alguno parezca forzado; la rúbrica baja a 75 % si "la integración de alguno
    resulta forzada o añade complejidad innecesaria".
  - El Singleton se suele considerar un antipatrón y el plan lo mantiene.
  - El plan no tenía tiempos ni fechas.
- **Decisión:** descarté el Decorator opcional para no agregar complejidad. Mantengo el Singleton, pero inyectado (A1),
  y en la defensa voy a destacar [State, Strategy y Factory Method].

## Entrada 03 — Fases 0, 1 y 2 (Hexagonal y correcciones A1–A6)

- **Cómo lo revisé:**
  - Ejecuté `python -m pytest` (10 pruebas pasaron) y `python main.py`, y comparé la salida con la del ejercicio
    original: las mismas 3 alertas y después 0.
  - Agregué a mano un `import` de `adapters` dentro de `domain/` y confirmé que `test_arquitectura.py` falla.
  - Para la prueba de A4, **quité el `with self._candado_datos:` de `set_threshold()` y volví a ejecutar la prueba.**
    [Resultado que obtuviste: ¿pasó o falló?]
- **Qué acepté y por qué:** el puerto `ConfigProvider` (A1), porque ahora puedo probar la fachada con una
  configuración falsa (`ConfigFija`), y antes no se podía. También acepté dejar solo `get_metrics()` (A2).
- **Qué está mal o qué me genera duda:**
  - **La prueba de A4 no demuestra la condición de carrera:** [si pasó sin el lock] pasa igual sin el lock, porque en
    CPython asignar una clave en un diccionario ya es atómico gracias al GIL. La prueba da una falsa sensación de
    seguridad.
  - `except Exception` en `notify()` es muy amplio, pero como registra el error con `logger.exception`, no lo oculta.
  - Al quitar `get_cpu_usage()` se pierde un método que pedía el enunciado del ejercicio 2.
- **Decisión:** el lock se queda, porque protege también lecturas compuestas como copiar el diccionario. La prueba de A4
  la [corrijo / renombro y documento que solo verifica que no se pierdan escrituras]. `except Exception` se queda.

## Entrada 04 — Fase 3 (patrón State)

- **Cómo lo revisé:** ejecuté `python main.py` y miré la sección 5; leí `domain/service_state.py` y ejecuté las pruebas
  (21 pasaron). Confirmé la histéresis: con 97, 98, 99 y luego 60 %, el servicio sigue en CRITICO.
- **Qué acepté y por qué:** el patrón, porque `Microservice` ya no tiene ningún `if` que pregunte en qué estado está;
  cada estado decide su transición. Agregar un estado nuevo no toca los demás.
- **Qué está mal o qué me genera duda:**
  - **El flapping no se resuelve del todo.** En la salida de la sección 5 se ve `CPU 98% -> DEGRADADO (1 alertas)`: el
    servicio ya estaba en DEGRADADO y aun así volvió a alertar. Mientras siga ahí, manda una advertencia por ciclo,
    aunque la IA presentó el patrón como solución al flapping.
  - `emit()` decide con `if self.severidad is None`, en vez de que cada estado sobrescriba `emit()`.
  - Los números 3 y 2 (ciclos para CRITICO y para recuperarse) están fijos en el código.
- **Decisión:** corregir DEGRADADO para que avise solo cuando entra al estado [ver entrada 09]. Las constantes las
  dejo documentadas como limitación.

## Entrada 05 — Fase 4 (patrón Strategy)

- **Cómo lo revisé:** calculé a mano la sección 6 de la demo. Con umbral de 95 %, el promedio de (99, 70, 99) es 89,3, que
  no alerta, y el de (99, 99, 99) es 99, que sí alerta; coincide con "promedio: 1 alerta". Ejecuté las pruebas (34 pasaron).
- **Qué acepté y por qué:** separar `MetricEvaluator` de `Microservice`, porque cierra A3: ahora cada clase tiene una
  sola razón para cambiar. También que las reglas no guarden estado, porque así se pueden compartir y probar fácil.
- **Qué está mal o qué me genera duda:**
  - **`ServiceMonitor` vuelve a crear una dependencia por dentro:** `evaluador or MetricEvaluator(...)`. Es el mismo
    problema que se corrigió en A1, así que la IA reintrodujo algo que ella misma había señalado.
  - `SpikeRule` recibe `umbral` y no lo usa, lo que es dudoso frente a LSP.
  - Con la regla de pico, el mensaje dice `en 39.0% supera el límite de 20.0%` cuando en realidad son **39 puntos** de
    subida, no un porcentaje.
- **Decisión:** hacer obligatorio el parámetro `evaluador` [entrada 10]; ajustar el mensaje de la regla de pico. Sobre
  LSP: [lo justifico así: ___ / lo corrijo así: ___].

## Entrada 06 — Fase 5 (Factory Method y JSON)

- **Cómo lo revisé:** ejecuté `main.py` y confirmé que la sección 3, ahora armada desde el JSON, da la misma salida
  que antes. Cambié un canal a `"tipo": "sms"` y apareció el error con los tipos disponibles. Busqué `elif` en
  `domain/`, `application/` y `adapters/`: solo aparece en comentarios.
- **Qué acepté y por qué:** el registro `tipo → fábrica`, porque elimina el `if/elif` y agregar un tipo es una línea.
  También que el cargador no importe `application/`, porque si lo hiciera rompería la regla hexagonal.
- **Qué está mal o qué me genera duda:**
  - **¿Es Factory Method?** Según el GoF, el Creator tiene una operación propia que usa el método fábrica. Aquí
    `Factory` solo tiene `create()`, así que se parece más a una "Simple Factory con registro".
  - **Las pruebas comparten el Singleton:** `test_carga_el_json...` cambia el intervalo y los umbrales globales, y
    `test_a4` agrega 200 métricas. [Probé ejecutar los archivos de prueba en otro orden y ___.]
  - `JsonConfigLoader` construye objetos **y** modifica la configuración global: son dos responsabilidades.
- **Decisión:** [agregar al Creator una operación que valide los parámetros y llame `create()` / justificarlo en la
  defensa así: ___]. Aislar el Singleton en las pruebas con un *fixture* que lo reinicie.

## Entrada 07 — Fase 6 (UML y documentación)

- **Cómo lo revisé:** pegué cada `.mmd` en https://mermaid.live [resultado: ___]. Comparé los nombres de clases y
  métodos de `clases_nucleo.mmd` con el código, y leí `arquitectura.md` buscando afirmaciones que el código no cumpla.
- **Qué acepté y por qué:** dividir el diagrama de clases en dos, porque uno solo con más de 30 clases no se lee. El
  diagrama de secuencia sigue exactamente `ServiceMonitor.check()`.
- **Qué está mal o qué me genera duda:**
  - La IA no pudo validar la sintaxis de los diagramas; lo dejó dicho en la bitácora.
  - `Microservice o-- ServiceState` está dibujado como agregación, pero el estado lo crea y lo reemplaza el propio
    servicio, así que debería ser composición (`*--`).
  - La justificación de por qué no usé arquitectura por eventos la escribió la IA; tengo que poder explicarla con mis
    palabras.
- **Decisión:** [corregí ___ en el diagrama]; cambio la relación a composición.

## Entrada 08 — Fase 7 (guía de sustentación)

- **Cómo lo revisé:** ensayé las demos A a D. [La demo C funcionó / tuve que ___.] Comparé las respuestas de la guía con
  el código.
- **Qué acepté y por qué:** el guion por criterios de la rúbrica y la demo de romper la arquitectura en vivo.
- **Qué está mal o qué me genera duda:**
  - Algunas respuestas dependen de correcciones que todavía no había hecho (por ejemplo, lo de Factory Method).
  - El guion supone 10 minutos; [no sé / confirmé con el profesor] cuánto dura la defensa.
  - La guía tiene las respuestas a las preguntas; no sé si conviene que esté en el repositorio entregado.
- **Decisión:** actualizar la guía después de mis correcciones y [sacarla / dejarla] del repositorio.
