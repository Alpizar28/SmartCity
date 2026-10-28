# Entrega técnica PostgreSQL para Fernanda

## Resultado y versiones que se pueden citar

Base `main`: `b77e5497fa28f8c2b483b06e2e593d96b7bd0a5d`, sincronizada por
fast-forward desde origin/main; árbol inicial limpio. Cambios de cierre locales,
sin staging, commit, push ni servidor compartido. Las fechas de los reportes son
UTC (28 de octubre); no son una fecha de aprobación docente.

**Auditoría formal terminada, con excepciones; PG07 probada funcionalmente pero
sin acreditación física; evidencia técnica preparada. No declarar 10/10 requisitos
académicos físicos ni doce relaciones estrictamente en 3FN.**

| Clave usada abajo | Artefacto | Qué prueba |
|---|---|---|
| H | `research/datasets/results/expanded-v2-2025-01/execution-0652c6cd8bbc.json` | PASS masivo PostgreSQL previo, 748.889 filas, replay, metadatos, cantidades y primeras 5 filas por consulta |
| A | [evidencias/cierre_auditoria_v2.json](evidencias/cierre_auditoria_v2.json) | Nueva lectura completa del paquete: hashes, IDs/payload/referencias/ledger y cálculo Python independiente de las diez consultas; coteja cantidad y muestra H |
| C | [evidencias/cierre_pg07_controlado.json](evidencias/cierre_pg07_controlado.json) | Nueva ejecución del SQL canónico exacto con fixtures sintéticas revertidas, diez consultas y casos ampliados PG07 |
| S | [evidencias/cierre_subconjunto_v2.json](evidencias/cierre_subconjunto_v2.json) | Nueva ejecución v2 con 2.907 lecturas auténticas seleccionadas y administración demo; todas las filas SQL cotejadas con Python, agregados, ventanas, catálogo/planes y limitaciones DDL |

H tiene SHA-256 `6800775f103b5dd50da838ff8a7e461cec113fb275a82ed6e6f73363d09a52b3`.
Se comprobaron sus hashes SQL/Python contra main, y el DDL actual contra la copia
del paquete. El informe histórico no incluía hash del DDL ni del paquete dentro
de su propio source_hashes: esa conexión se refuerza ahora con A, pero no se
presenta como un sellado criptográfico histórico inexistente. H compara todos
los metadatos y su huella de identidad coincide con el ledger verificado.

Los otros `execution-4ad733d734ab.json` (PostgreSQL) y
`execution-5153d59831f7.json` (MongoDB) son **FAIL**. No se reescribieron ni se usan
como PASS. No hay PASS masivo MongoDB v2 confirmado en main: el verificador de
ambos motores no puede declararse aprobado con esta entrega PostgreSQL.

## Paquete, origen y alcance

ZIP privado existente: `/home/dburger/Descargas/SmartCity_DATASET_COMPLETO_PRIVADO.zip`
(729.101.163 bytes); raíz v2 interna:
`research/datasets/private_results/expanded-v2-2025-01/`. Se leyó directamente;
no se extrajeron gigabytes ni se ejecutaron scripts incluidos. El TAR alternativo
en Descargas resultó ser `expanded-2025-with-hashes.tar.gz`, histórico v1; se
inspeccionó sin extraer y no se sumó a v2.

| Generación | Contrato | Observaciones aceptadas | Uso en este cierre |
|---|---|---:|---|
| expanded-2025 | madrid-draft-v1 | 1.076.813 aire, todo 2025 | Solo evidencia/benchmark histórico, no una nueva carga |
| expanded-v2-2025-01 | madrid-draft-v2 | 748.889: 91.959 MAD-AIR + 656.930 MAD-TRAFFIC | Prioridad; archivos completos auditados, H masivo y S subconjunto |

Preparación v2: 93.720 slots aire seleccionados, 1.761 rechazados por flag;
677.724 intervalos tráfico seleccionados, 20.794 rechazados (17.774 tipo de
elemento no documentado y 3.020 flag). Total rechazado 22.555. El tráfico usa
estrato `id % 20 == 0`, no todo Madrid. La fuente es Ayuntamiento de Madrid;
meteo está en catálogos (3 fuentes), pero **no** tiene lecturas aceptadas v2
(solo 2 fuentes observadas). Los 14.388 accidentes de 2026 son otro complemento,
no se agregan a observations ni a su enero de 2025.

A verifica SHA-256/tamaño de los seis derivados v2, preparación, siete originales,
diccionario de tráfico y catálogos/QA adicionales. Valores principales:

| Derivado v2 | Bytes | SHA-256 |
|---|---:|---|
| accepted.extjsonl | 1.472.550.998 | `842052ca68b331121cc843bb6dd8273465c6442b1d99955d46f461a8af06daae` |
| catalogs.json | 5.455.014 | `1c9b79d4386eb4dc79452f217ba7ff3c9f7ca7a389024283d69c70e8bce0874b` |
| administrative_seed.json | 7.405.490 | `550b349e3b26b73e2f82963c3abaeb327d39fe4b2eae92a2c6dfd30399d0bfa2` |
| identities.sqlite | 407.670.784 | `b50c1db33f21e4dcfde4142d675821ed49b67d4656cf1f4df1e3f2f2f2a11f81` |

Huella ordenada ID/payload compartida con H:
`9e8a6b6b7e1aa527693aa9c71ca8dc44123e2d4602f8b94f2ba2afa4b54c69a0`.
A comprueba 748.889 registros únicos, pertenencia individual al ledger de solo
lectura, claves naturales, relojes Madrid, contrato v2, reglas aire/tráfico y
referencias a canal/estación/tipo/unidad/zona/versión. **Cero duplicados detectados**.
Se copió únicamente el ledger a un temporal propio de 408 MB, eliminado al salir.

Catálogos v2: 5.133 estaciones/ubicaciones derivadas, 360 canales, 21 zonas,
12 tipos/categorías, 6 versiones y 3 fuentes. Administración:
5.133 sensores, 5.133 usuarios, 1 organización, todos `synthetic`,
`admin-demo-v2`, semilla `20261010`, reproducidos **exactamente** por A.
Una entidad demo por estación **no** implica que produjo las mediciones.
Todos los 360 channels.sensor_id y todos los sensores de las lecturas son NULL.
Geografía del inventario actual: vigencia histórica no acreditada.

## PG01–PG10: ficha común y matriz de resultados

Requisitos textuales tomados de `research/datasets/00_requirements.md`, sección
PostgreSQL (transcripción E p. 10); no se inventa otra pregunta.
**Implementación de cada fila:** `sprint1/postgres/queries.sql`, bloque con su ID.
Referencia exacta del archivo SHA-256:
`e0944eb54a777aa22714a9dbd23b23a112a6d34eb906622cdb37c3feb89eaed9`.
`read_queries()` extrae esos diez SELECT/CTE sin reescribirlos. Las líneas abajo
son referencias de main y el hash permite detectar desplazamientos/cambios.

Todas las cantidades de la siguiente tabla son de **H masivo v2**, no de v1 ni
de S. Cada fila se reproduce con el comando de auditoría A para comprobar el
resultado de H y con el comando S para ejecutar el SQL sobre su subconjunto.
C ejecuta sin datos privados; no es prueba física. Para cargar todo v2, ver guía.

| ID | Requisito textual / objetivo | SQL exacto | Tablas y JOIN | Operaciones principales | Filas H | Origen | Ejecuta / comprobación | Estado académico y limitación |
|---|---|---|---|---|---:|---|---|---|
| PG01 | Sensores por tipo. Contar dispositivos administrativos por categoría | bloque PG01, L6–15 | sensors LEFT JOIN sensor_categories | SELECT, COUNT, GROUP BY, ORDER BY | 12 | Mixto: sensores synthetic y categorías lógicas derivadas | H/C/S; A Counter por category_id y S cotejo completo | Demo autorizada; no inventario físico; categoría no es aparato |
| PG02 | Sensores por ubicación. Contar sensores por estación/ubicación disponible | PG02, L17–30 | stations INNER sensors LEFT locations | COUNT DISTINCT, GROUP BY, ORDER BY | 5.133 | Mixto: demo + catálogo observado/IDs derivados | H/C/S; A Counter de estaciones y stable_id de ubicación | Condicionado al demo y a vigencia geográfica |
| PG03 | Cantidad de sensores activos e inactivos. Separar estado administrativo y NULL | PG03, L32–38 | sensors; sin JOIN | COUNT(*), GROUP BY, NULLS LAST | 2 | Synthetic | H/C/S; A Counter de estados; C comprueba grupo NULL | Estados demo, no actividad observada ni diagnóstico físico |
| PG04 | Número de sensores por organismo responsable. Incluir organismos sin sensores | PG04, L40–49 | organizations LEFT sensors | COUNT(sensor_id), GROUP BY | 1 | Synthetic | H/C/S; A conteo por organismo; C organismo vacío=0 | Responsabilidad demo, no operador municipal acreditado |
| PG05 | Ubicaciones con mayor cantidad de sensores. Ordenar inventario | PG05, L51–63 | locations INNER stations INNER sensors | COUNT DISTINCT, HAVING >0, ORDER BY DESC | 5.133 | Mixto demo/catálogo | H/C/S; A agrupa/ordena ubicación; S todas las filas | Ranking de demo, no densidad física histórica |
| PG06 | Sensores instalados por año. Excluir fecha desconocida | PG06, L65–72 | sensors; sin JOIN | EXTRACT YEAR, WHERE IS NOT NULL, GROUP BY | 5 | Synthetic | H/C/S; A Counter por año; C excluye NULL | Fechas demo, no primera lectura ni Fecha alta de sitio |
| PG07 | Sensores sin actividad registrada. Ausencia de lecturas con vínculo conocido | PG07, L74–94 | sensors; EXISTS channels; NOT EXISTS channels INNER observations | Subconsultas correlacionadas, ventana semiabierta con offset explícito | 0 | Demo + series observadas **sin** vínculo entre ambos | H/C/S; A confirma 0 enlaces; C casos positivos/negativos/temporales exactos | **Bloqueado físicamente**; funcional probado; 0 no prueba actividad universal |
| PG08 | Ranking de zonas monitoreadas. Ordenar zonas por sensores vinculados al catálogo | PG08, L96–118 | zones INNER locations INNER stations INNER sensors | CTE, COUNT DISTINCT, HAVING, DENSE_RANK OVER | 21 | Mixto demo/distritos actuales | H/C/S; A Counter por zona/ranking; C empate 1,1; S todas las filas | Demo; no certificar zonas físicamente monitoreadas en enero |
| PG09 | Consulta utilizando vistas. Resumir actividad por canal | PG09, L120–128 | channel_activity → observations; sin JOIN en SELECT/vista | Vista con COUNT, MIN/MAX, GROUP BY | 360 | Lecturas reales; canales lógicos derivados | H/C/S; A cuenta y calcula extremos de todo el archivo, compara total/muestra; S todas las filas de su alcance | Evidencia técnica de vista sobre datos reales, no sensor físico |
| PG10 | Consulta utilizando procedimientos almacenados o funciones. Contar canales por estación | PG10, L130–135 | stations; channels_at_station() consulta channels; sin JOIN explícito | Función SQL STABLE, COUNT, ORDER BY | 5.133 | Catálogo observado/derivado, no depende de demo | H/C/S; A Counter de canales por estación; S todas las filas, incluidos 0 | Función acreditada localmente; **cuenta canales, no sensores** |

En H no se guardaron todas las filas SQL, solo cantidad y primeras cinco; A no
afirma compararlas con una salida completa inexistente. Genera por separado todas
las filas esperadas y su hash, y coteja cantidad/muestra H. S sí compara todas las
filas SQL en su alcance; PG01–PG08 y PG10 usan los catálogos/administración completos
y coinciden con H; **PG09 de S devuelve 126 canales de su subconjunto**, no 360.
La función y la vista no incorporan por sí mismas un filtro anual: operan sobre
el contenido que se haya cargado. La ventana está fijada únicamente donde el SQL
la expresa, como PG07 y el complemento avanzado.

### Muestras pequeñas de H (no resultados inventados)

IDs completos y hasta cinco filas por ID están en H; estos extractos omiten campos
largos, no cambian los resultados:

| ID | Ejemplo de resultado |
|---|---|
| PG01 | category_id=MAD-AIR:1, category_name=MAD-AIR:1, sensor_count=428 |
| PG02 | location_name=«TÁCTICO - PICO BALAITUS, 1 N-S», sensor_count=1 (IDs completos en H.PG02.sample[0]) |
| PG03 | active=2567; inactive=2566 (dos filas) |
| PG04 | Organización demo 01, sensor_count=5133 |
| PG05 | «Ctra. Acceso Estación de Hortaleza - Virgen del Carmen-Av. San Luis», sensor_count=1 |
| PG06 | 2020=887; 2021=1095; 2022=1095; 2023=1095; 2024=961 |
| PG07 | [] |
| PG08 | madrid:district:8, sensor_count=554, zone_rank=1; district:15, 432, rank=2 |
| PG09 | channel:3aecc8a9ce867323afb156b320f8a1b944b8a8192e42e3d9b845a2d159675743, readings=2964, UTC [2024-12-31T23:00:00+00:00,2025-01-31T22:45:00+00:00] |
| PG10 | station:00152fe25d8dd8d8018ca667ea5e69a324db25b385f5e9ea66ff56cc5e00142a, channel_count=0 |

PG07 tiene ficha específica, casos y solicitud lista para JP en
[`pg07_limite_evidencia.md`](pg07_limite_evidencia.md). No modificarla para
obtener una fila ni reemplazar sensor_id NULL con demo.

## Trazabilidad de operaciones SQL exigidas

S usa PostgreSQL 16.15, imagen local `postgres:16-alpine`, ID registrado, 1 CPU,
512 MiB, red none, sin puertos ni montajes de host. Contenido seleccionado:
**2.843 aire** con original_time el 1 de enero y **64 primeros intervalos tráfico**
del archivo aceptado. No es una muestra representativa ni aleatoria de toda la red.
No se mezclan promedios de aire/tráfico ni de magnitudes/unidades diferentes.
El ranking complementario compara conteos de filas, no valores medidos;
aire horario y tráfico de 15 minutos tienen frecuencias distintas. Se usa para
demostrar SQL, no para inferir intensidad física o prioridad de monitoreo.

| Operación SQL | Consulta/archivo | Evidencia de ejecución | Resultado | Estado |
|---|---|---|---|---|
| SELECT | Todas PG | H/C/S | Diez consultas ejecutadas | Verificado |
| WHERE | PG06/PG07; resumen aire al final de queries.sql | C/S | Filtra NULL/fechas/calidad | Verificado |
| ORDER BY | Todas PG | C/S | Filas comparadas en orden canónico | Verificado |
| DISTINCT | PG02/PG05/PG08, COUNT(DISTINCT sensor_id) | S | 5.133/5.133/21 filas no vacías | Verificado, sensores demo |
| INNER JOIN | PG02/PG05/PG07/PG08; vista observation_contract | C/S | PG02 5.133; 11 agregados de aire no vacíos | Verificado; JOIN real adicional en vista |
| LEFT JOIN | PG01/PG02/PG04; observation_contract | C/S | C organismo vacío cuenta 0; S agregados con 2.843 lecturas | Verificado |
| GROUP BY | PG01–06/PG08/PG09, resumen aire | H/C/S | Grupos y conteos contrastados con Python | Verificado |
| HAVING | PG05/PG08; sql_avanzado_observado.sql | C/S | Grupos no vacíos, 5 filas del ranking observado | Verificado |
| COUNT | Todas PG, función y vista | H/C/S | Cantidades de matriz | Verificado |
| SUM | Resumen aire exacto de queries.sql | S.canonical_air_aggregate | MAD-AIR:8, ug/m3: 18.056 en 528 lecturas | Verificado; suma aritmética de valores, no dosis/exposición |
| AVG | Mismo resumen | S | MAD-AIR:8 = 34,196969696969695 ug/m3 | Verificado; no mezclar tipos/unidades |
| MIN / MAX | Resumen aire y channel_activity | A/S | MAD-AIR:8, extremos 3/109; vista cotejada con archivo | Verificado |
| Subconsultas | PG07 EXISTS/NOT EXISTS; función PG10 | C | Tres sensores esperados en fase ampliada | Verificado funcionalmente; no físico |
| CTE | PG08; sql_avanzado_observado.sql | C/S | 21 zonas demo; 5 filas complementarias observadas | Verificado |
| Window functions | DENSE_RANK en PG08 y complemento | C empate 1,1; S observed_cte_dense_rank | Complemento: conteos 64,23,23,23,23; ranks 1,2,2,2,2 | Verificado, no inferir cobertura física |
| Fechas | PG06 EXTRACT; PG07 rango Madrid; resumen por original_time | C/S | Límites exactos y microsegundos, año NULL excluido | Verificado |
| Consultas apoyadas por índices | Filtro canal/tiempo en S.explain_analyze.channel_time | EXPLAIN ANALYZE, BUFFERS, FORMAT JSON READ ONLY | Bitmap Index Scan del UNIQUE natural, 23 candidatas, LIMIT 20 | Verificado para subconjunto v2 |

La consulta complementaria es pequeña y solo lectura; no reemplaza PG08 ni
pretende convertir canales en dispositivos. El resumen de aire se reutilizó del
SQL canónico mediante `read_air_summary()`: once filas agrupadas por magnitud y
unidad. No se copió/reimplementó una variante para conseguir evidencia.

## Modelo, integridad, índices y rendimiento

* [Auditoría formal de las doce tablas](normalizacion_3fn.md): PK/candidatas,
  UNIQUE, todas las FK, DF parciales/transitivas y diferencias v1/v2. Resultado:
  **channels y observations no 3FN estricta**; propuesta sin pérdida no aplicada.
* [E-R existente de doce tablas](../../docs/arquitectura/diagramas.md#3-e-r-postgresql--doce-tablas-preliminares):
  relaciones reales, usuarios sin FK, demo separado; la figura LaTeX es extracto.
* S inventaría **12 PK, 10 UNIQUE, 22 FK y 27 CHECK** en v2, además de NOT NULL,
  trigger observation_source y **27 índices B-tree**. Definiciones completas en JSON,
  no capturas ilegibles. C ejecuta 9 comprobaciones de esquema y 14 controles
  originales: unicidad, replay idéntico, conflicto inmutable y sensor de otra estación.
* Coherencia de fuente/estación/tipo/versión mediante FK compuestas y trigger.
  UNIQUE natural observación `(channel_id,observed_at,timestamp_role)`; `_id` compartido
  con MongoDB por contrato, no FK cruzada. SQL no recalcula los hashes de payload.
* `channel_activity`: COUNT/MIN/MAX por canal con lecturas, PG09=360 en H.
  `channels_at_station(text)`: COUNT de canales; incluye estaciones con 0, PG10=5.133.
* Índices explícitos: sensor_station, sensor_category, sensor_org, channel_station,
  observations_time. Los otros 22 respaldan PK/UNIQUE. El UNIQUE natural ya proporciona
  prefijo canal/fecha; no se añadió un índice duplicado ni se forzó el planificador.
* S guarda dos planes ANALYZE/BUFFERS completos. El filtro selectivo usa el índice
  natural; el ranking usa Seq Scan, Aggregate, Sort, WindowAgg, Limit. Esto es
  razonable al recorrer todo el subconjunto; no constituye fallo de índice.
* [Benchmark anual](performance_real_2025.md): **v1**, 1.076.813 filas. Medianas
  históricas PG09 711,360 ms; PG10 139,113 ms; filtro canal 0,139 ms; tiempo 0,839 ms.
  No son resultados medidos de v2 ni del servidor compartido. S contiene tiempos
  de una ejecución local corta, no un benchmark comparativo de 748.889 filas.

### Limitaciones de integridad reproducidas, no escondidas

`tests/integration/postgres_v2_limitations.sql` usa filas de prueba explícitas en
la base propia de S y ROLLBACK: demuestra que CHECK puede aceptar UNKNOWN con
element_type/interval_minutes NULL, que una referencia JSON de forma inválida
puede escapar al CHECK y que DELETE no está bloqueado por el trigger de UPDATE.
Los marcadores quedan en S.ddl_limitations_reproduced. **La prueba pasa porque
documenta el comportamiento real, no porque esas limitaciones sean deseables.**
No altera originales ni modifica silenciosamente DDL de JP. Propuesta de equipo:
regla `IS TRUE`/NOT NULL condicional, objeto raw_reference exigido explícitamente,
política de permisos o trigger DELETE; revisar compatibilidad y repetir regresión.

## Material integrable y revisión del equipo

Fernanda puede usar ahora las subsecciones PostgreSQL de `02-modelos.tex`,
`03-consultas.tex`, `04-validacion.tex`, esta matriz y tres JSON acotados.
`normalizacion_3fn.md` y la ficha PG07 contienen el razonamiento detallado que no
conviene volcar íntegro al informe. El [README de reproducción](reproduccion_cierre.md)
separa offline, SQL controlado, archivos grandes y carga completa.

Pendiente del equipo: aceptar/rectificar las excepciones de normalización,
endurecer integridad en una versión aprobada, validar alcance demo con docente,
obtener inventario físico fechado para PG07, completar evidencia MongoDB ajena a
este cierre y compilar/revisar LaTeX en un entorno disponible. No hay PDF compilado
en esta sesión. No cambiar una limitación de datos por un PASS ficticio.

## Pruebas y correcciones durante esta sesión

* Suite Python final: **59 pruebas aprobadas**, incluyendo comprobación de
  hashes de los tres reportes contra el código actual y control estático LaTeX
  (llaves, entornos, inputs y citas). No acredita renderizado ni paginación PDF.
* C: PASS, diez consultas exactas más nueve escenarios PG07; ROLLBACK y cleanup.
* A: PASS, seis derivados v2, originales/catálogos, 748.889 identidades/referencias,
  cero duplicados, diez totales/muestras cotejados. Rechaza explícitamente informes
  históricos FAIL, generación distinta, replay o limpieza incompletos.
* S: PASS, diez comparaciones completas en el alcance declarado, once agregados
  aire, ranking observado, dos planes y tres limitaciones DDL reproducidas.
* `bash scripts/validate_sprint1.sh`: Python aprobó, luego **bloqueo por Node.js
  ausente**. No se ejecutaron `--engines` completo, `--datos`, benchmark masivo ni
  compilación PDF por prerrequisitos faltantes y/o por existir evidencia masiva
  vigente suficiente. No se instaló software ni se descargaron imágenes.
* Primer intento de la ampliación PG07: error al parsear JSON multilinea de
  json_agg; corregido usando jsonb_agg para serializar la salida en una línea,
  sin cambiar el SELECT canónico. La regresión posterior pasó.
* Primer arranque del harness observado: importar el cargador masivo arrastraba
  pandas, ausente. Se reutilizó `load_catalogs()` del verificador existente,
  independiente de ese driver; no se instaló pandas ni se alteró el cargador de JP.
* Primera medición avanzada: el guard de EXPLAIN rechazó comentarios iniciales.
  Se eliminan únicamente líneas de comentario antes de pasar el SELECT/CTE al
  guard existente. La consulta sigue ejecutándose desde el mismo archivo; no se
  desactivó la protección READ ONLY ni se introdujo SQL alternativo.

Los FAIL/ejecuciones intermedias de desarrollo se conservan en `/tmp/opencode`,
incluidos `smartcity-s1-sql-z8mjgnun.json` y
`cierre-postgresql-subconjunto.json`. No se cambiaron sus estados. Los reportes
adjuntos corresponden a ejecuciones posteriores válidas; los hashes no fueron
retocados manualmente para aparentar correspondencia.
