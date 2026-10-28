# PG07 — sensores sin actividad registrada

## Conclusión

**SQL y demostración funcional: comprobados. Acreditación de inactividad física:
bloqueada por evidencia externa. Vínculos físicos sensor–canal acreditados: 0.**

No se modificaron `queries.sql`, el DDL común, sensores/canales operacionales ni
mediciones originales. Cero filas **no** significa que todos los sensores están
activos, ni que no existan dispositivos averiados.

## Universo revisado y resultado

Paquete leído in situ:
`/home/dburger/Descargas/SmartCity_DATASET_COMPLETO_PRIVADO.zip`.
Generación `expanded-v2-2025-01`, contrato `madrid-draft-v2`.
Los hashes, tamaños, campos de catálogos y cabeceras oficiales revisados están en
[`cierre_auditoria_v2.json`](evidencias/cierre_auditoria_v2.json).
Se verificaron los seis derivados v2, sus siete originales referenciados y el
diccionario oficial de tráfico; el manifiesto del ZIP coincide con preparación.

| Evidencia | Qué identifica | Qué NO acredita |
|---|---|---|
| catalogs.json v2: 5.133 estaciones, 360 canales | Sitios/series lógicas deterministas | Identidad física del dispositivo |
| Todos los channels.sensor_id NULL; catalog_basis=observations | Series que aparecieron en lecturas | Universo independiente de canales sin actividad |
| 748.889 documentos aceptados, sensor_id NULL | Hechos observados y origen verificable | Quién los midió físicamente |
| administrative_seed.json | 5.133 sensores/usuarios y 1 organismo synthetic | Inventario municipal físico |
| admin-demo-v2, semilla 20261010 | Reproducción exacta del demo | Vínculo con observaciones |
| Inventario aire: CODIGO, CODIGO_CORTO, variables, Fecha alta | Estación y disponibilidad de magnitudes | Serie/serial físico ni instalación de cada instrumento |
| Aire: ESTACION, MAGNITUD, PUNTO_MUESTREO | Punto/magnitud/técnica que forma channel_key | Evidencia independiente de aparato y vigencia |
| Inventario tráfico: id, cod_cent, tipo_elem, coordenadas | Punto lógico y elemento | sensor_id físico y período de asignación |
| Tráfico: id, fecha, tipo_elem, intensidad, periodo_integracion | Intervalo lógico; muestras no son minutos | Inventario físico independiente |
| Inventario meteo y catálogos históricos incluidos | Sitios/variables y ausencia de enlaces documentados | Mediciones meteo aceptadas v2 |

También se revisaron `unified_synthetic.py` (prohíbe explícitamente atribuir
lecturas al demo), `phase5_prepare.py`, `phase5_contract.py`, `preparar_v2.py`,
`CONTRATO_UNIFICADO.md`, `05_postgresql_design.md`, la matriz docente y los
manifiestos/evidencias v1 y v2. La documentación histórica no aporta inventario
de aparatos fechado. Los catálogos adicionales/QA incluidos en el ZIP quedan
inventariados por el auditor; no se ejecutó ningún script del ZIP.

La ausencia afirmada está acotada a **los archivos y contratos revisados**; no es
una prueba de inexistencia de inventario en toda la municipalidad. No se
interpreta compartir estación, coincidir en número o reproducir un ID hash como
prueba de identidad física. Los códigos de series son estables/reproducibles;
el identificador físico independiente y su vínculo temporal no están presentes.

El sesgo de cobertura importa: un catálogo construido desde observaciones no
puede descubrir por sí solo un canal que jamás reportó. Incluso si llegara un
vínculo físico parcial, se necesitaría inventario independiente/completo para
evaluar todos los sensores del período.

## SQL canónico e interpretación

Autoridad única: [`queries.sql`, bloque PG07](queries.sql#L74-L94), SHA-256
`e0944eb54a777aa22714a9dbd23b23a112a6d34eb906622cdb37c3feb89eaed9` del archivo.
El parser `read_queries()` devuelve ese SELECT sin comentarios ni terminador;
no lo sustituye por una variante equivalente.

* `EXISTS`: exige al menos un canal asociado al sensor.
* `NOT EXISTS` sobre todos sus canales: ninguno debe tener observaciones
  aceptadas en `[2025-01-01 00:00+01, 2025-02-01 00:00+01)`.
* Equivalente UTC: `[2024-12-31T23:00Z,2025-01-31T23:00Z)`.
* No usa estado administrativo como actividad; no usa primera lectura como
  instalación; no atribuye lecturas sin vínculo. No introduce duplicados por JOIN.
* Ausencia de observaciones **aceptadas** puede responder a cuarentena,
  cobertura/selección o transporte, no necesariamente falta de medición física.
  Tráfico v2 está acotado a `id % 20 == 0`, no a toda la red de Madrid.

## Prueba exacta, sintética y reversible

Se fortaleció el harness existente, no se creó una segunda PG07:

* `scripts/test_sprint1_sql.py`: ejecuta las diez consultas exactas con resultados
  esperados y, en otra transacción, reutiliza **la misma** PG07 para los casos extra.
* `tests/integration/postgres_canonical_fixture.sql`: casos originales.
* `tests/integration/postgres_pg07_cases.sql`: solo casos antes faltantes.
* `tests/sprint1/test_queries.sql`: conserva sus 14 controles de integridad.
* Evidencia persistente: [`cierre_pg07_controlado.json`](evidencias/cierre_pg07_controlado.json).

| Caso | Esperado y obtenido en la fase ampliada |
|---|---|
| Canal con lectura exactamente en inicio incluido | sensor-active excluido |
| Canal sin lecturas | sensor-no-readings incluido |
| Única lectura exactamente en fin excluido | sensor-outside incluido |
| Única lectura 1 microsegundo antes del inicio | sensor-before incluido |
| Lectura 1 microsegundo antes del fin | sensor-last excluido |
| Sensor sin canal, pero estación con lecturas sin asignar | sensor-unlinked excluido |
| Sensor con dos canales, uno activo y otro vacío | sensor-active excluido |
| Sensor con dos canales vacíos | sensor-no-readings una sola vez |
| Estado active sin lecturas; inactive con lecturas | La consulta depende de lecturas, no del estado |

Resultado ampliado exacto y ordenado:
`sensor-before`, `sensor-no-readings`, `sensor-outside`. Tres filas, sin duplicados.
Cada fixture se revierte con ROLLBACK y se comprueba cero remanentes; el contenedor
propio se elimina. La etiqueta observed de las filas fabricadas obedece al CHECK
del esquema: su provenance y entorno las identifican como **prueba sintética**,
nunca como datos de la municipalidad.

La evidencia masiva v2 histórica devuelve 0 filas; el auditor vuelve a contrastar
ese resultado con los archivos verificados y la nueva prueba local v2 lo confirma
sin inventar vínculos. No hubo una nueva carga masiva ni cambios de asociaciones.

## Solicitud concreta a JP (lista para enviar)

Necesitamos un **inventario oficial o documentado de dispositivos**, independiente
de las lecturas y correspondiente a enero de 2025, y una tabla de correspondencia:

`physical_sensor_id, source_id, station_original_code, channel_original_key,
measurement_type, valid_from, valid_to, evidence_uri, source_file_sha256,
inventory_complete_for_scope`.

1. Identificador estable de instrumento (no el sensor demo ni solo station_id).
2. Fuente/publicador, licencia, URL/documento y snapshot con SHA-256.
3. Correspondencia comprobable con las claves originales: aire
   estación/magnitud/punto de muestreo; tráfico id/tipo_elem; después se derivan
   los mismos station_id/channel_id con stable_id, sin reinterpretarlos.
4. Vigencia efectiva y cambios de aparato/canal durante la ventana; documentar
   intervalos semiabiertos y zona horaria. Evitar asignaciones solapadas ambiguas.
5. Cobertura completa del inventario, incluso aparatos/canales sin lecturas, y
   confirmación de qué sensores debían reportar en el estrato/período seleccionado.
6. Categoría, instalación, organismo/estado solo si tienen evidencia propia;
   no deducirlos de actividad ni utilizar Fecha alta del sitio como instalación.

La carga propuesta, cuando exista ese insumo, debe verificar unicidad/referencias,
reproducir los hashes y vigencias, comparar una evaluación independiente y conservar
el dataset original. Requiere revisión contractual del equipo antes de incorporarla
a implementación común. Hasta entonces PG07 está **funcionalmente probada**, pero
no **físicamente acreditada**.
