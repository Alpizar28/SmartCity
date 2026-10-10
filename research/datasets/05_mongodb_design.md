# Fase 5 — Modelo MongoDB preliminar para Kembly

## Colecciones propuestas

| Colección | Granularidad / referencias | Estado |
|---|---|---|
| readings |Hora real ambiental o intervalo multivariable de tráfico; _id=measurement_id, channel/station/zone/source_version compartidos |Muestra5k nativa local; estándar |
| derived_events |Evento por regla/version/inputs, observed_at y derived_at |Sin generar; umbral/unidad/duración/QA/severidad pendientes |
| alerts |Emisión demostrada por event_id y zone_id, emitted_at real |Sin mensajes; histórico/replay requieren fuente o aprobación |
| incidents_2026 |Un expediente de accidente2026; categoría NULL visible; personas/detalles fuera |Complemento separado; no probado nativamente en enero |
| energy_reports_monthly |Medidor/nivel/unidad/mes real |Complemento separado; no energía horaria |
| dynamic_metadata |Payload semiestructurado/versionado con raw_reference |Especificación; no metadatos ficticios |
| crud_demo |Tres fixtures de operación sin mediciones |Solo DB desechable; synthetic y no cuentan para500k |

**Tráfico:**677724 registros del estrato,674704 elegibles y únicos,3020 flag desconocido;0duplicados/conflictos por clave completa y payload. Examen incluye id/fecha/tipo_elem/intensidad/duración, no solo el resumen anterior. URB611153, M3048797, C3017774 en registros seleccionados; todas las clases legítimas conservadas. `vmed=0` URB no se presenta como velocidad medida; raw0 se conserva y el valor opcional analítico queda NULL. Opcionales ausentes no invalidan intensidad/duración válidas. La semántica temporal y geografía histórica aún necesitan cierre.

## Documento y tipos

Ejemplo **real** de cada fuente, con procedencia, en `results/phase5/examples.extjson`; los5000 originales de muestra y catálogos completos están ignorados en private_results/phase5. `{"_id": "measurement:<hash>", "sensor_id": null, "channel_id": "channel:<hash>", "station_id": "station:<hash>", "zone_id": null, "observed_at": {"$date": "2025-01-01T00:00:00Z"}, "measurement_type": "MAD-AIR:8", "value": "valor real del ejemplo adjunto", "unit": "ug/m3", "data_origin": "observed"}` es estructura ilustrativa, no otra lectura generada.

BSON Date para observed_at, double/int para value, NULL para sensor/unidad/zona desconocidos, objetos anidados de measurements y raw_reference. $jsonSchema estricto valida campos requeridos, tipos y enum de origen en la prueba; no afirma una FK remota. Usar catálogos versionados e integridad previa al lote. Desnormalizar en Mongo para consultas evita joins repetidos; misma regla de IDs y mismas unidades que SQL.

## Índices y estándar frente a time-series

Estándar elegida para Sprint1: _id único y UNIQUE(channel_id,observed_at,timestamp_role); índices channel+time, source+type+time y zone+type+time. EXPLAIN natural y con hint de demostración guardados; no confundir hint con elección automática del optimizador. No 2dsphere sin CRS confirmado. No TTL sobre evidencia histórica.

Time-series sería candidata futura con timeField=observed_at, metaField={source_id,channel_id,measurement_type,unit}, granularity según frecuencia. Reduce almacenamiento/buckets y facilita análisis temporal, pero **no admite índice UNIQUE como colección estándar**; deduplicación requiere registry externo/ETL. Restricciones de update/delete dependen de versión (7.0 frente a8.x): no prometer CRUD arbitrario sobre valores ni trasladar validator/índices sin comprobar documentación. Mantener events/alerts/incidents/crud_demo estándar. La prueba ejecutada no usa time-series ni acredita esos beneficios.

## Consultas y alcance

Diseños nativos locales ejecutados: MG01 canal, MG02 rango UTC, MG03 extremos separados por variable/unidad, MG06 distritos publicados de tráfico, MG07 tipo/variable con unidad conocida, MG09 Aggregation Framework y MG10 filtros múltiples. Siete diseños, **no siete requisitos físicos plenamente aprobados**. MG01/07 necesitan aceptar canal/variable; MG06 excluye zonaNULL y tiene geografía histórica pendiente; meteo sin unidad no se promedia como grados.

MG04 bloqueada por política de críticos; MG05 por emisión/zonas no acreditadas; MG08 tiene expedientes2026 auditados, pero permanece fuera de esta muestra2025 y requiere ingestión separada/prueba propia. No contar colecciones vacías como evidencia. CRUD update/delete solo crud_demo; lecturas originales intactas. Reimportación misma muestra no añade documentos; misma PK/payload distinto debe bloquearse, no ocultarse con timestamp de ingestión en la identidad.

Limitación: no500k cargados, cluster/sharding/producción ni comparación de versiones. La muestra solo demuestra mecánica y coherencia local.
