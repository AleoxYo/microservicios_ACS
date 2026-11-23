# Guía de sustentación

Preparación para la defensa oral del Proyecto Final 1. Está organizada según la rúbrica:
estilo arquitectónico (30), SOLID (25), patrones GoF (20), uso crítico de la IA (20), UML y defensa (15).

> Esta guía es para estudiar. Decide si la dejas en el repositorio que entregas o la sacas antes.

---

## 1. Guion de presentación (≈ 10 minutos)

| Min | Qué decir | Qué mostrar |
|---|---|---|
| 0–1 | **Problema:** una fintech monitorea microservicios con APIs de formatos distintos, umbrales que cambian en caliente, alertas por varios canales, sin alertas repetidas y configurable sin tocar código. | README |
| 1–3 | **Estilo Hexagonal:** núcleo sin tecnología, puertos que define el núcleo, adaptadores afuera. Regla: las dependencias apuntan al dominio. Por qué no Capas ni Eventos (2 frases). | `docs/arquitectura.md` §2, diagrama de componentes |
| 3–4 | **La regla se verifica sola:** `test_arquitectura.py`. | Demo C (abajo) |
| 4–7 | **Patrones, siguiendo un ciclo:** Facade → Adapter → Singleton (vía puerto) → Strategy → State → Observer. Factory Method arma todo desde el JSON. Para cada uno: *qué problema resuelve*. | Diagrama de secuencia + `python main.py` |
| 7–8 | **SOLID:** un ejemplo por letra, con la auditoría A1–A7 como evidencia de "antes y después". | `docs/arquitectura.md` §5 |
| 8–10 | **Auditoría de la IA:** 2 o 3 errores que encontraste en lo que propuso la IA, cómo los corregiste y el `git diff`. | `docs/bitacora_ia.md` + commits |

**Frase de cierre sugerida:** "El núcleo no sabe de dónde vienen las métricas, a dónde van las alertas ni cómo se guarda
la configuración; por eso puedo cambiar cualquiera de esas tres cosas sin tocarlo, y un test lo garantiza."

---

## 2. Demos preparadas

Ensáyalas antes. Todas se hacen desde la carpeta `proyecto_final/`.

**A. Demo general:** `python main.py`

| Sección | Qué señalar |
|---|---|
| 1. Singleton | `configuracion_a is configuracion_b: True` |
| 2. Adapter | La respuesta cruda de cada API frente a `get_metrics()` normalizado |
| 3. Factory + Facade + Observer | "Cargados 3 canales y 2 servicios" desde el JSON; cada alerta llega a Email, Slack y Log |
| 4. Singleton en caliente | Al subir el umbral a 95 % ya no hay alertas |
| 5. State | 97 → 98 → 99 % = DEGRADADO, DEGRADADO, CRITICO; un 60 % aislado **no** lo saca de CRITICO (histéresis); en mantenimiento, 0 alertas |
| 6. Strategy | La misma serie con 3 reglas: umbral 4 alertas, promedio 1, pico 2 |

**B. Pruebas:** `python -m pytest -v` → 44 pruebas. Nombra las `test_ocp_*` y las `test_lsp_*`.

**C. Romper la arquitectura en vivo (la más convincente):**
1. Agrega `from adapters.monitoring_config import MonitoringConfig` al inicio de `domain/alert.py`.
2. Ejecuta `python -m pytest tests/test_arquitectura.py` → falla con `domain\alert.py importa ['adapters']`.
3. Quita la línea y vuelve a ejecutar → pasa.

**D. Cambiar el comportamiento sin tocar código:** en `config/servicios.json`, cambia la regla de `cpu` de
`servicio-autenticacion` a `{ "tipo": "promedio", "ventana": 2 }` y ejecuta `main.py`. También puedes poner
`"tipo": "sms"` en un canal para mostrar el error claro con los tipos disponibles.

---

## 3. Preguntas probables y respuestas cortas

### 3.1 Estilo arquitectónico (30 pts)

**¿Qué es la arquitectura hexagonal?**
Separa un núcleo (dominio y casos de uso) de la tecnología externa. El núcleo define **puertos** (interfaces) y la
tecnología se conecta con **adaptadores** que los implementan. Así el núcleo no depende de nada externo.

**¿Qué diferencia hay entre un puerto y un adaptador? Dame un ejemplo de tu código.**
El puerto es el contrato que necesita el núcleo: `MetricsProvider.get_metrics()`. El adaptador es la implementación
concreta: `LegacyApiAdapter` traduce `{"cpu_usage_percent": 85}` a `{"cpu": 85.0}`.

**¿Puertos de entrada y de salida?**
De entrada (*driving*): `MonitoringFacade`, por donde operaciones usa el sistema. De salida (*driven*):
`MetricsProvider`, `AlertObserver` y `ConfigProvider`, que el núcleo usa para hablar con el exterior.

**¿En qué se diferencia de una arquitectura por capas?**
En capas, el negocio depende de la capa de datos o infraestructura que tiene debajo. En hexagonal la dependencia se
invierte: la infraestructura depende de interfaces que define el núcleo. Además, aquí hay **varias** tecnologías externas
al mismo nivel (APIs, canales, configuración), y eso encaja mejor con "puertos alrededor de un núcleo" que con una pila.

**Hiciste una exposición de arquitectura por eventos. ¿Por qué no la usaste?**
Las alertas son eventos, pero el sistema es un solo proceso con un ciclo síncrono. Un bus de eventos agregaría
infraestructura (broker, suscripciones asíncronas) sin resolver un problema real; el Observer ya desacopla a quien
detecta de quien notifica. Si el sistema creciera a varios procesos o necesitara reprocesar alertas, entonces sí
convendría.

**¿Cómo garantizas que el estilo no se degrade?**
Con `tests/test_arquitectura.py`, que lee los `import` de cada archivo con `ast` y falla si una capa importa una
prohibida (demo C).

**¿Por qué `main.py` puede importar todo?**
Es el *composition root*: el único lugar donde se crean las clases concretas y se inyectan. Si no existiera, alguna capa
del núcleo tendría que crear adaptadores y se rompería la regla.

**¿Por qué el Singleton está en `adapters/` y no en `domain/`?**
Guardar la configuración (en memoria, en un archivo o en una base de datos) es un detalle de infraestructura. El núcleo
solo necesita *leer* umbrales, y para eso usa el puerto `ConfigProvider`.

**¿Por qué `JsonConfigLoader` no registra los servicios directamente en la fachada?**
Porque está en `adapters/` y no puede importar `application/`. Devuelve una `SystemDefinition` y `main.py` hace el
cableado.

**Explica el flujo de datos de un ciclo.**
Fachada → `ServiceMonitor.check()` → `get_metrics()` (Adapter) → `get_thresholds()` (Singleton vía puerto) →
`MetricEvaluator` aplica la regla de cada métrica (Strategy) → `Microservice.record_cycle()` delega en su estado
(State) → `notify()` a cada canal (Observer). Ver el diagrama de secuencia.

### 3.2 SOLID (25 pts)

| Letra | Respuesta en una frase con tu código |
|---|---|
| S | `MetricEvaluator` solo evalúa y `Microservice` solo maneja estado; antes estaban juntos en `evaluate()` (A3). |
| O | Una regla, un estado o un canal nuevo es una clase nueva más una línea `register(...)`; `test_ocp_*` lo demuestra. |
| L | Cualquier `EvaluationRule`, `ServiceState`, `MetricsProvider` o `AlertObserver` se puede intercambiar; `test_lsp_*`. |
| I | Puertos de un método; se quitó `get_cpu_usage()` obligatorio, que forzaba CPU a todos los proveedores (A2). |
| D | `ServiceMonitor` recibe `ConfigProvider` por constructor en vez de llamar `MonitoringConfig()` (A1); por eso las pruebas usan `ConfigFija`. |

**La rúbrica habla de eliminar los `if/switch`. Todavía tienes `if` en el código, ¿por qué?**
Se eliminaron los `if` que preguntan por el **tipo** (qué estado, qué regla, qué canal), que son los que hay que
modificar cada vez que aparece un tipo nuevo. Los que quedan, como `if alertas` o `if metrica not in umbrales`, son
decisiones sobre **datos** dentro de una sola clase. Agregar un estado o una regla nueva no los toca.

**`SpikeRule` recibe el umbral y no lo usa. ¿No viola LSP?**
Prepara tu respuesta (o corrígelo antes de la defensa). Defensa posible: el contrato es "dado el historial y el umbral
configurado, di si hay violación y contra qué límite"; `SpikeRule` lo cumple y reporta su propio límite en `Violation`.
Crítica posible: el contrato debería dejar claro que el umbral es opcional, o la regla debería recibir su límite de otra
forma.

**¿Qué pasa si un canal de alerta lanza una excepción?**
`notify()` la captura por canal, la registra en el log y sigue con los demás (A5). `test_a5_...` lo prueba.

### 3.3 Patrones GoF (20 pts)

Para **cada** patrón, ten lista la respuesta a tres preguntas: *qué problema resuelve aquí*, *quiénes son los
participantes* y *qué pasaría sin él*.

| Patrón | Sin él… |
|---|---|
| Adapter | `ServiceMonitor` tendría que conocer el formato de cada API (`cpu_usage_percent`, `cpuLoad`) |
| Facade | `main.py` tendría que crear monitores, suscribir canales y coordinar ciclos a mano |
| Observer | El monitor conocería los canales y habría que modificarlo para agregar SMS o Teams |
| Singleton | Podría haber varias configuraciones y un cambio de umbral no lo verían todos |
| State | Un `if/elif` sobre el estado actual, con contadores y casos de mantenimiento mezclados |
| Strategy | Para agregar una regla de evaluación habría que modificar el evaluador |
| Factory Method | Un `if tipo == "email" … elif …` que crece con cada tipo nuevo |

**State y Strategy tienen la misma estructura. ¿Cuál es la diferencia?**
La intención. En **State**, el propio objeto cambia de estado internamente (`on_cycle` devuelve el siguiente) y el
cliente no lo elige. En **Strategy**, el cliente elige la regla desde afuera (al registrar el servicio o en el JSON) y
la regla no cambia sola.

**El Singleton se considera un antipatrón. ¿Por qué lo usaste?**
El problema del Singleton es el **acceso global** (dependencia oculta y difícil de probar). Aquí se mantiene la instancia
única, pero el núcleo nunca llama `MonitoringConfig()`: la recibe inyectada por el puerto `ConfigProvider` (A1). En las
pruebas se reemplaza por `ConfigFija`.

**¿Es Factory Method, Simple Factory o Abstract Factory?**
Prepárala bien. En el GoF clásico, el Creator tiene una operación que *usa* el método fábrica y las subclases deciden qué
se crea. En tu código, `Factory[T]` declara `create()`, cada fábrica concreta lo sobrescribe y un registro elige cuál
usar. Es la estructura Creator/ConcreteCreator, pero sin una operación propia en el Creator. Por eso alguien puede
llamarlo "Simple Factory con registro". **No** es Abstract Factory, porque no se crean familias de productos
relacionados. Si quieres que sea un Factory Method sin discusión, agrega al Creator una operación (por ejemplo,
validar los parámetros y después llamar `create()`).

**¿Tu Adapter es de clase o de objeto?**
De objeto: `LegacyApiAdapter` *contiene* una `LegacyMonitoringApi` (composición), no hereda de ella.

**¿Observer es lo mismo que publicar/suscribir?**
No. En Observer, el Subject (`ServiceMonitor`) conoce la lista de observadores y los llama directamente. En
publicar/suscribir hay un intermediario (bus o broker) y ninguno conoce al otro.

**¿Facade no es un "God object"?**
No: no implementa lógica, solo delega (crea monitores, suscribe canales, recorre ciclos). La lógica está en
`ServiceMonitor`, `MetricEvaluator` y los estados.

### 3.4 Uso crítico de la IA (20 pts)

**Esta parte solo la puedes responder tú.** El profesor va a preguntar "¿qué hizo mal la IA y cómo lo corregiste?". Necesitas
2 o 3 ejemplos **corregidos por ti**, con commit, antes de la defensa. Candidatos reales detectados durante el desarrollo
(los detalles están en cada entrada de la bitácora):

| Problema en lo que propuso la IA | Entrada | Dificultad de corregir |
|---|---|---|
| La prueba de A4 no demuestra una condición de carrera (pasaría sin el lock) | 03 | Media |
| DEGRADADO emite una advertencia en **cada** ciclo: el *flapping* no se resuelve del todo | 04 | Baja |
| `emit()` decide con `if self.severidad is None` en vez de polimorfismo | 04 | Baja |
| `SpikeRule` ignora el umbral; el mensaje muestra "35.0%" cuando son puntos | 05 | Baja |
| `ServiceMonitor` crea un `MetricEvaluator` por defecto (dependencia oculta, igual que A1) | 05 | Baja |
| `Factory` no tiene operación propia: es discutible que sea Factory Method | 06 | Media |
| Las pruebas comparten el Singleton (dependen del orden) | 06 | Media |
| `FactoryRegistry.create()` convierte cualquier `KeyError` en "Falta el parámetro" | 06 | Baja |

**Cómo contarlo:** "La IA propuso X. Lo revisé y vi que violaba Y (por ejemplo, DIP o la regla hexagonal) porque Z. Lo
cambié así [diff]. Lo verifiqué con [prueba]."

**¿Cuánto del código hizo la IA?**
Responde con honestidad: la IA generó la mayor parte siguiendo un plan por fases; tu trabajo fue elegir el estilo,
revisar cada propuesta, detectar los problemas y corregirlos. La bitácora lo documenta.

### 3.5 UML (15 pts)

**¿Composición o agregación entre `ServiceMonitor` y `Microservice`?**
Composición (`*--`): el monitor crea su `Microservice` y su `MetricEvaluator`, y viven con él. Los canales son
agregación (`o--`): existen por fuera y se comparten entre monitores.

**¿Qué significan los estereotipos `<<Context State>>`, `<<Adaptee>>`, etc.?**
Indican el rol de la clase dentro de su patrón GoF, para que en el diagrama se lea qué patrón aplica cada clase.

**¿El diagrama refleja el código?**
Compruébalo tú antes de la defensa: nombres de clases, métodos y relaciones de `docs/uml/*.mmd` contra el código.

---

## 4. Conceptos técnicos que pueden salir

- **`Lock` y el GIL:** el GIL de CPython hace atómicas algunas operaciones simples (asignar en un dict), pero no las
  secuencias de operaciones (leer, modificar, escribir). El lock protege la consistencia y no depende de un detalle de
  CPython.
- **`deque(maxlen=10)`:** cola que descarta la lectura más vieja al llenarse; el historial no crece sin límite.
- **`@dataclass(frozen=True)` en `Alert`:** objeto de valor inmutable; para cambiar la severidad se crea uno nuevo con
  `dataclasses.replace`.
- **`ABC` y `@abstractmethod`:** Python no deja instanciar una clase que no implementó todos los métodos abstractos; así
  se garantiza el contrato del puerto.
- **Inyección de dependencias:** las dependencias se pasan por constructor en lugar de crearse adentro.

---

## 5. Checklist antes de entregar

- [ ] Repositorio en GitHub con `proyecto_final/` como raíz (o repositorio propio), sin `__pycache__`.
- [ ] `python -m pytest` pasa y `python main.py` corre sin errores en un clon limpio.
- [ ] Los 5 diagramas se ven bien en GitHub (abrir `docs/arquitectura.md`).
- [ ] Bitácora: la "Auditoría del estudiante" completa en **todas** las entradas.
- [ ] 2 o 3 correcciones propias con commit "versión IA" → commit "corrección", citadas en la bitácora.
- [ ] Consultado con el profesor si se acepta partir del ejercicio 2.
- [ ] Ensayadas las demos A–D y el guion de 10 minutos.
