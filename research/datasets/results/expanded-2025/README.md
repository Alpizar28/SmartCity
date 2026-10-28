# Evidencia de la ampliación real de aire, 2025

Esta generación **no se suma** a enero ni a las muestras previas. Contiene el mismo enero, más febrero–diciembre del mismo snapshot oficial. No hay mediciones inventadas, copiadas o alteradas.

**Cierre verificado:** PostgreSQL y MongoDB terminaron la carga y reimportación de **1.076.813 registros cada uno**, con comparación completa de valores/metadatos, misma huella de IDs/payloads y limpieza de recursos. `verification.json` contiene `verified=true`. Tiempos totales: 1.105,65 s PostgreSQL y 644,91 s MongoDB. [Informe de cierre histórico](https://github.com/Alpizar28/SmartCity/blob/5eb3db7/docs/equipo/CIERRE_VALIDACION_SPRINT1.md).

| Magnitud | Cantidad |
|---|---:|
| Slots seleccionados | 1.103.232 |
| Observaciones aceptadas | **1.076.813** |
| Aceptadas adicionales respecto de enero | 984.854 |
| Cuarentena de aire | 26.419 |
| Flags no válidos | 26.167 |
| Hora local inexistente | 126 |
| Hora local ambigua sin evidencia | 126 |
| Duplicados | 0 |
| Conflictos del conjunto original | 0 |
| Mediciones sintéticas | 0 |
| Archivos de mediciones nuevos descargados | 0: el CSV auditado ya contiene todo 2025 |

## Archivos y afirmaciones verificables

- `preparation.json`: conteos por mes y variable, hashes de código/archivos privados, snapshots y tiempo del ETL (154,87 s en esta máquina).
- `audit.json`: confirma que las 91.959 observaciones aceptadas de enero conservan IDs y hashes dentro del año; contabiliza tamaños y cuarentena sin duplicar generaciones.
- `research_sources.json`: siete recursos oficiales consultados, sus URLs, fechas, hashes y tamaños; PDF/HTML completos conservados fuera de Git.
- `traffic_v2_assessment.json`: dimensionamiento de solo lectura de la revisión propuesta, con 656.930 candidatas URB/M30 de enero; **cero añadidas** a aceptados. Propuesta pendiente: [madrid-draft-v2](../../../../docs/decisiones/PROPUESTA_MADRID_DRAFT_V2.md).
- `tests.xml`: ejecución actual de 134 pruebas Python, incluidas pruebas de DST, límite mensual, reimportación, duplicados, interrupción, conflictos y rechazo de evidencia incompleta.
- `postgresql_full.json` y `mongodb_full.json`: evidencia de ejecución completa de cada motor. Consultar `native_executed`, `count`, `metadata_verified`, `ledger_reconciled`, errores y limpieza; **la existencia de un archivo no prueba que la ejecución haya terminado bien**.
- `verification.json`, cuando exista: salida de `unified_full_verify.py`, que exige ambos motores completos y mismos IDs/payloads que el ledger anual.

Los documentos oficiales confirman una corrección contractual pendiente en tráfico: `periodo_integracion` cuenta muestras, no minutos. Tráfico no se habilita mediante cambio de etiqueta; meteorología sigue sin reloj acreditado. Las observaciones aceptadas actuales pertenecen a **una sola fuente**, `MAD-AIR`.

Volúmenes medidos: aceptados JSONL **1.567,85 MB / 1,568 GB**; derivados anuales **2,175 GB**, de los cuales el ledger SQLite ocupa 577,55 MB. No representan registros adicionales. Los datasets completos, catálogos voluminosos, ledger y cuarentena están ignorados por Git en `private_results/expanded-2025/`.

La segunda ejecución de preparación devolvió `idempotent_reuse=true`, 1.076.813 aceptadas, verificando hashes sin reescribir el lote. Las pruebas pequeñas inyectan interrupciones y reconstruyen solo derivados propios sin sellar, con fingerprint idéntico.

Spark/Hadoop **no se implementaron ni ejecutaron**. Tener más de un millón de entradas disponibles no acredita procesamiento Spark. No hay despliegue compartido ni equivalencia entre canales y sensores físicos. Las 14 entidades administrativas de demo anteriores permanecen fuera de estos conteos y de las cargas anuales.

Reproducción y entrega a Daniel, Kembly y Fernanda: [AMPLIACION_REAL_SPRINT1.md](https://github.com/Alpizar28/SmartCity/blob/9d84a34e529a72b316c540bff549080c906b0126/docs/equipo/AMPLIACION_REAL_SPRINT1.md).
