# Pipeline acotado y reproducción segura

## Alcance ejecutado

Originales inmutables → validación → normalización → identificadores → catálogos → muestras PostgreSQL/MongoDB → exportación posterior CSV/Parquet.

Los [diagramas](diagramas.md) y [plan de Fase 5](../../research/datasets/05_ingestion_plan.md) distinguen implementación local de especificación futura. La preparación valida toda la selección de enero en un ledger local, pero exporta **1.000–10.000 documentos** como máximo; la corrida acreditada usa 5.000. No hay ingestión completa en motores compartidos ni Hadoop, Spark o Streamlit.

## 1. Entorno e insumos

Directorio de trabajo para comandos de investigación: `research/datasets/`. Entorno acreditado: Python 3.11.16; paquetes fijados en [requirements.lock](../../research/datasets/scripts/requirements.lock), versiones registradas en [environment.json](../../research/datasets/results/environment.json). Los scripts usan rutas relativas al archivo, no al host remoto.

En un clon limpio, la instalación explícita puede hacerse con `uv`:

```bash
cd research/datasets
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r scripts/requirements.lock
```

Estas órdenes pueden descargar intérprete/dependencias; **no se ejecutaron en Fase 6** y requieren acceso autorizado. No recrear el entorno existente sin necesidad. No son descargas del dataset.

Un clon no contiene `raw/`, `private_results/`, `.venv/`, los PDF E/P/I ni transcripciones completas restringidas. Por tanto:

- El validador documental funciona sin datos privados (y sin lanzar Docker).
- Las pruebas completas de evidencia requieren los snapshots y salidas privadas exactas: pedirlos a José por canal autorizado y comparar manifiestos/SHA. No cambiar assertions para aparentar éxito sin insumos.
- `phase5_prepare.py --dry-run` requiere los seis snapshots locales del manifiesto.
- La preparación real también reutiliza evidencia anterior y escribe cache, ledger y muestra. El verificador de Fase 5 exige originales PDF en las rutas registradas y resultados previos: no se promete portabilidad automática de esas rutas.
- Las pruebas nativas requieren la muestra/catálogos, referencia guardada, Docker local y las imágenes ya disponibles.

Las instrucciones de adquisición en [02_reproduction.md](../../research/datasets/02_reproduction.md) son históricas y tienen presupuesto. **No ejecutar descarga o actualización automática para validar esta documentación.** Una nueva versión de URL viva no reproduce necesariamente el snapshot anterior.

## 2. Validación sin modificar fases históricas

Desde la raíz del repositorio:

```bash
mkdir -p /tmp/opencode
cd research/datasets
.venv/bin/python scripts/phase5_prepare.py --dry-run
TMPDIR=/tmp/opencode .venv/bin/python -m pytest tests -q --junitxml=results/phase6/tests.xml
.venv/bin/python scripts/phase6_validate_docs.py
```

El `dry-run` verifica hashes y muestra el plan sin extraer, escribir ni conectar motores. Pytest lee datos/evidencia local y usa temporales exclusivos asignados automáticamente; no vuelve a cargar las bases ni arranca contenedores. No reutilizar un `--basetemp` con archivos propios: pytest limpia su contenido al iniciar. El JUnit nuevo se guarda en `results/phase6/`, **no sobrescribe `results/phase5/tests.xml`**. El validador documental usa biblioteca estándar; también puede ejecutarse desde la raíz con `python3 research/datasets/scripts/phase6_validate_docs.py`.

No ejecutar `run_offline.py`, `phase3_run.py` ni generadores de reportes para validar la nueva documentación: regeneran entregables históricos. Los verificadores antiguos también pueden escribir preflight/sellos; en Fase 6 se comprueban sus manifiestos sin regenerarlos.

## 3. Replay y prueba nativa opcionales, fuera de la validación documental

**Solo en una copia de trabajo autorizada con insumos locales**, para no sobrescribir evidencia histórica. Estos comandos ya existen y no son implementación definitiva:

```bash
# Desde research/datasets/ de la copia de reproducción
.venv/bin/python scripts/phase5_prepare.py --sample-size 5000
.venv/bin/python scripts/phase5_postgres_sample.py
.venv/bin/python scripts/phase5_native.py --engine mongodb
```

La preparación reutiliza outputs solo si configuración, scripts, contrato y hashes coinciden; si cambian, aborta y exige versión/directorio revisado. No modificar a 500.000 como forma de eludir el límite.

Los runners usan `docker --host unix:///var/run/docker.sock`, `--network none`, sin puertos, `--pull=never`, nombres aleatorios, inputs readonly y recursos temporales propios. Requieren imágenes `postgres:16-alpine` y `mongo:7.0` locales; **no descargan imágenes automáticamente** ni leen `.env`/DSN remoto/DOCKER_HOST para apuntar a bases compartidas. Las referencias históricas son PostgreSQL 16.15 y MongoDB 7.0.43; registrar digest y patch al reproducir, porque los tags menores pueden cambiar. No iniciar el Compose raíz para estas pruebas. Revisar límite local de 1 GiB/1 CPU y limpieza `container_removed`/`anonymous_volumes_removed`.

MongoDB 8.0 no se debe repetir como primera alternativa en este host: [startup_failure.json](../../research/datasets/results/phase5/mongodb8_startup_failure.json) documenta incompatibilidad con kernel Linux 6.19+. No cambiar el kernel ni pins de Compose para esta fase.

## 4. Controles reales del pipeline

| Control | Implementación limitada | Límite / siguiente trabajo |
|---|---|---|
| Procedencia | SHA de inputs, localizador raw, versión de contrato/catálogo | Registrar actualización autorizada y política de correcciones |
| Cache/atomicidad | Fingerprint, CRC al EOF, archivo temporal y `os.replace` | Cache parcial no aceptada; no checkpoint distribuido |
| Exclusión mutua | `flock` del writer | No ejecutar preparaciones concurrentes sobre misma salida |
| Lotes | Extracción CSV por chunks; commits de ledger; `insertMany` acotado | Carga completa por motor necesita extensión autorizada |
| Idempotencia | IDs naturales, payload hash y verificación de outputs; reimportación idéntica sin extras | No upsert destructivo de correcciones |
| Reanudación | Reuso de cache completa o reconstrucción determinista del ledger | Reprocesar validación puede costar tiempo; no saltar offset sin verificar |
| Errores | Hash/clock/catálogo fatal; flags inválidos contados, conflicto excluido | Reportar rechazos; no convertirlos en éxito silencioso |
| Integridad | Catálogo previo, FK/trigger SQL, tipos BSON y comparación de referencia | Sin FK/transacción automática SQL–MongoDB |
| Cleanup | `finally` en pruebas nativas y verificación de recursos propios | No remover volúmenes existentes ni usar `compose down -v` |

Código: [contrato](../../research/datasets/scripts/phase5_contract.py), [preparación](../../research/datasets/scripts/phase5_prepare.py), [runner PostgreSQL](../../research/datasets/scripts/phase5_postgres_sample.py), [runner MongoDB](../../research/datasets/scripts/phase5_native.py).

## 5. Exportación y etapas posteriores

Existen CSV/Parquet/Extended JSON privados de la muestra con IDs, UTC y procedencia; no son tres poblaciones distintas. Una exportación completa posterior puede particionarse por fuente/año/mes y manifiesto, manteniendo QA y claves. El calendario de partición debe explicitar fecha fuente frente a UTC y H24.

Pendientes, no ejecutados: exportador completo; manifests de lote durables por motor; estados pending/SQL_committed/Mongo_committed/reconciled y recuperación de escrituras parciales; staging, backup/restore y recursos; ingestión HDFS; Spark distribuido ≥1 millón con DST/QA/cardinalidad anual; dashboard. No usar una exportación Parquet local como evidencia de procesamiento distribuido.
