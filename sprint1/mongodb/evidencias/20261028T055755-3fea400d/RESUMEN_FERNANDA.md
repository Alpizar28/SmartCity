# Cierre técnico MongoDB — Sprint 1 — Kembly

El bloque MongoDB Madrid v2 tiene **PASS técnico nativo**, sustentado por la
ejecución `execution-20261028T055755-3fea400d`. La aceptación académica de las
adaptaciones de sensor/canal, reglas demo y períodos sigue siendo una decisión
separada. Este cierre no certifica la base compartida.

## Ejecución y procedencia

- Código oficial: `main`, commit `804d6a551dc84e22d901b64554c30a712b951f77`.
- Contrato y catálogo: `madrid-draft-v2`; generación `expanded-v2-2025-01`.
- Intervalo del auxiliar: 2026-10-28 05:57:55–06:14:05 UTC.
- MongoDB 7.0.16; Docker 29.1.3; Python 3.11.16 y veinte versiones del lock.
- Contenedor propio: `smartcity-full-mongodb-ff51a93dc802`, red `none`, sin
  puertos publicados, 2 CPU y límite de 2 GiB. Pico registrado: 1.253.732.352 bytes.
- El contenedor y sus volúmenes anónimos se eliminaron; el informe nativo lo
  comprobó. No hubo acceso al servidor compartido ni cambios de grupos/socket.

La evidencia principal es [execution-d26e40706dcd.json](originales/execution-d26e40706dcd.json).
Su SHA-256 es `639a295191a8321c0eb40505842435e70d53bb6ca5de9a81c2f149f36862b585`.
Los 18 archivos del manifiesto original fueron verificados. Los logs se copiaron
con extensión `.txt`, conservando exactamente sus bytes; la correspondencia está
en [MANIFIESTO_ORIGEN.json](MANIFIESTO_ORIGEN.json).

## Carga, replay y conciliación

| Control actual | Resultado |
|---|---|
| Muestra nativa oficial | PASS: 3 lecturas, diez consultas, 1 evento y 1 alerta |
| Carga masiva | PASS: **748.889 lecturas**, 91.959 aire y 656.930 tráfico |
| Replay de lecturas | PASS: segunda pasada compara documentos completos; total constante |
| Replay de derivados | PASS: dos generaciones de eventos/alertas con conteos constantes |
| Incidentes | 14.388 expedientes anonimizados de 2026 |
| Eventos y alertas demo | 10.841 eventos y 10.841 alertas locales |
| Reconciliación | Verificador actual PASS; mismo conteo e idéntica huella SQL/Mongo |
| Integridad de entradas | Siete archivos privados idénticos al snapshot de la ejecución |
| Código y contrato | Archivos oficiales idénticos al commit; sin cambios de contrato |

Huella compartida de IDs/payloads:
`9e8a6b6b7e1aa527693aa9c71ca8dc44123e2d4602f8b94f2ba2afa4b54c69a0`.

La reconciliación [reconciliation.json](originales/reconciliation.json) se ejecutó
en esta sesión contra el informe PostgreSQL identificado por ruta y hash.
**No se volvió a ejecutar PostgreSQL:** el informe de ese motor es la referencia
previa `execution-0652c6cd8bbc.json`, no un sustituto de la nueva ejecución MongoDB.

## Diez consultas: resultado individual

Todas se implementan en `sprint1/basico/consultas_mongodb_v2.js`, función
`consultar()`, con `buscar()` para filtros/proyección/orden y `agrupar()` para
Aggregation Framework. Se contrastaron durante la carga mediante
`comprobar_consultas()` y, al cerrar, se repitió el cálculo Python independiente
sobre el paquete actual, sin volver a cargar bases. Véase
[verificacion_independiente.json](verificacion_independiente.json).

| ID | Operación y resultado nativo | Estado y alcance |
|---|---|---|
| MG01 | 2.936 lecturas del canal seleccionado y su snapshot | PASS técnico; canal lógico, no sensor físico acreditado |
| MG02 | 748.765 lecturas en `[2024-12-31T23:00Z, 2025-01-31T23:00Z)` | PASS; ventana semiabierta de enero en Madrid; 124 aceptadas quedan fuera del filtro |
| MG03 | 11 grupos de aire válido, 91.959 lecturas, mínimos/máximos/promedios | PASS; se separan variable y unidad; NO₂: 1–157 ug/m3 |
| MG04 | 10.841 eventos derivados por intensidad >2.000 veh/h | PASS técnico; regla docente demo, no umbral oficial |
| MG05 | 10.841 alertas agrupadas en 14 zonas | PASS técnico; emisiones locales actuales de replay |
| MG06 | 21 grupos zona/fuente/tipo/unidad sobre 653.997 lecturas con zona | PASS; se excluye zona desconocida, sin mezclar unidades |
| MG07 | 12 grupos fuente/tipo de medición/unidad, 748.889 lecturas | PASS técnico; no clasificación física acreditada de dispositivos |
| MG08 | 14 categorías, 14.388 incidentes; 2 sin categoría | PASS; expedientes de accidentes de 2026, separados de lecturas de 2025 |
| MG09 | 2 grupos fuente/calidad: 91.959 MAD-AIR/V y 656.930 MAD-TRAFFIC/N | PASS; Aggregation Framework |
| MG10 | 10.841 lecturas con fecha, tráfico, calidad N, umbral y zona conocida | PASS; filtro combinado, proyección y ordenamiento |

No se promedia aire junto con tráfico. Los resultados completos, parámetros y
muestras acotadas están en el informe nativo; no se adjunta el dataset privado.

## Colecciones y validadores efectivamente capturados

| Colección | Documentos | Validador observado |
|---|---:|---|
| `readings` | 748.889 | Sí; `strict`, `validationAction=error`, BSON Date, identidad cruzada y política v2 |
| `incidents` | 14.388 | Sí; esquema de incidente anonimizado, origen MAD-CRASH y fecha 2026 |
| `derived_events` | 10.841 | Sí; origen derivado y marca de evento no oficial |
| `alerts` | 10.841 | Sí; emisión BSON Date, replay y entrega solo a colección local |
| `organizations` | 1 | No hay validador instalado en esta ruta v2 |
| `users` | 5.133 | No hay validador instalado en esta ruta v2 |
| `sensors` | 5.133 | No hay validador instalado en esta ruta v2 |

Los registros administrativos son sintéticos. No acreditan inventario físico ni
autoría de lecturas. Para los tres validadores derivados no se serializó
`validationLevel` explícito en las opciones; sí `validationAction=error`.
La ejecución comprueba configuración y carga válida; **no incluye una batería
de inserciones inválidas ni pruebas de permisos/autenticación MongoDB**.

Los catálogos se validan desde `catalogs.json` y se desnormalizan en las lecturas;
la captura no muestra una colección `catalogs` ni FK entre motores. Los esquemas
completos están en [native-metadata.json](originales/native-metadata.json).

## Índices y planes

Se capturaron **13 índices en siete colecciones**: siete `_id_` y seis índices
adicionales:

| Colección | Clave adicional | Unicidad |
|---|---|---|
| `readings` | `(channel_id, observed_at, timestamp_role)` | Único |
| `readings` | `(source_id, measurement_type, observed_at)` | No |
| `readings` | `(zone_id, measurement_type)` | No |
| `incidents` | `(category)` | No |
| `derived_events` | `(rule_version, observed_at)` | No |
| `alerts` | `(zone_id, emitted_at)` | No |

| Plan actual, limitado a cinco resultados | Elección natural y métricas |
|---|---|
| MG01 representativo | IXSCAN del índice único canal/fecha/rol; 5 claves y 5 documentos examinados; 1 ms |
| MG10 representativo | IXSCAN fuente/tipo/fecha y SORT; 656.930 claves y documentos examinados; 6.470 ms |

Los tiempos corresponden a una observación nativa de esos planes, no a un
benchmark repetido ni al costo total de cada consulta. MG10 funciona, pero su
índice actual no evita examinar todo el tráfico; no se afirma optimización total
ni superioridad de rendimiento sobre PostgreSQL.

## Siete operaciones CRUD

El archivo oficial `sprint1/basico/crud_mongodb.js` se ejecutó con `GUARDAR=true`
en el contenedor propio. Se copiaron tres lecturas a `practica_crud`:

| Operación | Evidencia de ejecución |
|---|---|
| `insertOne` | Primera copia e ID utilizado por las operaciones siguientes |
| `insertMany` | Otras dos copias; tres documentos de práctica |
| `findOne` | Salida de una copia por su ID |
| `find` | Salida de las tres copias con proyección |
| `updateOne` | Comprobación de exactamente una modificación |
| `updateMany` | Comprobación de exactamente tres modificaciones |
| `deleteOne` | Comprobación de un borrado y dos documentos restantes |

El log contiene los siete marcadores y `CRUD_BASICO_PASS`. Después se verificó
que `readings` seguía en **748.889** y que la colección de práctica se había
eliminado. Véanse [native-crud.json](originales/native-crud.json) y
[native-crud.txt](originales/native-crud.txt). No se modificaron las lecturas
originales del paquete ni las aceptadas en `readings`.

## Código que debe acompañar la entrega

Conservar el checkout oficial completo en el commit indicado, además de estas
evidencias. [CODIGO_OFICIAL.json](CODIGO_OFICIAL.json) identifica **19 archivos**
con función, SHA-256 y blob Git; todos coinciden con `HEAD`:

- MongoDB: `sprint1/basico/cargar_mongodb_v2.js`,
  `sprint1/basico/consultas_mongodb_v2.js`, `sprint1/basico/crud_mongodb.js`.
- Ejecución/verificación: `scripts/test_mongo_v2_sample.py`,
  `scripts/validar_v2.py`, `scripts/verificar_v2.py`.
- Datos/contrato: `sprint1/basico/preparar_v2.py`,
  `research/datasets/scripts/phase5_contract.py`, `unified_full_load.py`,
  `phase5_postgres_sample.py`, `unified_expand.py`, `phase5_prepare.py`,
  `unified_synthetic.py` (estos últimos bajo `research/datasets/scripts/`).
- Dependencias del harness: `tests/sprint1/validate_real_postgres.py`,
  `sprint1/postgres/queries.sql`, `sprint1/postgres/contract_v2.sql`.
  Su presencia/importación no significa que se ejecutara PostgreSQL nuevamente.
- Entorno: `research/datasets/scripts/requirements.lock`.
- Pruebas complementarias a distribuir: `tests/sprint1/test_mongodb_v2.js` y
  `tests/sprint1/test_resultados_v2.py`; no se usan como sustituto del PASS nativo.

La carpeta `auxiliares/` conserva el recolector externo, su configuración y el
JavaScript de captura, idénticos a sus hashes registrados. **No son código
oficial de main**: añaden captura/CRUD dentro del contenedor antes de que la
función oficial lo limpie, sin alterar los scripts oficiales ni las consultas.

## Límites y cierre para Fernanda

El mínimo de 500.000 documentos MongoDB está superado con 748.889 lecturas
observadas; los incidentes, derivados y administración no se sumaron para
alcanzarlo. El cierre técnico de carga, diez consultas, replay, CRUD, índices,
validadores y reconciliación queda sustentado por esta ejecución actual.

No presentar como aprobados por estas pruebas:

1. Sensor físico: MG01 usa canal lógico y MG07 tipo de medición; no se inventó
   relación sensor–canal. La equivalencia académica requiere aceptación.
2. Alertas oficiales: MG04/MG05 son regla demo y replay local emitido en 2026,
   no avisos oficiales históricos ni umbrales legales.
3. Geografía histórica: las zonas corresponden al inventario disponible, sin
   vigencia histórica confirmada para 2025.
4. Año de incidentes: MG08 usa 2026 y no se integra como accidentes de enero 2025.
5. Producción: no hubo conexión ni carga del servidor compartido; no se
   probaron roles, autenticación real, alta disponibilidad o restauración de backup.
6. Validación negativa: capturar los esquemas no demuestra todos sus rechazos;
   las tres colecciones administrativas no tienen validador en esta ruta.

No es necesario reimplementar las diez consultas ni recuperar las correcciones
locales v1. Fernanda debe incorporar estos resultados y límites al informe;
la aceptación académica y una eventual demostración compartida son decisiones
distintas de este PASS local. No hubo commit, push, merge ni cambios del contrato.
