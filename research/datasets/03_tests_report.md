# Fase 3 — Pruebas y reproducción

**42 pruebas aprobadas:22 heredadas y 20 nuevas;0 fallos/errores/omisiones.** JUnit separados en `results/phase3/legacy_tests.xml` y `tests.xml`; no se sobrescribió la evidencia de Fase 2.

## Comandos

Desde `research/datasets/`, con el entorno Python 3.11.16 y `scripts/requirements.lock` existente; paquetes nuevos instalados:ninguno.

```bash
.venv/bin/python scripts/phase3_run.py
```

Ejecuta secuencialmente:

```bash
.venv/bin/python scripts/phase3_validate.py
.venv/bin/python scripts/phase3_enrich.py
.venv/bin/python scripts/phase3_postgres.py
.venv/bin/python -m pytest tests/test_audit.py tests/test_saved_evidence.py -q --basetemp=/tmp/opencode/smartcity-phase3-legacy --junitxml=results/phase3/legacy_tests.xml
.venv/bin/python -m pytest tests/test_phase3.py -q --basetemp=/tmp/opencode/smartcity-phase3-tests --junitxml=results/phase3/tests.xml
.venv/bin/python scripts/phase3_reports.py
.venv/bin/python scripts/phase3_finalize.py
```

No usar `run_offline.py` para esta fase: regenera los entregables 02. Phase 3 no modifica esos archivos. Datos/muestras deben existir localmente; no hay nuevas descargas. Enunciado original extraído conpdftotext ySHA en `academic_evidence.json`.

## Aislamiento y ejecución nativa

Versión:PostgreSQL 16.15 on x 86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit. Imagen PostgreSQL 16 ya disponible; Docker forzado a socket LOCAL`unix:///var/run/docker.sock`, `--network none`, sin puertos, `--pull never`, memoria 1 GB/CPU 1. Bind read-only exclusivamente para CSVprivados de prueba. Volumen anónimo nuevo, descartado con contenedor. Contenedor eliminado:True; volúmenes eliminados:True. No Compose, Coolify, Tailscale o bases existentes.

Dos intentos iniciales fallaron: uno conpsql durante arranque y otro por agotamiento deltmpfs 512 MiB duranteCOPY. Se endureció readiness para esperar final deinitdb y se cambió a volumen anónimo desechable. No se reportan esos intentos como exitosos ni se promete operar en 512 MB. Ejecuciones finales completas con códigos 0 en `run.log`; SQL/results/planes en `postgres_execution.*`.

## Registro de verificaciones

| Grupo | Evidencia y resultado | Límite |
|---|---|---|
| Legado 22 | Budget/retry/403/503/ZIPCRC/path/H24/nulos/DST/joins y assertions de métricas reales | No probaba todas las consultas académicas |
| Nuevas 20 | Tres pruebas de ejecución nativa, tres de IDs/FK/datos ausentes, dos de normalización Madrid, EPA UTC/valor, DOT claves, coberturas Madrid/NYC/Londres, LCL global, incidentes/nulos, unidades, tres agregaciones e inmutabilidad | Datos/semántica aún parciales, no proyectos completos |
| SQL |30 diseños, referencias Python, conteos/sumas/min/max, vista, función y CTE/DENSE_RANK | PG03/06 diagnósticosNULL; PG07 catálogo derivado no inventario completo |
| Restricciones |9 rechazos reales (PKduplicada, FKhuérfana, timestampNULL por ciudad) | Fixtures mínimos en transacciones fallidas, ninguna medición ficticia persistida |
| Raw |CSV aire/meteo, ZIP tráfico leído completo conCRC, originales EPA local, DOT/311 y 4 Menergía | Raw filas no equivalen a observaciones únicas |
| LCL |3.997.252 claves,2748 extras,0 conflictos de valor globales, porSQLite en disco | Cuatro miembrosCRC completos, no ZIP entero ni 5567 hogares |
| Incidentes |14.388 expedientesMadrid;14.386 categorías conocidas y 2 NULL, sin conflictos |33.322 detalles no son 33.322 accidentes;311 solicitud no confirmado |
| Unidades/reloj |Unidadesaire contra diccionario; H24 yEPA UTC exactos |Meteo/unidad ytimezoneLCL quedan pendientes |
| Inmutabilidad |Hashes/tamaños de documentación previa, scripts, pruebas, métricas, logs, manifiestos y cuerpos/derivados anteriores |DatosPhase 3 regenerables, originales intactos |

`inputs_manifest.csv` conserva fingerprints; `validation.json`, `dot_conflicts.json`, `catalog_activity.csv`, `incident_checks.json`, `unit_history_checks.json`, referenciasSQL y agrupacionesPython detallan resultados. `phase3_finalize.py` valida entregables, sintaxis, matrices y hashes previos; guarda `final_checks.json` y `outputs_manifest.csv` (excluye el log activo del runner). Raw/derivados privados ignorados porGit.

MongoDB no disponible: filtros y agrupaciones Python +diseñosJS, sin CRUD/BSON/índices/Aggregation Framework nativo. Hadoop/Spark/dashboard no ejecutados. Las pruebas sobre formas/protocolo del legado no se usan para aumentar volumen. **30 SQLejecutados no equivalen a 30 requisitos cumplidos.**
