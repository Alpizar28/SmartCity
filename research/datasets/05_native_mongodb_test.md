# Fase 5 — Prueba nativa MongoDB local

**Ejecución nativa: True**. Versión:7.0.43; imagen `mongo:7.0`; digest `mongo@sha256:1f995ad6fdb93244a1addab1b58f934a0bc2f5643c38e02f5e9d7f0c7d227a7b`. No se sustituyó MongoDB por Python: mongosh envió operaciones a mongod dentro de un contenedor desechable, DB `smartcity_phase5_b2fb4abd374c`.

## Entrada, aislamiento y prueba

5000 documentos reales ({'MAD-AIR': 1000, 'MAD-METEO': 1000, 'MAD-TRAFFIC': 3000}), con SHA `5b92b47059c0b1b0740c71d7b94ce10ef794e93f39abf2186f216e01b76c47a3`. Muestra por cuotas de primeras observaciones válidas en el orden del snapshot, reproducible pero **no representativa de toda la ciudad ni benchmark de500k**. Catálogos compartidos:462 canales/5134 sitios; memberships y relaciones coinciden con los catálogos SQL locales. sensor_id NULL; ninguna identidad física fabricada.

Socket local fijo, red none, sin puertos publicados, localhost127.0.0.1 dentro del contenedor, inputs readonly, límite1GiB/1CPU. No conexión con MongoDB remoto, Coolify ni Tailscale. Contenedor eliminado:True; sus volúmenes anónimos eliminados:True. Las imágenes descargadas permanecen como cache local Docker, no son servicios ni datos de producción.

Mongo8.0 abortó al arrancar por incompatibilidad declarada con kernels Linux6.19+ (SERVER-121912). Se conserva `mongodb8_startup_failure.json`/`mongodb8_server.log`; no se desactivaron controles ni se cambió kernel. Se eligió7.0 para prueba, compatible con rama mayor del Compose estático; patch/digest local distintos de7.0.16 deben validarse antes de reproducir en otra versión. Las fases anteriores quedan como evidencia histórica de0nativas, no se reescribieron.

## Operaciones y resultados

MG01 canal, MG02 rango UTC, MG03 extremos, MG06 zonas tráfico, MG07 variables/unidades, MG09 Aggregation Framework ($match→$group→$sort) y MG10 filtros múltiples. Conteos/extremos/sumas comprobados contra referencia independiente y muestra fuente. MG06/07 excluyen unidad/zonaNULL según regla; su alcance no sustituye requisitos físicos/zonas completas. MG04/05 no ejecutadas (regla/emisión), MG08 no ejecutada (accidentes2026 fuera de muestra2025).

Validator BSON rechazó string donde se exige Date; PK/índice único rechazaron duplicado. Índices compuestos creados; explain('executionStats') natural y con hint guardados completos, sin prometer rendimiento remoto ni que un hint sea selección automática. Plan ganador natural: `{"stage": "FETCH", "inputStage": {"stage": "IXSCAN", "keyPattern": {"channel_id": 1, "observed_at": 1}, "indexName": "channel_time", "isMultiKey": false, "multiKeyPaths": {"channel_id": [], "observed_at": []}, "isUnique": false, "isSparse": false, "isPartial": false, "indexVersion": 2, "direction": "forward", "indexBounds": {"channel_id": ["[\"channel:ab914056374bd60014a9dc19dfcd21e65656f3046e1c891b7c5868414aa14dc2\", \"channel:ab914056374bd60014a9dc19dfcd21e65656f3046e1c891b7c5868414aa14dc2\"]"], "observed_at": ["[new Date(1735686000000), new Date(1738368000000))"]}}}`.

Reimportación idéntica:{'upserted': 0, 'count': 5000}. CRUD insertOne/Many,find/findOne,updateOne/Many,deleteOne en crud_demo; tres fixtures synthetic no métricos separados,0observaciones originales mutadas. Siete diseños locales ejecutados, **no declaración7/10académicas estrictas ni500kdocumentos cargados**.

| Operación local | Milisegundos medidos |
|---|---|
| insert_batches | 479.419 |
| create_indexes | 149.66 |
| MG01 | 37.046 |
| MG02 | 7.523 |
| MG03_MG09 | 18.286 |
| MG06_MG07 | 29.864 |
| MG10 | 14.767 |

Tiempos de una única corrida local, incluyen estado/cache y no tienen intervalo estadístico. Logs/JSON: `mongodb_execution.json`, `mongodb_execution.log`, `mongodb_server.log`, `sample_reference.json`; reproducción en `05_ingestion_plan.md`. Si no existe imagen/daemon compatible, el script falla y no presenta native_executed=true.
