# Plan del Proyecto Final 1 (a partir del ejercicio 2)

## Estilo: Hexagonal (Puertos y Adaptadores)

| Capa | Carpeta | Puede importar |
|---|---|---|
| Dominio | `domain/` | nada del proyecto |
| Puertos | `ports/` | domain |
| Aplicación | `application/` | domain, ports |
| Adaptadores | `adapters/` | domain, ports |
| Composition root | `main.py` | todo |

La regla se verifica automáticamente en `tests/test_arquitectura.py`.

## Auditoría inicial del código del ejercicio 2

| # | Problema | Principio | Corrección | Estado |
|---|---|---|---|---|
| A1 | `MonitoringConfig()` llamado por dentro de ServiceMonitor/Facade | DIP | Puerto `ConfigProvider` inyectado | ✅ Fase 1 |
| A2 | `get_cpu_usage()` abstracto obliga a todo proveedor a tener CPU | ISP / LSP | Solo `get_metrics()` | ✅ Fase 1 |
| A3 | `Microservice.evaluate()` evalúa **y** cambia estado | SRP | Strategy + State | ✅ Fases 3–4 |
| A4 | Escrituras de umbrales sin lock | Corrección | Lock en lectura/escritura | ✅ Fase 1 |
| A5 | Un canal que falla rompe el ciclo | Robustez | try/except por canal | ✅ Fase 1 |
| A6 | `detach()` lanza ValueError | Robustez | Validar | ✅ Fase 1 |
| A7 | `main.py` arma todo a mano | OCP | Factory + JSON | ✅ Fase 5 |

## Patrones

| Patrón | Problema que resuelve | Estado |
|---|---|---|
| Adapter | APIs externas con formatos distintos | ✅ |
| Facade | Punto único de entrada | ✅ |
| Observer | Canales de alerta desacoplados | ✅ |
| Singleton | Configuración única compartida (inyectada, no global) | ✅ |
| State | Estados Saludable/Degradado/Crítico/Mantenimiento, histéresis anti-flapping | ✅ |
| Strategy | Reglas de evaluación: umbral, promedio móvil, pico | ✅ |
| Factory Method | Construir canales/proveedores/reglas desde JSON sin if/elif | ✅ |
| Decorator (opcional) | Filtro por severidad / reintentos en canales | Opcional |

## Fases

| Fase | Contenido | Estado |
|---|---|---|
| 0 | Copiar ejercicio 2, .gitignore, bitácora | ✅ |
| 1 | Correcciones A1, A2, A4, A5, A6 | ✅ |
| 2 | Capas hexagonales + test de arquitectura | ✅ |
| 3 | State | ✅ |
| 4 | Strategy | ✅ |
| 5 | Factory Method + `config/servicios.json` | ✅ |
| 6 | Tests, UML (componentes, clases, secuencia, estados), README, `docs/arquitectura.md` | ✅ (diagramas revisados en GitHub) |
| 7 | Preparación de la defensa (`docs/defensa.md`) | ✅ |
