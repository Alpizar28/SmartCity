# Estado del Sprint 1

> **Actualización para revisión, 20/10/2026:** esta rama implementa el [contrato común `madrid-draft-v1`](CONTRATO_UNIFICADO.md) y la [ampliación real anual](AMPLIACION_REAL_SPRINT1.md), con 1.076.813 observaciones aceptadas de aire. Las cargas locales verificadas incluyen 1 organización, 5.133 usuarios y 5.133 sensores administrativos sintéticos, autorizados y documentados en [EVIDENCIA_AUTORIZACION_DATOS_SINTETICOS.md](EVIDENCIA_AUTORIZACION_DATOS_SINTETICOS.md). Las lecturas permanecen reales y no se vinculan a sensores demo. La segunda fuente aceptada sigue pendiente de revisión/evidencia; Spark no se ejecutó.

**Contrato vigente de esta rama:** [`madrid-draft-v1`](CONTRATO_UNIFICADO.md).

**Contrato histórico:** [`madrid-draft-v1-frozen`](../../CONTRATO_PROVISIONAL_DATASET.md), conservado para trazabilidad; no es la interfaz de la carga anual.

## Se puede desarrollar ya

### Recuperación histórica y desarrollo nuevo son frentes separados

La reproducción histórica sigue **pendiente**: 83/85 pruebas pasan; dos controles rechazan los hashes binarios de los SQLite regenerados y faltan 13 respuestas históricas. La correspondencia con fuentes verificadas no acredita identidad con las bases históricas. Véanse [recuperación](RECUPERACION_INSUMOS_HISTORICOS.md) y [auditoría lógica](AUDITORIA_LOGICA_SQLITE.md). No se declara PASS ni se modifica esa suite.

Esto **no invalida la interfaz provisional `madrid-draft-v1-frozen` ni impide desarrollar código nuevo** sobre sus campos congelados. Tampoco acredita cumplimiento académico, estabilidad de los campos abiertos ni autorización de carga. El desarrollo nuevo tendrá pruebas propias, separadas de la reproducción histórica; su PASS no sustituirá los controles pendientes.

La consolidación documental se integra en `main` por autorización explícita del usuario, **sin declarar reproducción histórica completa ni validación global PASS**. La rama local `fix/repo-consolidation` se elimina únicamente después de confirmar integración y publicación; la recuperación pendiente queda documentada en `main`. La continuación se mantiene en `feat/sprint1-local-core`. El [plan de inicio](PLAN_IMPLEMENTACION_SPRINT1.md) delimita archivos, consultas y bloqueos.

- Adaptadores, DTOs, validadores y consultas locales contra los campos congelados: fuente/versión, estación, canal, variable, valor, procedencia, calidad, reloj original y payload de tráfico.
- Catálogos y pruebas de integridad que respeten `NULL`, trazabilidad e IDs estables (`source_id`, `source_version`, `station_id`, `channel_id`, `location_id`).
- Diseño de migraciones y colecciones en una rama de trabajo, sin colocarlas en `postgres/init/` o `mongodb/init/` ni aplicarlas a un servidor.
- Reproducción acotada de la investigación si se poseen los insumos locales autorizados.

## No se debe asumir

- Un canal, estación o variable no representa un sensor físico.
- Las entidades administrativas de entrega sí están pobladas con datos sintéticos deterministas: `sensor_id`, `organization_id`, `user_id`, `installation_date` y `administrative_status` no acreditan una identidad física observada. En canales y observaciones reales, `sensor_id` permanece `NULL`.
- Las unidades meteorológicas, los relojes de meteo/tráfico, CRS, geografía y vigencia histórica siguen abiertos.
- `measurement_id` y `_id` de meteo/tráfico no son IDs definitivos mientras cambie la interpretación del reloj.
- Los 832.668 candidatos no están cargados en las bases compartidas; Spark/Hadoop no se ejecutó.

## Estado PostgreSQL

Los estados se refieren a evidencia local de Fase 5 y al alcance del contrato vigente; **CUMPLE** no significa despliegue compartido ni aprobación docente.

| Consulta | Estado | Evidencia y límite |
|---|---|---|
| PG01 | PARCIAL | Alternativa por canal/tipo; no inventario físico. |
| PG02 | PARCIAL | Sitio/ubicación parcial; identidad física y vigencia abiertas. |
| PG03 | BLOQUEADA | No existe estado administrativo acreditado. |
| PG04 | BLOQUEADA | Falta relación dispositivo–organismo/responsable. |
| PG05 | PARCIAL | Ranking de canales/sitios, no de sensores físicos. |
| PG06 | BLOQUEADA | No existe fecha de instalación individual. |
| PG07 | PARCIAL | Falta inventario físico e independiente completo. |
| PG08 | PARCIAL | Zonas de tráfico parciales y geografía histórica abierta. |
| PG09 | CUMPLE | Vista ejecutada en prueba local desechable. |
| PG10 | CUMPLE | Función ejecutada en prueba local desechable, con alcance de canal. |

## Estado MongoDB

| Consulta | Estado | Evidencia y límite |
|---|---|---|
| MG01 | PARCIAL | Find local por canal lógico; sensor físico pendiente. |
| MG02 | PARCIAL | Rango BSON local; reloj de meteo/tráfico pendiente. |
| MG03 | PARCIAL | Extremos locales; unidad meteorológica no confirmada. |
| MG04 | BLOQUEADA | Sin regla, umbral, QA y severidad aprobados. |
| MG05 | BLOQUEADA | Sin emisión histórica acreditada ni replay autorizado. |
| MG06 | PARCIAL | Solo distritos de tráfico publicados; vigencia pendiente. |
| MG07 | PARCIAL | Variable/unidad conocida, no tipo de sensor físico. |
| MG08 | BLOQUEADA | Accidentes 2026 separados; requiere carga y prueba propias. |
| MG09 | CUMPLE | Aggregation Framework ejecutado en muestra local desechable. |
| MG10 | CUMPLE | Filtros múltiples ejecutados en muestra local desechable. |

## Bloqueos académicos y preguntas

Las preguntas oficiales para envío están en [`PREGUNTAS_PROFESOR.md`](../../PREGUNTAS_PROFESOR.md); el contexto está en [`preguntas_profesor.md`](preguntas_profesor.md). No hay respuestas docentes acreditadas.

- Aceptación de canal/sitio como alcance alternativo mientras `sensor_id` es `NULL`.
- Tratamiento académico de instalación y estado administrativo faltantes.
- Evidencia aceptable para organismo/responsable y cuentas de usuario consentidas.
- Reglas derivadas y emisión de alertas, si la rúbrica las exige.

## Responsables inmediatos

| Responsable | Dependencia / siguiente acción |
|---|---|
| José | Acreditar unidades de meteo, relojes meteo/tráfico, CRS y vigencia de inventarios; no cargar sin autorización. |
| Daniel | Convertir el diseño histórico en propuesta Sprint 1 revisable; mantener PG03/04/06 bloqueadas y preparar pruebas locales. |
| Kembly | Preparar propuesta de colección/índices y pruebas locales; no presentar MG04/05/08 como cumplidas. |
| Fernanda | Mantener preguntas, decisiones, evidencia y esta matriz; registrar literalmente cualquier respuesta docente. |

## Siguiente checkpoint

Antes de diseñar migraciones definitivas o autorizar una carga: revisar esta matriz, cerrar la evidencia técnica disponible, registrar las respuestas docentes y aprobar explícitamente el alcance del equipo. Cualquier carga, cambio de Coolify/Tailscale o conexión al entorno compartido queda fuera de este Sprint 1 documental.
