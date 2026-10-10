# Fase 2 — Reproducción

Directorio de trabajo: `research/datasets/` del repositorio SmartCity. Fases 00/01 no modificadas; conservarlas porque los scripts reutilizan las URLs de `01_http_evidence.csv`. No seguir las instrucciones de infraestructura del README raíz para esta auditoría. Ningún script conecta a PostgreSQL/MongoDB/Coolify/Tailscale.

## Entorno

Sistema Python 3.12.3 sin pandas/NumPy/PyArrow/pyproj/pytest al comenzar. Entorno aislado Python 3.11.16 creado por uv. Paquetes principales en `scripts/requirements.txt`; versiones resueltas en `results/environment.json` y `scripts/requirements.lock`. Para reproducir con Python 3.11:

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r scripts/requirements.lock
```

Entorno/descargas/derivados ignorados por `.gitignore` local. No subir `raw/`, `private_results/`, `.venv/` ni SQLite. No se modifican fuentes; las transformaciones quedan separadas.

## Ejecución offline con archivos locales

```bash
.venv/bin/python scripts/verify.py
.venv/bin/python scripts/audit.py all
.venv/bin/python scripts/integrate.py
.venv/bin/python -m pytest tests -q --basetemp=/tmp/opencode/smartcity-phase2-tests --junitxml=results/tests.xml
.venv/bin/python scripts/build_reports.py
```

`audit.py` admite `madrid`, `traffic`, `epa`, `nyc`, `london`, `complements`, `all`; no accede a red. Muestras definidas en código: Madrid enero/julio 2025, tráfico ID%20=0 en enero 2025; NYC DOT 2023 completo/311 en 16 días; LAQN cinco sitios × dos meses; LCL miembros iniciales completos con CRC y selección enero/julio 2013. No hay muestras sintéticas ni parámetros escondidos. `quality.py` y `readers.py` son reutilizables; `integrate.py` guarda reglas, denominadores y correspondencias faltantes. También puede ejecutarse todo con `.venv/bin/python scripts/run_offline.py`, que conserva `results/offline_run.log`.

Controles de memoria: CSV por chunks de 100k filas; EPA filtra localmente en stream antes de acumular, sin materializar su CSV nacional de 2,6 GB; tráfico conserva solo el estrato de ID; LCL acumula dos meses y cuenta claves exactas en SQLite en disco (cache 8 MiB). Miembros ZIP limitados a 70 MB descomprimidos, validación de paths/CRC/longitud antes de procesar. Pico medido en la última ejecución completa: 948 904 KiB; reservar aproximadamente 1,5–2 GB para reproducir. No se promete operar en 512 MB ni se acredita rendimiento remoto.

Estadísticos originales en `*-schema_quality.json`; tipos declarados provienen de Socrata cuando hay metadatos, o quedan pendientes/descripción básica de estructura. Estadística física normalizada por variable/unidad en `*-summary.json`. Estadísticas numéricas sobre IDs/códigos son diagnósticos de formato, no interpretación física. Rangos/unidades que requieren validación adicional se indican en los bloqueos.

## Adquisición en entorno limpio o actualización autorizada

Estas órdenes realizan red pública y **consumen el presupuesto**. Ejecutar **secuencialmente**: no correr varios downloaders concurrentes sobre un mismo manifiesto, pues el control de presupuesto/append no tiene lock entre procesos.

```bash
.venv/bin/python scripts/download.py initial --budget 1000000000
.venv/bin/python scripts/download.py official --budget 1000000000
.venv/bin/python scripts/download.py nyc --budget 1000000000
.venv/bin/python scripts/download.py madrid-traffic --budget 1000000000
.venv/bin/python scripts/download.py epa --budget 1000000000
.venv/bin/python scripts/download.py complements --budget 1000000000
```

En una reproducción nueva, EPA se ensambla desde cero por rangos de 1 MiB. Esta corrida reutilizó 11 862 016 bytes de una descarga interrumpida, registrados en manifiesto. Comprobar inicio/fin/total de `Content-Range` antes de ensamblar. SHA del archivo completo en `results/epa_assembly.json` y `02_artifact_manifest.csv`. Si cambian rango/ETag/tamaño, revalidar versión; CRC detecta inconsistencias, no asumir continuidad entre versiones.

Timeout conexión 15 s/lectura 90 s, hasta dos intentos solo en fallos transitorios/429/5xx, backoff 2 s/Retry-After hasta 120 s; 403/401/404 sin reintentos ni evasión. Paginación secuencial, pausa de un segundo y orden explícito SODA, límites 10k DOT/5k 311. No hay snapshot transaccional entre páginas de tablas vivas: guardar fecha/versión/hash y verificar duplicados. `$offset` puede desplazarse si cambia la tabla durante la adquisición.

Límite acumulado de 1 GB persistido en `02_download_manifest.csv`, incluyendo intentos fallidos/prefijos. Si se ignora Range, el stream se cierra al alcanzar el cap; `complete_response` significa respuesta completa, no «dataset válido». `BudgetExceeded` detiene red; el script rechaza presupuesto superior a 1 GB. Aumentarlo requiere autorización expresa y cambio posterior. Logs en `results/download.log`. Reutilización exige archivo/SHA coincidente; cada nuevo intento tiene un path distinto, no sobrescribe las fuentes.

## Validación de evidencia

`verify.py` comprueba tamaño/SHA de cada respuesta contabilizada, presupuesto, hashes de 00/01 y artefactos locales. Resultado: **22 pruebas, 0 fallos, 0 errores**, evidencia JUnit. Los pequeños fixtures/mocks de las pruebas **no son datos sintéticos para aumentar datasets**. Se prueban 403 sin retry, 503 con backoff, presupuesto persistido, Range ignorado, ZIP truncado/CRC/path seguro, H24, ceros/nulos, duplicados/gaps, conflictos de valor y prevención de joins cartesianos. Cinco pruebas adicionales comprueban los resultados guardados de fuentes reales.

`build_reports.py` regenera reportes desde resultados locales; no invoca scraping ni servicios remotos. Los tres manifiestos/métricas CSV son UTF-8 con cabecera. Si se amplían muestras, volver a ejecutar auditoría/integración/reportes antes de presentar un diagnóstico actualizado.

## Proveniencia/licencias

Referenciar organismo/recurso/fecha/hash del manifiesto. Licencias: Madrid CC BY 4.0 (M25), UKPN CC BY 4.0 (L03), LAQN uso educativo restringido (L11), EPA descripción/disclaimer y términos NYC descargados. Revisar permisos vigentes antes de publicar. No se descargaron direcciones/narrativas 311; lecturas LAQN e integraciones permanecen locales e ignoradas por Git.

No instalar servicios, generar esquemas finales SQL/MongoDB, seleccionar ganador ni realizar commit/push/merge. **Fase 2 cerrada; Fase 3 pendiente de autorización.**
