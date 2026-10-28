# Recuperación de insumos históricos

**Actualización de integración:** el usuario autoriza integrar y publicar la consolidación documental en `main` aunque la reproducción siga incompleta. Esto no convierte los 83/85 tests en PASS ni modifica la evidencia. Las referencias a «sin merge/push» y «Listo para PR: NO» más abajo describen los checkpoints previos, no una prohibición vigente de integrar documentación.

**Pendiente, sin bloquear el desarrollo nuevo:** los dos SQLite regenerados y las 13 respuestas históricas siguen sin recuperación exacta acreditada. No se relajan los controles ni se declara reproducción completa. Este pendiente no invalida `madrid-draft-v1-frozen`: el [plan de implementación](https://github.com/Alpizar28/SmartCity/blob/9d84a34e529a72b316c540bff549080c906b0126/docs/equipo/PLAN_IMPLEMENTACION_SPRINT1.md) permite trabajo nuevo local sobre campos congelados, con pruebas separadas y sin cargas autorizadas. La consolidación documental y sus pendientes se conservan en `main` tras la integración autorizada.

La [auditoría lógica posterior de SQLite](https://github.com/Alpizar28/SmartCity/blob/9d84a34e529a72b316c540bff549080c906b0126/docs/equipo/AUDITORIA_LOGICA_SQLITE.md) compara todas las filas contra fuentes verificadas y documenta qué puede acreditarse sin disponer de las bases históricas.

Trabajo local en `fix/repo-consolidation`. No se modifica la suite, el contrato, los modelos, los manifiestos históricos ni los servicios compartidos. Las descargas son únicamente de fuentes públicas originales; una respuesta nueva no se acepta como snapshot histórico sin igualdad exacta de SHA-256 y tamaño.

## Alcance exacto

La ejecución inicial produjo **59 PASS, 15 FAIL y 11 ERROR**. Los primeros errores muestran 13 rutas distintas, pero no enumeran todas las dependencias: las pruebas se detienen en el primer archivo ausente.

El [inventario completo por archivo](insumos_historicos.csv) contiene **210 entradas**: los 191 insumos ausentes del manifiesto, los 12 CSV requeridos por las pruebas relacionales y siete derivados/cachés de Fase 5. Cada fila incluye test, finalidad, procedencia, generador, requisitos, exclusión de Git, hash esperado/actual, estado y ruta exacta de backup necesaria. `first_traceback` distingue los 13 archivos expuestos por la ejecución inicial de las dependencias adicionales descubiertas leyendo las pruebas. Los nombres de tests del CSV son abreviados; pertenecen a `research/datasets/tests/test_phase3.py` o `test_phase5.py`.

- `test_shared_identifiers_integrity_and_unknown_attributes[Madrid/NYC/London]`: `private_results/phase3/<ciudad>/readings.csv`, `channels.csv`, `categories.csv`, `locations.csv` (12 archivos).
- `test_original_madrid_normalization_exact[MAD-AIR/MAD-METEO]`: los dos CSV originales `raw/MAD-*-file.attempt1.bin`, sus Parquet normalizados y sus inventarios `*-META.parquet`.
- `test_epa_utc_identity_and_values_match_raw`: `private_results/NYC-AIR-raw.parquet` y `NYC-AIR.parquet`.
- `test_london_temporal_match_not_household_geography`: `private_results/phase3/London/locations.csv`.
- `test_python_aggregation_separates_units_and_matches_samples`: siete Parquet normalizados: `MAD-AIR`, `MAD-METEO`, `MAD-TRAFFIC`, `NYC-AIR`, `NYC-COUNTS`, `LON-AIR`, `LON-ENERGY`.
- `test_prior_inputs_unchanged_after_phase3`: **191 rutas inicialmente ausentes** del manifiesto `research/datasets/results/phase3/inputs_manifest.csv`, incluyendo originales, prefijos, respuestas HTTP, 20 Parquet y `private_results/lcl_keys.sqlite`. Exige bytes idénticos; una coincidencia de métricas no basta.
- Las 11 instancias con ERROR de Fase 5 dependen de `private_results/phase5/sample.extjson`; las pruebas de referencias y metadatos también requieren `catalogs.json`.
- `test_exact_January_cardinality_in_saved_ledger` (tres instancias): `private_results/phase5/identity_ledger.sqlite`.
- `test_dry_run_no_mutation_and_complete_run_idempotent`: seis originales de Madrid y los cinco archivos de `preparation.json.private_output_hashes`: `sample.extjson`, `catalogs.json`, `sample.csv`, `sample.parquet`, `identity_ledger.sqlite`.

Los cachés `phase5/traffic_selected.parquet` y `traffic_cache_manifest.json` son necesarios para reconstruir, no para la reutilización idempotente ya completada. No deben confundirse archivos faltantes con pruebas faltantes ni con fuentes nuevas.

## Origen y procedimiento original

Todas las rutas de datos indicadas aquí son relativas a `research/datasets/` y deben permanecer **fuera de Git**, bajo `raw/` o `private_results/`.

| Familia | Para qué sirve | Generador existente | Insumo original indispensable |
|---|---|---|---|
| `raw/*` registrados en `02_download_manifest.csv` | Snapshot, respuesta o prefijo exacto auditado; test de inmutabilidad | `download.Downloader.fetch` con URL, límite y Range originales | Fuente pública si sigue devolviendo esos bytes; de lo contrario copia privada exacta |
| `raw/EPA-2023-assembled.zip` | Archivo nacional EPA 2023 completo | Ensamblaje de adquisición de `download.py` | Prefijo y rangos EPA completos, o ZIP idéntico |
| `raw/lcl_members/LCL-June2015v2_{0,1,10,100}.csv` | Miembros completos del prefijo LCL, no archivo ZIP completo | `readers.complete_zip_members` | `raw/LCL-prefix.record27.bin`; CRC, longitud y SHA históricos |
| `private_results/MAD-*.parquet` | Aire/meteo enero+julio, tráfico enero ID%20; inventarios separados | `audit.py madrid`, `audit.py traffic` | CSV anuales, inventarios, ZIP de enero; la etapa madrid también lee energía y accidentes |
| `private_results/NYC-AIR[-raw].parquet` | Lecturas NYC EPA con identidad UTC/POC/método | `audit.py epa` | `raw/EPA-2023-assembled.zip` |
| `private_results/NYC-COUNTS[-raw].parquet`, `NYC-311.parquet` | Campañas DOT y solicitudes 311 históricas | `audit.py nyc` | Páginas JSON DOT/311 y metadatos N01/N03 exactos del manifiesto |
| `private_results/LON-AIR[-META].parquet`, `LON-ENERGY.parquet`, `lcl_keys.sqlite` | Cinco sitios LAQN, energía enero+julio 2013 y deduplicación global | `audit.py london` | L01, diez respuestas LAQN y prefijo LCL exactos |
| `private_results/*integrated.parquet` | Integraciones medidas de Fase 2, no sensores equivalentes | Funciones `integrate.madrid`, `integrate.nyc`, `integrate.london` | Parquet normalizados, inventarios y crudos DOT |
| `private_results/phase3/<ciudad>/*.csv` | Tablas de prueba relacional local y atributos desconocidos | `phase3_validate.prepare_relational` | Los siete Parquet normalizados y tres inventarios aire/meteo/LAQN |
| `private_results/phase5/traffic_selected.parquet`, `traffic_cache_manifest.json` | Nueve campos originales y referencia de fila física | `phase5_prepare.traffic_cache` | ZIP enero 2025 completo y verificado |
| `private_results/phase5/sample.extjson`, `catalogs.json`, `sample.csv`, `sample.parquet`, `identity_ledger.sqlite` | Muestra real acotada, catálogos e identidad exacta enero | `phase5_prepare.py --sample-size 5000` | Seis originales verificados, tres Parquet de inventario y diccionario aire histórico versionado |

## Recuperación sin sobrescribir evidencia

`phase5_prepare.py` detecta el `results/phase5/preparation.json` ya completado y **solo verifica/reutiliza** sus salidas. No basta con ejecutar el comando sobre una copia donde esas salidas faltan.

Para reconstruir se usa `private_results/recovery_workspace/`: copia sin cambios de los scripts, manifiesto original y evidencia necesaria, con enlaces a originales verificados. Dentro de esa copia, el informe previo se conserva como `preparation.historical.json`; se genera un informe nuevo sin tocar el histórico del repositorio. Los resultados solo se copian a sus rutas de trabajo tras comparar hashes y métricas. Los dos SQLite regenerados se conservan como reconstrucciones funcionales con hash distinto, nunca como copias históricas idénticas. No se ejecutan `phase3_run.py`, scripts nativos, PostgreSQL, MongoDB, Spark ni Hadoop.

Comandos de regeneración dentro de ese workspace, con el intérprete del `.venv` raíz:

```text
scripts/audit.py madrid
scripts/audit.py traffic
scripts/audit.py epa
scripts/audit.py nyc
scripts/audit.py london
scripts/phase5_prepare.py --sample-size 5000
```

Las integraciones y `prepare_relational` se llaman únicamente como funciones offline del código existente. Sus salidas documentales se escriben en la copia aislada; no se ejecuta el pipeline completo que requiere PDFs privados y pruebas nativas.

**Excepción de procedencia explícita para el perfilado NYC:** los metadatos públicos N01/N03 actuales no coinciden con los snapshots históricos. Se usan únicamente dentro del workspace para el perfilado que hace `audit.py nyc`; no se aceptan ni copian como originales históricos. Las lecturas se reconstruyen desde las páginas DOT/311 recuperadas con hash exacto. Los ocho Parquet NYC resultantes, incluidos los crudos y las integraciones, coinciden exactamente con sus SHA históricos. Los dos snapshots de metadatos antiguos siguen pendientes.

## Correspondencia comprobada

| Artefactos | Resultado |
|---|---|
| 157 originales/respuestas/miembros bajo `raw/` | SHA-256 y tamaño históricos exactos; adquiridos de las fuentes originales o extraídos con CRC/longitud verificados |
| Los 20 Parquet históricos de Fase 2 | Regenerados; todos con SHA-256 y tamaño históricos exactos |
| `phase5/sample.extjson`, `catalogs.json`, `sample.csv`, `sample.parquet` | Regenerados; los cuatro SHA coinciden con `preparation.json` |
| Caché `phase5/traffic_selected.parquet` | Hash, fingerprint, miembro y conteos coinciden con `preparation.json.cache`; manifiesto de caché también coincide semánticamente |
| 12 CSV requeridos de Fase 3 | Regenerados desde Parquet verificados mediante `prepare_relational`; no existe hash histórico de estos CSV en el manifiesto de inputs |
| `private_results/lcl_keys.sqlite` | Regenerado: integridad SQLite OK y 3.997.252 claves, pero hash binario diferente |
| `phase5/identity_ledger.sqlite` | Regenerado: integridad SQLite OK, conteos y conflictos históricos exactos, pero hash binario diferente |

En el inventario: **182 EXACT_HASH**, **13 PRESENT_NO_HISTORICAL_HASH**, **2 HASH_DIFF**, **13 MISSING**. Los 13 sin hash histórico son los 12 CSV requeridos y el manifiesto del caché. Los dos SQLite requieren todavía copia original para cumplir las verificaciones binarias; no se alteraron los hashes esperados. La causa específica de su diferencia binaria no está acreditada. La investigación usó Python 3.11.16; este entorno usa Python 3.12 con SQLite 3.46.1, y la historia de escrituras del ledger original incluye ejecuciones previas. Estos factores no autorizan aceptar otro hash como el histórico.

Conteos exactos del ledger de enero (`seleccionadas / válidas sin conflicto / conflictos`):

- Aire: **93.720 / 91.959 / 0**.
- Meteo: **69.408 / 66.005 / 0**.
- Tráfico: **677.724 / 674.704 / 0**.
- Muestra: **5.000 documentos**, repartidos **1.000 / 1.000 / 3.000**; total elegible **832.668**. No se cargó en motores.

Hash de la muestra: `5b92b47059c0b1b0740c71d7b94ce10ef794e93f39abf2186f216e01b76c47a3` (exacto).

Para los SQLite:

| Archivo | SHA-256 histórico | SHA-256 regenerado |
|---|---|---|
| `private_results/lcl_keys.sqlite` | `e7d5a25d70aec48a47b5869ec1a93dc57af42cfe0e897a63489bc21fa09cda4f` | `2f984bf5f9d0cb0941ea51354e9e4adb68b80386ce51752b4571849bde1f47e7` |
| `private_results/phase5/identity_ledger.sqlite` | `08037c13deafe41612d7889c7cb1f653a9f0c9c995e4ffaa65031878030bc45d` | `b046a66d8d566cb7f49d05bdf284adbfb3b64a5e3a0b389f0cd8693bf3ce4f6e` |

Los informes locales de adquisición se conservan en `raw/recovery*/`; las comparaciones de regeneración, en `private_results/recovery_regenerated.json`. Son resultados de esta recuperación, no evidencia reescrita de Fase 5.

## Copias exactas pendientes de buscar

No se encontró ni se recuperó manualmente ninguna copia privada durante este trabajo. Hay **15 artefactos pendientes** (13 respuestas históricas cambiadas y dos SQLite no idénticos). Buscar estas rutas en la carpeta original o backups, conservando nombres y bytes:

```text
private_results/lcl_keys.sqlite
private_results/phase5/identity_ledger.sqlite
raw/208627-0-transporte-ptomedida-historico-catalog.record43.bin
raw/212629-0-estaciones-control-aire-catalog.record38.bin
raw/300352-0-meteorologicos-horarios-catalog.record42.bin
raw/300360-0-meteorologicos-estaciones-catalog.record40.bin
raw/L03-refresh.attempt1.bin
raw/L11-refresh.attempt1.bin
raw/M03-refresh.attempt1.bin
raw/M25-refresh.attempt1.bin
raw/N01-refresh.attempt1.bin
raw/N03-refresh.attempt1.bin
raw/N12-refresh.attempt1.bin
raw/NYC-energy-search.record49.bin
raw/NYC-terms.record46.bin
```

Cada hash esperado y tamaño conocido figura en el inventario. No es necesario recuperar manualmente los Parquet ni la muestra: ya son idénticos. Las búsquedas locales acotadas en el workspace y `/tmp/opencode` no encontraron copias; una búsqueda ampliada por nombre en `/home/pablo` excedió el tiempo del buscador y no permite afirmar que se revisaron todos los discos o backups.

## Criterio de recuperación manual

Para las rutas pendientes, buscar la carpeta original `research/datasets/raw/` y `research/datasets/private_results/` de la computadora donde se ejecutaron las fases, o su backup. La evidencia original sitúa los PDFs en `/home/jp/Descargas/`, pero **no acredita la ubicación de un backup del dataset**. No se presupone que esos archivos estén en la computadora actual.

No usar `results/phase5/examples.extjson` como sustituto de `sample.extjson`: contiene ejemplos, no los 5.000 documentos. No recrear respuestas HTTP históricas con contenido inventado, ni actualizar SHA esperados para aceptar respuestas distintas.

Los hashes esperados de los cinco derivados de Fase 5 se conservan en `results/phase5/preparation.json`; los de los 191 insumos históricos están en `results/phase3/inputs_manifest.csv`. Si un Parquet regenerado tiene métricas iguales pero bytes distintos, se necesita el artefacto original para el test de inmutabilidad; no se altera el manifiesto.

## Validación final de esta recuperación

- `python -m pytest research/datasets/tests -q`: **FAIL: 83 PASS, 2 FAIL, 0 ERROR, 0 SKIP**. Fallan `test_prior_inputs_unchanged_after_phase3` (hash de `lcl_keys.sqlite`; además siguen pendientes las 13 respuestas) y `test_dry_run_no_mutation_and_complete_run_idempotent` (hash del ledger de Fase 5).
- `./scripts/validate_repo.sh`: **FAIL**. La etapa documental detecta el hash histórico diferente de `lcl_keys.sqlite` y se detiene antes de pytest. Enlaces internos y topología textual pasan; no se modifican las salidas históricas del validador.
- Los 182 artefactos con hash esperado idéntico también coinciden en tamaño cuando el manifiesto incluye tamaño.
- Ninguna prueba fue adaptada, omitida o convertida en SKIP. No se modificaron scripts históricos ni manifiestos para aceptar las reconstrucciones.
- **Listo para PR: NO**, hasta recuperar los 15 originales pendientes, verificar sus hashes y repetir ambos comandos con `.venv` activado.
