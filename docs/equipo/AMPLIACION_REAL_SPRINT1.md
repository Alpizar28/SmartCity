# Ampliación real y entrega técnica del Sprint 1

Estado: propuesta implementada en `feat/unified-data-contract`, pendiente de revisión del equipo. No autoriza cambios remotos. Fecha de trabajo: 14–15/10/2026; Sprint 1: 18/10/2026.

La segunda fuente tiene una [propuesta técnica detallada `madrid-draft-v2`](../decisiones/PROPUESTA_MADRID_DRAFT_V2.md), **sin implementar**. El dimensionamiento de solo lectura identifica 656.930 candidatas URB/M30 en el estrato auditado de enero; no se suman a los aceptados hasta aprobar y probar esa revisión.

## 1. Auditoría de partida

- Rama base: `2bcee5778a5ce16d1da5fc14f5cd9fc96066607d`. Se conservaron todos los cambios locales de la unificación y el worktree independiente `SmartCity-sprint1`. No se reemplazó la rama `origin/feature/postgresql-sprint1` ni se modificaron consultas de Daniel.
- Las 91.959 aceptadas proceden exclusivamente del CSV oficial de aire, enero de 2025: 3.905 filas diarias × 24 = 93.720 slots, menos 1.761 flags no válidos. SHA-256 del archivo: `9122af41d3e73e71f5a0e0a22b99a0cefbd4c7f8abe9e2fae344207482398471`.
- La prueba anterior cargó solo 5.000 observaciones. No acreditaba mínimos globales.
- El pipeline anterior fijaba enero de 2025 y la fecha `2025-01-...` en código. No admitía múltiples meses de forma configurable. Se conserva ese reproductor acotado y se añade un exportador multi-mes reutilizando contrato, IDs, catálogos, unidades y validadores.
- La cuarentena anterior contenía 748.893 registros: 1.761 aire, 69.408 meteorología y 677.724 tráfico. No contarlos como lecturas aceptadas.

## 2. Fuentes oficiales investigadas

### Aire: ampliación prioritaria

- [Catálogo horario oficial](https://datos.madrid.es/dataset/201200-0-calidad-aire-horario): datos desde 2001, actualización mensual, responsable Dirección General de Sostenibilidad y Control Ambiental, licencia **CC BY 4.0**.
- [Índice de descargas](https://datos.madrid.es/dataset/201200-0-calidad-aire-horario/downloads): CSV/JSON/XML «Desde 2025» y ZIP anuales anteriores, incluido 2024. No hace falta descargar ZIP históricos para alcanzar el volumen requerido.
- [CSV oficial desde 2025](https://datos.madrid.es/dataset/201200-0-calidad-aire-horario/resource/201200-1-calidad-aire-horario-csv/download/201200-1-calidad-aire-horario-csv.csv).
- [Intérprete oficial](https://datos.madrid.es/dataset/201200-0-calidad-aire-horario/resource/201200-17-calidad-aire-horario/download/201200-17-calidad-aire-horario.pdf).

El snapshot **ya disponible** tiene 20.166.384 bytes y contiene enero–diciembre de 2025 y enero–agosto de 2026. Se utiliza únicamente 2025 completo. No se descargó otra copia de las mediciones: incorporar meses significa procesar filas ya auditadas, no repetir enero.

La ficha dice «Desde 2025»; la cobertura real del snapshot se verifica leyendo ANO/MES, no confiando solo en etiquetas del manifiesto antiguo. Se comprueba exactamente el conjunto de columnas en cada chunk: provincia, municipio, estación, magnitud, punto de muestreo, fecha y H01/V01–H24/V24. Las unidades y códigos siguen el mismo intérprete oficial usado en enero.

**Evidencia temporal específica:** intérprete de aire, apartado de observaciones, texto extraído líneas 304–311: hora local de Madrid UTC+1/UTC+2; explicación del cambio de hora y de H24 como media 23:00–24:00. La política contractual conservadora pone en cuarentena la hora inexistente y la ambigua sin asignar fold. No reconstruye la hora omitida ni altera valores.

### Meteorología: documentación localizada, reloj pendiente

- [Catálogo oficial](https://datos.madrid.es/dataset/300352-0-meteorologicos-horarios), CC BY 4.0, datos desde enero de 2019, publicación mensual, formatos horarios anuales desde 2025.
- [Intérprete oficial meteorológico](https://datos.madrid.es/dataset/300352-0-meteorologicos-horarios/resource/300352-122-meteorologicos-horarios/download/300352-122-meteorologicos-horarios.pdf).

El intérprete sí documenta H01/H02, la composición del punto de muestreo, estaciones y flag V. Anexo II: viento 81 m/s, dirección 82 sin unidad indicada (`-`), temperatura 83 ºC, humedad 86 %, presión 87 **mb**, radiación 88 W/m² y precipitación 89 **l/m²**. No se sustituyen silenciosamente por las antiguas unidades candidatas ni se acredita dirección en grados a partir de un guion.

**Bloqueo:** el documento no explicita zona horaria ni DST, ni acredita para todas las variables la misma función temporal que el `hour_end` de aire. No se deduce por pertenecer a la misma red. Se conservan los 69.408 slots auditados de enero en cuarentena. Hará falta evidencia adicional del publicador y una revisión contractual antes de habilitarlos.

### Tráfico: evidencia nueva y discrepancia incompatible

- [Catálogo histórico oficial](https://datos.madrid.es/dataset/208627-0-transporte-ptomedida-historico), CC BY 4.0, ZIP mensuales desde julio de 2013.
- [Intérprete oficial de históricos](https://datos.madrid.es/dataset/208627-0-transporte-ptomedida-historico/resource/208627-81-transporte-ptomedida-historico/download/208627-81-transporte-ptomedida-historico.pdf).

Página 4: integración en periodos de **15 minutos**; `fecha` es «Fecha y hora oficiales de Madrid»; intensidad veh/h; ocupación %; carga índice 0–100; velocidad km/h aplicable a M30; negativos indican ausencia; flag N sin errores/sustituciones. Página 5: **`periodo_integracion` es número de muestras recibidas y consideradas**, no una duración en minutos. La descripción del formato de fecha del documento difiere del ISO observado en el ZIP; el parser debe verificar el formato real.

La interpretación previa `interval_minutes = periodo_integracion` es incorrecta. **No se ha habilitado tráfico ni cambiado silenciosamente el significado**. Permanecen 677.724 filas seleccionadas en cuarentena. Se propone para revisión `madrid-draft-v2`: `interval_minutes=15`, nuevo `integration_sample_count` para el campo original, `timestamp_role=publisher_label` sin inventar inicio/fin, zona oficial Madrid con rechazo de DST ambiguo/inexistente. También requiere revisión de clases observadas como C30 y reglas de aplicabilidad. Antes de implementarla se solicita autorización por ser incompatible con el contrato actual; no basta renombrar `timestamp_status`.

La investigación encontró semántica de reloj más fuerte para tráfico que la disponible inicialmente; su permanencia en cuarentena se debe ahora también a la discrepancia contractual y a la revisión pendiente. No se afirma que la documentación carezca de toda evidencia temporal.

### Incidencias encontradas y resueltas sin alterar mediciones

- El ETL anterior seleccionaba solo enero aunque el CSV era anual: resuelto con exportador configurable separado, sin sobrescribir esa generación.
- El conteo provisional de duplicados de la primera unificación podía volverse negativo al restar inválidos: la generación unificada vigente usa registros identificados menos claves únicas; la ampliación usa unicidad explícita y reconciliación `seleccionados = aceptados + cuarentena + duplicados`.
- La descarga documental con `urllib` falló por el almacén local de certificados. Se utiliza `requests` con validación TLS activa, no `verify=False`.
- `pdftotext` heredaba bibliotecas incompatibles de Quartus mediante `LD_LIBRARY_PATH`. Solo para ese subproceso se elimina esa variable; no se modifica el entorno del usuario ni la instalación del sistema.
- El validador histórico comparaba código migrado con hashes antiguos y el E-R no reflejaba nuevas FK de fuente. Se verifica el código histórico desde el commit original registrado y se actualizó el diagrama del contrato actual, sin reescribir resultados históricos.
- El `git diff --check` del wrapper veía CSV temporales generados por la validación: se restauran primero las salidas históricas respaldadas y después se comprueba el diff real.

### Procedencia documental

`research/datasets/results/expanded-2025/research_sources.json` registra URLs, fecha real de recuperación, estado HTTP, tamaño, SHA-256 y ruta privada de siete documentos/páginas. Los PDF y HTML completos quedan en `raw/sprint1-research/` (ignorado). Se descargaron solo documentos necesarios; no mediciones adicionales.

## 3. Dataset ampliado

El año completo produce **1.076.813 observaciones aceptadas** de `MAD-AIR`, seleccionadas entre 1.103.232 slots. Cero mediciones sintéticas, duplicados o conflictos. 26.419 rechazos: 26.167 por flag del publicador, 126 por hora inexistente y 126 por hora ambigua.

| Mes original | Aceptadas |
|---|---:|
| 2025-01 | 91.959 |
| 2025-02 | 82.748 |
| 2025-03 | 91.145 |
| 2025-04 | 86.722 |
| 2025-05 | 91.736 |
| 2025-06 | 87.741 |
| 2025-07 | 91.700 |
| 2025-08 | 92.297 |
| 2025-09 | 88.229 |
| 2025-10 | 91.479 |
| 2025-11 | 88.778 |
| 2025-12 | 92.279 |

Son **984.854 observaciones adicionales respecto de enero**, no 1.076.813 más enero. El conjunto anual reemplaza el alcance de enero para conteos, no se suma a él. La cuarentena combinada sin repetir enero de aire es 773.551: 26.419 aire anual + 69.408 meteo enero + 677.724 tráfico enero. Las otras fuentes no se amplían ni cargan como aceptadas en esta revisión.

La generación anual es `expanded-2025`, bajo el mismo contrato semántico `madrid-draft-v1` y transformación `madrid-normalize-v2`: cambia el alcance temporal configurable, no la interpretación de variables, IDs o valores. Preserva fuente y snapshot, referencia física, hash de payload, catálogos y DTO. Las filas válidas de enero mantienen exactamente la identidad de la generación unificada anterior.

## 4. Reproducción

```bash
.venv/bin/python research/datasets/scripts/unified_research.py
.venv/bin/python research/datasets/scripts/unified_expand.py --dry-run
.venv/bin/python research/datasets/scripts/unified_expand.py
.venv/bin/python research/datasets/scripts/unified_expand.py
.venv/bin/python -m pytest research/datasets/tests -q
.venv/bin/python research/datasets/scripts/unified_full_load.py --engine postgresql
.venv/bin/python research/datasets/scripts/unified_full_load.py --engine mongodb
.venv/bin/python research/datasets/scripts/unified_full_verify.py
.venv/bin/python research/datasets/scripts/unified_audit.py
```

Para otro alcance: `--generation expanded-2025-first-half --year 2025 --months 1 2 3 4 5 6`. Se conserva JSON canónico, serialización e IDs del contrato. El ETL trabaja por chunks, escribe JSONL incremental y usa SQLite con unicidad tanto por ID como por clave canal/UTC/rol. Solo se publica `preparation.json` después de cerrar archivos, reconciliar conteos y calcular hashes. Un conflicto bloquea el lote. Un proceso interrumpido reconstruye **únicamente sus derivados sin sellar**, con fingerprint idéntico; no reescribe una generación terminada.

Los loaders exigen manifiesto terminado y verifican hashes antes de iniciar contenedores locales propios (`--network none`, sin puertos, máximo 2 GiB y 2 CPU por motor). No aceptan DSN ni credenciales remotas. Cargan **todo** `accepted.extjsonl`, comparan metadatos y valores, reimportan todo el lote y contrastan la huella ordenada de todos los IDs/hash con el ledger. Las pruebas de 5.000 siguen siendo muestras, no evidencia de la carga anual.

Tamaños medidos: originales referenciados 129.381.665 bytes (129,38 MB decimales); nuevos documentos oficiales 2.606.497 bytes; lecturas aceptadas JSONL 1.567.851.765 bytes (**1.567,85 MB / 1,568 GB**); derivados anuales completos 2.174.903.844 bytes (**2,175 GB**), incluido ledger SQLite, catálogos y muestra. No sumar derivados como más observaciones. `unified_audit.py` verifica que los 91.959 IDs y payloads de enero se conservan exactamente dentro del año.

Un clon limpio necesita los snapshots privados y metadatos de inventario usados por `sources()`/`metadata()`. No están en Git. Deben obtenerse por transferencia autorizada y verificarse contra el manifiesto; las URLs oficiales son mutables y una descarga actual podría no tener el mismo hash. Si difiere, registrar otro snapshot/generación, nunca reemplazar el original esperado ni afirmar reproducción binaria exacta. El antiguo `download.py` registra adquisiciones nuevas, pero no debe ejecutarse sobre manifiestos históricos para aparentar igualdad.

Las pruebas nuevas cubren límites de mes/H24, DST, duplicados, conflictos, fingerprint de reinicio, interrupción, archivos alterados y dry-run sin escritura. Los resultados completos de motores se registran en `postgresql_full.json` y `mongodb_full.json` junto al manifiesto anual.

## 5. Entrega a Daniel

DDL: `research/datasets/scripts/phase5_postgresql.sql`; esquema `smartcity`, relaciones estación → ubicación y observación → canal, FK compuestas fuente/estación/tipo/versión, sensor opcional de la misma estación. Catálogos: `private_results/expanded-2025/catalogs.json`; muestra: `sample.extjson`; lote: `accepted.extjsonl`.

Revisada su rama `origin/feature/postgresql-sprint1`, archivos `sprint1/postgres/queries.sql`, `schema_proposal.sql` y pruebas de `tests/sprint1/`. No se alteraron. Adaptaciones concretas:

1. Cambiar prefijo `sprint1` a `smartcity`; usar el DDL común, no crear tablas paralelas.
2. Cambiar conteos/trazas `observation_id` por `measurement_id`.
3. PG02, PG05 y PG08: unir `stations.location_id = locations.location_id`, no `locations.station_id`.
4. PG09: vista común usa `readings`, `first_observed_at`, `last_observed_at` (UTC); su propuesta usa `reading_count`, `first_original_time`, `last_original_time`. Elegir una interfaz aprobada o adaptar explícitamente su SELECT; no recrear la vista con otro significado.
5. PG10: `channels_at_station()` cuenta **canales**, no sensores. Su `count_sensors_at_station()` tiene otra función y puede añadirse como tal sin confundirlas.
6. No recrear índices que ya cubre una FK/UNIQUE o índice existente; medir con `EXPLAIN ANALYZE`. `locations_station_id_index` no aplica al modelo nuevo.
7. PG03: NULL/desconocido separado; PG04 y PG06 no atribuyen organismo ni instalación falsos. PG07 requiere ventana explícita anual o mensual y etiqueta «sin lecturas en la ventana», no «averiado».

Puede empezar ya consultas analíticas y rendimiento sobre más de un millón de lecturas. El inventario de sensores reales sigue vacío; las consultas físicas no quedan acreditadas por devolver cero filas.

## 6. Entrega a Kembly

- `readings` estándar; importar el JSONL Extended JSON **con soporte EJSON**, para convertir `observed_at.$date` en BSON Date. No cargarlo como objeto o string.
- `_id = measurement_id` suministrado; no recalcular hashes en Mongo ni generar IDs nuevos.
- Catálogos compartidos y manifiesto SHA-256 del lote; validar estación/canal/fuente/tipo/unidad/versión antes de importar.
- Unicidad `_id` y `(channel_id,observed_at,timestamp_role)`; índices por fuente/tipo/tiempo y zona/tipo/tiempo. El índice único ya cubre canal/tiempo: evitar índice redundante. Sin TTL ni geoespacial con CRS pendiente.
- Reimportación: mismo ID y contenido no duplica; discrepancia registra conflicto y aborta sin sobrescribir. Comparar contenido además del hash para detectar payload alterado conservando el hash antiguo. El harness local usa un único escritor; no promete transacción distribuida ni atomicidad multi-documento de producción.
- Se proporciona un lote real anual suficiente para medir rendimiento; mantener sus scripts y lógica de aplicación separados de `unified_full_mongo.js`, que es **solo evidencia de prueba local**.
- `measurements` de tráfico no se divide ni fabrica; esa fuente no está habilitada todavía. Alertas/eventos/demos siguen separados.

No se encontró una implementación propia de Kembly disponible en la rama inspeccionada; no se afirma haber verificado compatibilidad con código que no está presente.

## 7. Entrega a Fernanda y decisiones

Incorporar contrato común, `unified_fields.csv`, nuevo alcance anual, política de cuarentena, manifiestos de ejecución y diferencias de vistas/funciones. Las cifras 832.668 históricas y 5.000 de muestra no deben figurar como volumen aceptado anual ni cargado remotamente. Registrar CC BY 4.0 y atribución al Ayuntamiento de Madrid.

Actualizar diseños y diccionario oficiales con advertencias de campos aún no acreditados. La evidencia meteorológica y de tráfico debe incorporarse como propuesta de revisión; no presentar unidades candidatas como confirmadas ni `periodo_integracion` como minutos. Mantener resultados antiguos y explicar su supersesión, sin reescribir sus conteos.

Requieren aprobación: revisión del contrato por el equipo, migración futura de tráfico/unidades meteo, alcance académico de sensores ficticios y aceptación de integración sin sincronización demostrada. Las 14 entidades administrativas de demo siguen separadas; no se añadieron ni asignaron a mediciones reales en esta ampliación.

## 8. Cumplimiento y límites

- PostgreSQL ≥100.000: el dataset es suficiente; solo se declara carga cumplida cuando `postgresql_full.json` confirma ejecución completa y reconciliación.
- MongoDB ≥500.000: el dataset es suficiente; solo se declara carga cumplida con `mongodb_full.json` completo.
- Spark ≥1.000.000 procesados: **pendiente**. Hay 1.076.813 registros aceptados disponibles, pero no se ejecutó ni implementó Spark/Hadoop.
- Al menos dos fuentes: **parcial/bloqueado** para observaciones aceptadas: solo `MAD-AIR`. Los inventarios auxiliares enriquecen catálogos, pero no se cuentan como segunda fuente de mediciones sin acuerdo sobre el criterio. La solución verificable es revisar y habilitar tráfico con el contrato nuevo tras autorización, o acreditar el reloj meteorológico.
- Servidor compartido, Coolify y Tailscale: no modificados. No hay migración destructiva, carga remota ni merge a `main`.

El bloqueo de la segunda fuente y la discrepancia contractual de tráfico se comunican antes de aplicar cambios incompatibles. La instrucción más reciente exige **commit local sin push, merge ni cambios al servidor compartido sin autorización**. No se publica la rama ni se crea PR remoto. La propuesta v2 queda para aprobación antes de programar la migración.
