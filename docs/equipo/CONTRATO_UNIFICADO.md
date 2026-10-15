# Contrato común: `madrid-draft-v1`

Implementación: `unified-v1`. Especificación de integración: **Contrato_Datos_SmartCity.pdf**, Kembly Garro, 14/10/2026, decisiones 1.0. Esta rama implementa la propuesta; no constituye aprobación de los demás integrantes ni autorización para modificar el servidor compartido.

## Decisiones y límites

- SQL: `smartcity`; MongoDB: colección estándar `readings`, `_id = measurement_id`.
- `madrid-draft-v1-frozen` queda obsoleto como interfaz vigente. Se conserva la evidencia de Fase 5 sin modificar sus resultados ni hacerla pasar por una ejecución del contrato nuevo.
- La etiqueta contractual es la exigida por el PDF, `madrid-draft-v1`. El cambio de identidad de canal y de política de aceptación respecto de los prototipos queda registrado como migración de implementación `unified-v1`, transformación `madrid-normalize-v2`. Cualquier cambio semántico posterior requiere nueva versión contractual y migración revisada.
- No fusionar observaciones antiguas y nuevas. Catálogos y mediciones de desarrollo se regeneran juntos en `private_results/unified-v1/`. `results/unified-v1/` contiene únicamente evidencia acotada revisable.
- No se acredita simultaneidad, unidad meteorológica, CRS, vigencia histórica ni identidad física sin evidencia. No crear GeoJSON, índices 2dsphere, TTL ni alertas supuestamente reales.

## Identidades y serialización

`stable_id(kind, *parts)` produce `kind + ':' + sha256(canonical(['sca-id-v1', *parts]).encode('utf-8')).hexdigest()`.

`canonical` usa JSON UTF-8 sin normalización Unicode adicional, claves ordenadas, `ensure_ascii=False`, separadores `(',', ':')`, sin NaN/Infinity. El orden y los tipos de los elementos de listas se conservan. No concatenar partes ni recalcular IDs por motor.

| Identidad | Partes después de `sca-id-v1` |
|---|---|
| estación | `source_id`, código original convertido a texto |
| canal | `source_id`, **`station_id`**, `channel_key` |
| medición aceptada | `channel_id`, UTC ISO-8601 con `Z`, `timestamp_role` |
| ubicación | `station_id`, `current-inventory` (snapshot de inventario asociado) |

`channel_key`: aire/meteo `[station_code, variable_code, sampling_point_or_null]`; tráfico `[station_code, element_type]`. Los códigos conservan su representación original: no convertir arbitrariamente `04` a `4`.

La identidad histórica del canal omitía la estación como parte explícita. Esta generación cambia canales y mediciones; no altera los IDs de estación. Para correspondencia histórica usar fuente, código, clave lógica y tiempo original, no actualizar hashes in situ.

## Tiempo y aceptación

- Zona de conversión: `Europe/Madrid`, nunca la del sistema.
- Aire: H01–H24 son extremos horarios documentados; H24 pasa al siguiente día local.
- Solo `documented_local` y `publisher_confirmed_local` se admiten en observaciones.
- Horas inexistentes, ambiguas sin evidencia y semántica no confirmada van a cuarentena. No se inventa `fold`.
- Meteo y tráfico mantienen actualmente estados pendientes: **no entran en la muestra aceptada**. Resolverlo requiere evidencia del publicador, revisión versionada y regeneración; no basta cambiar una etiqueta.
- En cuarentena `observed_at`, `measurement_id` y `_id` no se publican como identidades confirmadas. La referencia al original permite reconstruir el registro.
- Unidades desconocidas: `unit=NULL`, `unit_status=pending_dictionary`; las candidatas no autorizan agregaciones.

## Trazabilidad y conflictos

`source_version` es el SHA-256 hexadecimal completo del archivo, igual a `raw_reference.sha256`. Se conservan ruta, fila, columna y miembro ZIP cuando corresponde. La versión debe pertenecer a la fuente de la estación, canal y tipo.

`payload_hash = stable_id('payload', contenido)`; contenido incluye los campos exportados salvo `raw_reference`, `payload_hash` y el diagnóstico `time_error`. Excluir el localizador permite reconocer filas repetidas del mismo snapshot; `source_version` permanece dentro del contenido. Un cambio de archivo para la misma identidad debe investigarse como conflicto, no sobreescribirse automáticamente.

- ETL: ledger SQLite privado para deduplicación; discrepancias registradas en `conflicts.extjsonl.partial` bloquean la publicación de un lote completo.
- PostgreSQL: observaciones inmutables, claves compartidas y unicidad canal/tiempo/rol. El replay acepta el mismo contenido; un cambio genera error. El controlador conserva el error de conflicto en su evidencia.
- MongoDB: validar referencias antes de cargar; preflight y upsert filtrado por ID/hash. El conflicto se registra en `import_conflicts` y no cambia la lectura existente. La prueba usa un único escritor en una base desechable; no promete atomicidad multi-documento ante escritores concurrentes en producción.

## Datos administrativos sintéticos autorizados

Fuente de autorización: conversación aportada por Jose del **10/10/2026**, respuesta docente de las 21:14: «Pueden poner datos aleatorios a la hora de la carga». Resuelve la posibilidad de simular atributos administrativos faltantes; no acredita sensores reales, mediciones, relojes ni unidades. No se versiona el número telefónico del mensaje.

`unified_synthetic.py` genera con semilla `20261010` y versión `admin-demo-v1`: organismos, usuarios y sensores ficticios con fechas y estados administrativos. Todos llevan `data_origin=synthetic`, procedencia y propósito. Los correos usan `example.invalid`; no se inventa consentimiento de personas reales.

Se cargan en `smartcity_demo.entities`, **no** en inventario ni observaciones oficiales. No existe relación inventada entre sensor y canal observado. Este demo no acredita PG01–PG08 con sensores reales ni reemplaza las adaptaciones de consultas de Daniel.

## Reproducción local

Para el lote anual de más de un millón de observaciones, usar [AMPLIACION_REAL_SPRINT1.md](AMPLIACION_REAL_SPRINT1.md) y los scripts `unified_expand.py`, `unified_full_load.py` y `unified_full_verify.py`. El alcance y comandos de esta sección conservan la prueba inicial acotada. La nueva documentación oficial de tráfico descubre una interpretación incorrecta de `periodo_integracion`; esa fuente continúa bloqueada y su corrección incompatible requiere revisión contractual, no un cambio de estado.

Desde la raíz del repositorio, con las dependencias Python y snapshots locales verificados:

```bash
.venv/bin/python -m pytest research/datasets/tests -q
.venv/bin/python research/datasets/scripts/phase5_prepare.py --dry-run
.venv/bin/python research/datasets/scripts/phase5_prepare.py
.venv/bin/python research/datasets/scripts/unified_synthetic.py
.venv/bin/python research/datasets/scripts/phase5_postgres_sample.py
.venv/bin/python research/datasets/scripts/phase5_native.py --engine mongodb
.venv/bin/python research/datasets/scripts/unified_verify.py
```

Los scripts nativos usan exclusivamente `unix:///var/run/docker.sock`, imágenes locales `postgres:16-alpine` y `mongo:7.0.16`, contenedores propios con red deshabilitada y sin puertos publicados. No leen `.env`, DSN ni contexto remoto, no descargan imágenes y eliminan únicamente sus contenedores/volúmenes. Las credenciales de prueba solo existen dentro del PostgreSQL aislado.

El ETL recorre el conjunto auditado de enero de 2025, tráfico `ID % 20 == 0`. Produce todos los aceptados en `accepted.extjsonl`, cuarentena referenciada, catálogos y una muestra acotada de 5.000 para prueba nativa. **Probar 5.000 no acredita una carga de 100.000 ni una carga del lote completo.** Reejecutar una preparación terminada verifica configuración y hashes; si cambian, bloquea la sobrescritura.

## Coordinación pendiente

- Daniel: adaptar sus `queries.sql`, `test_schema.sql`, `test_queries.sql` a este DDL y revisar PG01–PG10; separar ausencia de lecturas de avería. Los ejemplos PG de Jose se ejecutan, pero las consultas físicas vacías no acreditan cumplimiento funcional.
- Kembly: adoptar IDs, Extended JSON, catálogos, validación y política de conflictos; no sustituir su implementación con los scripts de prueba.
- Fernanda: incorporar esta decisión y la matriz `unified_fields.csv` en los diseños y diccionario de entrega. Los documentos históricos conservan avisos de supersesión.
- Equipo: revisar diff y evidencia, aprobar versión y resolver relojes/unidades pendientes. Solo después planificar carga compartida con autorización, respaldo y recuperación; no hay migración automática destructiva.
