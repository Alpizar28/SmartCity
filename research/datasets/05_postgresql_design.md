# Fase 5 — Modelo PostgreSQL preliminar para Daniel

DDL: `scripts/phase5_postgresql.sql`; consultas: `phase5_postgresql_queries.sql`. **No migración definitiva**. Esquema local draft5,12 tablas (más vistas/funciones), revisable y con vacíos visibles.

## Relaciones, normalización y tipos

- sources1:N source_versions; fuente/versión con SHA y path, publicador no propietario.
- zones1:N locations; locations1:N stations (en muestra1:1), estaciones de redes independientes.
- sensor_categories1:N measurement_types; cada tipo define fuente, unidad acreditada/candidata y estado.
- stations1:N sensors físicos acreditados y1:N channels; sensors0..1:N channels. Sin evidencia, sensor_id NULL, tabla sensors vacía.
- organizations1:N sensors, solo vínculo acreditado; usuarios de aplicación independientes con correo UNIQUE y consentimiento, tabla users vacía.
- channels1:N observations; observations N:1 source_versions. PK y UNIQUE natural independientes del payload; hechos structured sin inventar maestros.

3FN: identidad de fuente, zona, estación, categoría, unidad/tipo, dispositivo y canal se guarda una vez en su catálogo; observations no repite station_id,zone_id,unit,measurement_type ni source_id, pues canal/snapshot los determinan. La vista observation_contract reconstruye DTO. original_time/reloj, QA, duración, procedencia y valor dependen de la observación. measurements JSONB es payload semiestructurado opcional de ese intervalo, no copias de hechos para inflar volumen. Historial de geografía/organismos requiere tablas de vigencia posteriores antes de reportar enero como validado; no afirmar3FN elimina ese vacío histórico.

PK/FK para todas las referencias; UNIQUE(station_id,source_key), UNIQUE(channel_id,observed_at,timestamp_role), CHECK de origen, fecha/reloj, rango de coordenadas, duración y valor finito. Trigger rechaza fuente de snapshot distinta de estación/canal/tipo. Sensores exigen identity_evidence_reference para poblarse. Instalación/estado/vínculo organismo permiten NULL; usuarios no se crean sin consentimiento. Correo de víctima no es usuario del sistema.

Índices B-tree de PK/UNIQUE, sensor estación/categoría/organismo, canal estación y tiempo observación. El UNIQUE natural ya cubre canal+fecha; evitar duplicarlo sin EXPLAIN. Particiones mensuales y BRIN temporal si benchmark justifica; no implementadas. Particionar requeriría revisar PK global (incluir clave partición o registry de IDs) y cargas tardías. Materialized view diaria por tipo/unidad/zona, refresh y benchmark siguen propuestos, no acreditados.

## Compatibilidad con las diez consultas

| ID | Viabilidad exacta / cierre requerido |
|---|---|
| PG01 |SQL por tipo sobre sensores vacíos no cumple inventario; alternativa por canal revisable por profesor |
| PG02 |Ubicación de sitios disponible parcial; dispositivo físico y vigencia pendientes; canal→sitio explícito |
| PG03 |Bloqueada estricta: sin estado administrativo; actividad en ventana no sustituto silencioso |
| PG04 |Bloqueada estricta: sin vínculo individual completo ni responsable acreditado; publisher separado |
| PG05 |Ranking de canales por ubicación viable condicionado; no conteo de lecturas como sensores |
| PG06 |Bloqueada estricta: no fecha instalación; alta de sitio/primera lectura separadas |
| PG07 |NOT EXISTS diseñado; inventario independiente de sitios existe, pero no inventario físico ni completo de canales históricos; ausencia ≠ falla |
| PG08 |CTE/DENSE_RANK diseñado; zonas tráfico parciales y geografía ambiental desconocida; aceptar alcance muestreado |
| PG09 |Vista nativa local ejecutada; contrato físico completo no acreditado |
| PG10 |Función nativa local ejecutada y rotulada canales, no sensores inventados |

Se mantienen las2/10 estrictas y6/10 funcionales condicionadas de Fase3 como evidencia histórica; no prometer10/10 por escribir diez SQL sobre tablas vacías. Nuevos diseños no son automáticamente aprobación académica.

## Ingestión y muestra local

Staging por snapshot/lote; validar y conservar rechazos; transacción de catálogos+hechos por lote. INSERT...ON CONFLICT solo permite replay idéntico; comparar payload/versión antes, cuarentena en cambios. No sobrescribir hechos corregidos sin política histórica. Orden:fuentes/versiones→zonas/ubicaciones→estaciones→tipos→canales→observaciones. Exportación CSV/Parquet comparte IDs.

Prueba nativa aislada: **5000 hechos**, 462 canales, 5134 sitios del inventario/observados; **0sensores físicos y0usuarios**. DDL/vistas/función/consultas, PK/FK/trigger probados y valores comparados con referencia independiente. Tiempo medido de preparación/insert:3.219s, no rendimiento de100k ni remoto. Evidencia `results/phase5/postgresql_sample.json`; contenedor y volúmenes eliminados. Hay 832668 hechos estructurales locales candidatos; la muestra5k no acredita mínimo100k en este esquema definitivo aún no autorizado.
