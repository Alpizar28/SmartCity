# Fase 4 — Comparación técnica final

**Se recomienda Madrid como núcleo preferido condicionado. No hay aprobación del equipo ni declaración de cumplimiento completo.** La prioridad es Sprint 1 y la reutilización posterior en HDFS/Spark; la decisión no deriva del 87 inicial ni del tamaño raw.

## Evidencia comparada

| Resultado | Madrid | Nueva York | Londres |
|---|---|---|---|
| PostgreSQL estricto verificado |2/10 (PG09/10) |2/10 |2/10 |
| SQL funcional condicionado a canales lógicos |6/10;460 canales de prueba |6/10;9 canales EPA, no campañas DOT |6/10;5 canales LAQN, no hogares |
| MongoDB factible por datos/diseño |8/10 |7/10 más incidentes parcial |7/10;TfL no verificado |
| MongoDB nativo ejecutado |0/10 |0/10 |0/10 |
| Hechos cargados con PK/FK en prueba local |993374 |112070 |354637 |
| Datos para 500kdocumentos |674704 intervalos tráfico solos;993374 hechos locales |236200 locales;531503IDs311 consultados enAPI, no descargados todos |3997252 claves LCL locales; ventana Jan/Jul sola no basta |
| Datos para 1M Spark |1795279 slots V aire locales, normalización/QA anual pendiente |1875154DOT rawglobales potenciales, unicidad/QA no medida |3997252 claves energéticas locales, distribución no ejecutada |
| Integración medida |19087/33821NO2elegibles;13 sitios co-localizados |146/322DOT–EPA y11/322DOT–311, borough/día |1488/1488 horas interpretadas; hogares con zona fina0% |
| Riesgo diferencial |Unidades meteo, inventarios históricos, energía horaria/KPIs faltantes |4767 claves DOT conflictivas, campañas y mínimos adicionales |LicenciaLAQN, reloj LCL y geografía de hogares ausente |

Los 56,44%,45,34%y100% **no son métricas comparables de calidad**: sus denominadores y supuestos difieren. El 3,42%NYC está condicionado por 16fechas311; no significa imposibilidad de descargar más solicitudes. Londres conserva la ventaja de energía semihoraria, no energía por zona fina.

## Rúbrica y reglas explícitas

Se usa la ponderación de **I p.1**,20/15/15/10/10/10/10/10, total 100. Es una rúbrica de planificación propuesta, **no la calificación oficial E p.28**. Ratings iguales para todas:0ausente,1potencial con dependencia bloqueante,2prerrequisitos parciales,3prerrequisitos medidos suficientes para alcance limitado con cierres pendientes,4subcriterio acreditado dentro de su alcance. Puntos =peso_subcriterio×rating/4. Las calificaciones son juicios de ingeniería sustentados en evidencia, no mediciones universales ni probabilidades de éxito.

Para coberturas se usan fórmulas, no redondeos de consultas:
- SQL estricto:4×verificadas/10; SQL funcional:4×funcionales condicionadas/10; MongoDB nativo:4×verificadas/10=0.
- SoporteMongo:4×media de créditos(CUMPLE1, FACTIBLE0,75, PARCIAL0,25, NO_CUMPLE/NO_VERIFICADO0).
- Spark potencial:créditos1/0,60/0,30/0/0; el descuento expresa falta de ejecución distribuida.
- Dashboard:créditos1/0,75/0,40/0/0, por dominio; pesos movilidad 4, ambiente 4, energía 4, IoT 3. Un PARCIAL no se declara KPIcubierto; se usan los 21 estados exactos de Fase3.

Créditos y esfuerzo son convenciones explícitas que se pueden discutir. No se asigna crédito nativo aPython. Puntos de disponibilidad y trabajo de adquisición se separan; no se suman raw y normalizado como observaciones nuevas. Una dependencia crítica no queda aceptada porque el total sea mayor.

| Criterio | Peso | Madrid | Nueva York | Londres |
|---|---|---|---|---|
| Compatibilidad con consultas obligatorias | 20 | 8.20 | 7.80 | 7.60 |
| Integración con las cuatro tecnologías | 15 | 10.41 | 10.05 | 9.42 |
| Cobertura de indicadores del dashboard | 15 | 5.05 | 3.50 | 2.58 |
| Calidad, procedencia y trazabilidad | 10 | 8.00 | 6.50 | 6.50 |
| Volumen y escalabilidad | 10 | 9.00 | 4.75 | 10.00 |
| Compatibilidad espacial y temporal | 10 | 7.50 | 5.00 | 2.50 |
| Facilidad de descarga y preparación | 10 | 9.00 | 5.75 | 7.25 |
| Riesgo y esfuerzo de implementación | 10 | 6.50 | 3.00 | 3.50 |
| Total | 100 | 63.665 | 46.345 | 49.345 |

**Puntuación final:** Madrid 63.665, Londres 49.345, Nueva York 46.345/100. Decimales son precisión aritmética, no intervalos estadísticos. `04_scores.csv` contiene 24 criterios y3 totales; `results/phase4/subscores.csv` contiene 90 subcriterios con evidencia y condiciones individuales.

## Justificación completa por subcriterio

### C1. Compatibilidad con consultas obligatorias (20 puntos)

| Subcriterio / peso | Madrid: rating y justificación | Nueva York | Londres |
|---|---|---|---|
| SQL estricto ejecutado (4 × verificadas/10) / 4 | 0.8/4 — 2/10 verificadas: PG09/10; diagnóstico NULL no cumplimiento | 0.8/4 — 2/10 verificadas: PG09/10; diagnóstico NULL no cumplimiento | 0.8/4 — 2/10 verificadas: PG09/10; diagnóstico NULL no cumplimiento |
| SQL funcional en alcance lógico (4 × funcionales/10) / 4 | 2.4/4 — 6/10 funcionales condicionadas, no seis estrictamente cumplidas | 2.4/4 — 6/10 funcionales condicionadas, no seis estrictamente cumplidas | 2.4/4 — 6/10 funcionales condicionadas, no seis estrictamente cumplidas |
| MongoDB soporte de datos (4 × media de créditos) / 8 | 2.5/4 — 8 factibles +1 parcial +1 no cumple | 2.3/4 — 7 factibles +2 parciales +1 no cumple | 2.2/4 — 7 factibles +1 parcial +1 no cumple +1 no verificado |
| MongoDB nativo ejecutado (4 × verificadas/10) / 4 | 0/4 — 0/10 nativas; Python no Aggregation Framework | 0/4 — 0/10 nativas; Python no Aggregation Framework | 0/4 — 0/10 nativas; Python no Aggregation Framework |

**Evidencia, faltantes y sensibilidad del criterio:**
- SQL estricto ejecutado (4 × verificadas/10): 03_compliance_matrix.csv; results/phase3/summary.json. Falta: Inventario físico, estado, instalación, organismos completos. Recalcular si: Reejecución semántica nativa tras cerrar fuente/aceptación.
- SQL funcional en alcance lógico (4 × funcionales/10): 03_compliance_matrix.csv; results/phase3/summary.json. Falta: Aceptación docente del canal como unidad y catálogos independientes. Recalcular si: Aceptar alcance y comprobar PG03/04/06/07 sin inventar atributos.
- MongoDB soporte de datos (4 × media de créditos): 03_compliance_matrix.csv; results/phase3/summary.json. Falta: Política de críticos, emisiones reales, incidentes según ciudad. Recalcular si: Fuente y semántica acreditadas; no puntuar una alerta vacía.
- MongoDB nativo ejecutado (4 × verificadas/10): 03_tests_report.md; scripts/phase3_mongo_queries.js. Falta: BSON/pipelines/CRUD/índices nativos. Recalcular si: Evidencia de diez ejecuciones y referencias, en fase autorizada posterior.

### C2. Integración con las cuatro tecnologías (15 puntos)

| Subcriterio / peso | Madrid: rating y justificación | Nueva York | Londres |
|---|---|---|---|
| Relacional, IDs e integridad / 4 | 4/4 — Carga nativa >100k con PK/FK y referencias compartidas de prueba | 4/4 — Carga nativa >100k con PK/FK y referencias compartidas de prueba | 4/4 — Carga nativa >100k con PK/FK y referencias compartidas de prueba |
| Documentos variables y contrato reutilizable / 4 | 2/4 — JSON preliminar y tipos variables auditados; BSON/ingestión entre motores no probados | 2/4 — JSON preliminar y tipos variables auditados; BSON/ingestión entre motores no probados | 2/4 — JSON preliminar y tipos variables auditados; BSON/ingestión entre motores no probados |
| Archivos históricos exportables a HDFS / 3 | 3/4 — CSV/ZIP/Parquet con hashes locales, sin HDFS ejecutado | 3/4 — CSV/JSON/Parquet locales; ampliar ventanas para historia | 2/4 — Miembros LCL válidos; LAQN redistribución pendiente |
| Soporte de los diez productos Spark / 4 | 2.16/4 — 8 factibles,2 parciales; no Spark | 1.8/4 — 6 factibles,3 parciales,1 no verificado; no Spark | 1.92/4 — 7 factibles,2 parciales,1 no verificado; no Spark |

**Evidencia, faltantes y sensibilidad del criterio:**
- Relacional, IDs e integridad: results/phase3/postgres_execution.json; tests/test_phase3.py. Falta: Contrato final no aprobado. Recalcular si: Revisar si contrato invalida identidades existentes.
- Documentos variables y contrato reutilizable: private_results/phase3/*/documents_preview.json; 03_mongodb_matrix.md. Falta: Ejecución integrada nativa. Recalcular si: Carga documental e IDs cruzados validados.
- Archivos históricos exportables a HDFS: 02_artifact_manifest.csv; 03_spark_future_matrix.md. Falta: HDFS/batch/distribución y permisos efectivos. Recalcular si: Ejecutar HDFS y cerrar alcance de exportación.
- Soporte de los diez productos Spark: 03_compliance_matrix.csv; results/phase3/summary.json. Falta: Join aceptado, panel anual, evento y reporte reales. Recalcular si: Evidencia distribuida; no confundir potencial con ejecución.

### C3. Cobertura de indicadores del dashboard (15 puntos)

| Subcriterio / peso | Madrid: rating y justificación | Nueva York | Londres |
|---|---|---|---|
| Movilidad (media de créditos de KPIs) / 4 | 1.56/4 — Vehículos detectados:PARCIAL; Velocidad promedio:PARCIAL; Congestión promedio:PARCIAL; Accidentes/incidentes:FACTIBLE_NO_EJECUTADO; Tiempo promedio de recorrido:NO_CUMPLE | 0.64/4 — Vehículos detectados:PARCIAL; Velocidad promedio:NO_CUMPLE; Congestión promedio:NO_CUMPLE; Accidentes/incidentes:PARCIAL; Tiempo promedio de recorrido:NO_CUMPLE | 0.32/4 — Vehículos detectados:PARCIAL; Velocidad promedio:NO_CUMPLE; Congestión promedio:NO_CUMPLE; Accidentes/incidentes:NO_VERIFICADO; Tiempo promedio de recorrido:NO_CUMPLE |
| Ambiente (media de créditos de KPIs) / 4 | 1.24/4 — Temperatura global promedio:PARCIAL; PM2.5 promedio:FACTIBLE_NO_EJECUTADO; CO₂:NO_CUMPLE; Humedad:PARCIAL; Número de alertas ambientales:NO_CUMPLE | 0.6/4 — Temperatura global promedio:NO_VERIFICADO; PM2.5 promedio:FACTIBLE_NO_EJECUTADO; CO₂:NO_CUMPLE; Humedad:NO_VERIFICADO; Número de alertas ambientales:NO_CUMPLE | 0.0/4 — Temperatura global promedio:NO_VERIFICADO; PM2.5 promedio:NO_VERIFICADO; CO₂:NO_CUMPLE; Humedad:NO_VERIFICADO; Número de alertas ambientales:NO_CUMPLE |
| Energía (media de créditos de KPIs) / 4 | 1.28/4 — Consumo total:PARCIAL; Consumo promedio por zona:PARCIAL; Consumo por hora:NO_CUMPLE; Picos de consumo:PARCIAL; Variación respecto al período anterior:PARCIAL | 1.28/4 — Consumo total:PARCIAL; Consumo promedio por zona:PARCIAL; Consumo por hora:NO_CUMPLE; Picos de consumo:PARCIAL; Variación respecto al período anterior:PARCIAL | 1.28/4 — Consumo total:PARCIAL; Consumo promedio por zona:NO_CUMPLE; Consumo por hora:PARCIAL; Picos de consumo:PARCIAL; Variación respecto al período anterior:PARCIAL |
| IoT (media de créditos de KPIs) / 3 | 1.3/4 — Número de sensores:PARCIAL; Mediciones recibidas:PARCIAL; Sensores activos/inactivos:NO_CUMPLE; Alertas generadas:NO_CUMPLE; Datos por minuto/hora/día:FACTIBLE_NO_EJECUTADO; Total de lecturas registradas por segundo:PARCIAL | 1.3/4 — Número de sensores:PARCIAL; Mediciones recibidas:PARCIAL; Sensores activos/inactivos:NO_CUMPLE; Alertas generadas:NO_CUMPLE; Datos por minuto/hora/día:FACTIBLE_NO_EJECUTADO; Total de lecturas registradas por segundo:PARCIAL | 1.3/4 — Número de sensores:PARCIAL; Mediciones recibidas:PARCIAL; Sensores activos/inactivos:NO_CUMPLE; Alertas generadas:NO_CUMPLE; Datos por minuto/hora/día:FACTIBLE_NO_EJECUTADO; Total de lecturas registradas por segundo:PARCIAL |

**Evidencia, faltantes y sensibilidad del criterio:**
- Movilidad (media de créditos de KPIs): 03_dashboard_coverage.md; 03_compliance_matrix.csv. Falta: UI y KPI faltantes; proxy no indicador observado. Recalcular si: Fuente real/definición aprobada cambia solo KPIs afectados, no UI imaginaria.
- Ambiente (media de créditos de KPIs): 03_dashboard_coverage.md; 03_compliance_matrix.csv. Falta: UI y KPI faltantes; proxy no indicador observado. Recalcular si: Fuente real/definición aprobada cambia solo KPIs afectados, no UI imaginaria.
- Energía (media de créditos de KPIs): 03_dashboard_coverage.md; 03_compliance_matrix.csv. Falta: UI y KPI faltantes; proxy no indicador observado. Recalcular si: Fuente real/definición aprobada cambia solo KPIs afectados, no UI imaginaria.
- IoT (media de créditos de KPIs): 03_dashboard_coverage.md; 03_compliance_matrix.csv. Falta: UI y KPI faltantes; proxy no indicador observado. Recalcular si: Fuente real/definición aprobada cambia solo KPIs afectados, no UI imaginaria.

### C4. Calidad, procedencia y trazabilidad (10 puntos)

| Subcriterio / peso | Madrid: rating y justificación | Nueva York | Londres |
|---|---|---|---|
| Derechos y procedencia institucional / 2 | 4/4 — CC BY4.0 municipal comprobada, atribución requerida | 2/4 — Términos NYC/EPA conservados, derechos terceros pendientes | 1/4 — LCL CC BY, LAQN educativo/restrictivo sin redistribución acreditada |
| Snapshots, hashes y pruebas reproducibles / 2 | 4/4 — Hash/manifiestos y42 pruebas previas, referencias nativas y Python | 4/4 — Hash/manifiestos y42 pruebas previas, referencias nativas y Python | 4/4 — Hash/manifiestos y42 pruebas previas, referencias nativas y Python |
| Identidad natural y duplicados / 2 | 3/4 — Sin duplicados en muestra; ZIP tráfico completo no cardinalizado | 1/4 — 4767 conflictos DOT sin clave física; cuarentena9534 filas | 3/4 — LCL3997252 claves,2748extras idénticos y0conflictos; hogares no medidor |
| Unidades, relojes y diccionarios / 2 | 2/4 — Aire confirmado; meteo provisional y DST fuera de muestra | 3/4 — EPA unidades/UTC confirmados; CRS/clock DOT pendientes | 2/4 — NO2 GMT y kWh; LCL GMT/BST sin resolver |
| QA, nulos, extremos y sesgo declarados / 2 | 3/4 — Flags/nulos/extremos y muestreo cuantificados; no extremos borrados ni representatividad urbana acreditada | 3/4 — Flags/nulos/extremos y muestreo cuantificados; no extremos borrados ni representatividad urbana acreditada | 3/4 — Flags/nulos/extremos y muestreo cuantificados; no extremos borrados ni representatividad urbana acreditada |

**Evidencia, faltantes y sensibilidad del criterio:**
- Derechos y procedencia institucional: 01_source_risks.md; 02_blockers.md; 02_download_manifest.csv. Falta: Alcance de publicación NYC/LAQN. Recalcular si: Permiso/cláusulas compatibles con despliegue previsto.
- Snapshots, hashes y pruebas reproducibles: results/phase3/inputs_manifest.csv; outputs_manifest.csv; tests.xml. Falta: Reproducción sin datos privados distribuibles. Recalcular si: Fallos de hashes o resultados reducirían crédito.
- Identidad natural y duplicados: results/phase3/dot_conflicts.json; validation.json; 02_volume_analysis.md. Falta: Unicidad global tráfico, identidades físicas. Recalcular si: Claves correctas documentadas y prueba global, no incluir valor en PK.
- Unidades, relojes y diccionarios: results/phase3/unit_history_checks.json; 03_integration_gaps.md. Falta: Diccionario meteo/timezone y CRS DOT/LCLclock. Recalcular si: Fuente técnica oficial y pruebas de bordes.
- QA, nulos, extremos y sesgo declarados: 02_quality_metrics.csv; results/*-summary.json; 02_audit_report.md. Falta: Ratificación, panel estable y representatividad. Recalcular si: QA fuente/ventana específica, no afirmar calidad de ciudad entera.

### C5. Volumen y escalabilidad (10 puntos)

| Subcriterio / peso | Madrid: rating y justificación | Nueva York | Londres |
|---|---|---|---|
| 100k hechos SQL efectivamente cargados / 3 | 4/4 — 993374 con PK/FK | 4/4 — 112070 con PK/FK | 4/4 — 354637 con PK/FK |
| 500k documentos reales disponibles localmente / 3 | 4/4 — 674704 intervalos tráfico solos;993374 hechos locales | 1/4 — 236200 locales;531503unique_key311 API no descargados | 4/4 — 3997252 claves LCL locales, ampliar ventana de 347314 |
| 1M registros y crecimiento histórico sin síntesis / 4 | 3/4 — 1795279 slots V aire, ampliación local/DST pendiente; no Spark | 1/4 — 1875154DOT globalrawpotencial, QA/únicos sin comprobar | 4/4 — 3997252 claves locales verificadas; no Spark |

**Evidencia, faltantes y sensibilidad del criterio:**
- 100k hechos SQL efectivamente cargados: results/phase3/postgres_execution.json. Falta: Carga final y recursos de infraestructura no probados. Recalcular si: Nuevo contrato reduce válidos bajo100k.
- 500k documentos reales disponibles localmente: results/phase3/prepared_data.json; validation.json; 02_volume_analysis.md. Falta: MongoDB nativo para todas; adquisición extra NYC. Recalcular si: Contar documentos únicos cargados, no campos ni raw más derivado.
- 1M registros y crecimiento histórico sin síntesis: results/MAD-AIR-annual_counts.json; results/phase3/validation.json; 02_volume_analysis.md. Falta: Ejecución Spark, panel comparable y recursos. Recalcular si: Cardinalidad QA y ejecución real >=1M.

### C6. Compatibilidad espacial y temporal (10 puntos)

| Subcriterio / peso | Madrid: rating y justificación | Nueva York | Londres |
|---|---|---|---|
| Geografía compartida defendible (no ranking de porcentajes) / 4 | 3/4 — 13 sitios co-localizados <1m; radios tráfico solo exploratorios | 2/4 — Borough compartido; EPA3boroughs, CRS DOT pendiente | 1/4 — Energía sin ubicación fina0%; solo contexto ciudad |
| Períodos y relojes comunes / 3 | 3/4 — Jan/Jul2025 sinDST, aire/meteo2025-2026local; accidente2026nojoinJan2025 | 2/4 — Campañas2023, UTC EPA;31116días; interanualidad local pendiente | 1/4 — 2013Jan/Julcomún peroGMT/BSTjulio pendiente, cohorte variable |
| Join medido con denominadores y pérdidas / 3 | 3/4 — 19087/33821 NO2, pérdidas explícitas; no causalidad | 2/4 — 146/322DOT-EPA y11/322DOT-311; muestra y campañas | 1/4 — 1488/1488 horas condicionales, no geografía ni sincronía demostradas |

**Evidencia, faltantes y sensibilidad del criterio:**
- Geografía compartida defendible (no ranking de porcentajes): results/*-integration.json; 03_integration_gaps.md. Falta: Vigencia/cartografía/CRS/geografía hogar. Recalcular si: No casas ficticias; fuente geográfica compatible o alcance aprobado.
- Períodos y relojes comunes: results/phase3/validation.json; 02_integration_results.md. Falta: DST/horas endpoint, exposición y años. Recalcular si: Definición oficial del clock y períodos equivalentes.
- Join medido con denominadores y pérdidas: results/*-integration.json; results/phase3/validation.json. Falta: Ponderación/exposición/cobertura aceptada. Recalcular si: Revalidar semántica de joins, nunca comparar56%contra100%como nota.

### C7. Facilidad de descarga y preparación (10 puntos)

| Subcriterio / peso | Madrid: rating y justificación | Nueva York | Londres |
|---|---|---|---|
| Datos suficientes ya locales para Sprint1 / 3 | 4/4 — Datos y normalización suficientes, ZIP oficial ya descargado | 2/4 — MínimoMongo exige adquisición extra pese aAPIfuncional | 4/4 — LCLhistórico suficiente en4miembros locales |
| Adquisición oficial acotada y robustez / 2 | 3/4 — CSV/ZIP accesibles;403pasado no vigente en recurso auditado | 2/4 — SODA+paginación+EPA rangos; desconexiones/adjuntos404 | 1/4 — LCLRangeignorado yprefijo, LAQNpor sitio/período |
| Complejidad de formatos y limpieza / 2 | 3/4 — CSVsemicolon/HV/decimal, scripts disponibles; meteo unidades | 2/4 — Campañas/SODA/UTC/métodos/qualifier yLL84 padres | 3/4 — CSVenergía simple y JSONLAQN; clock/duplicados conocidos |
| Pipeline offline existente y evidencia de preparación / 3 | 4/4 — Normalización, joins y pruebaSQL completa, sin descargar más núcleo | 3/4 — Pipeline reproduce solo alcance2023/16 fechas, no mínimosMongo/Spark | 3/4 — Pipeline4CSV/5 sitios, no zona niTfL completo |

**Evidencia, faltantes y sensibilidad del criterio:**
- Datos suficientes ya locales para Sprint1: 02_download_manifest.csv; results/phase3/prepared_data.json. Falta: MínimoMongoNYC y catálogos semánticos todas. Recalcular si: Nueva descarga solo con autorización/presupuesto.
- Adquisición oficial acotada y robustez: 02_reproduction.md; results/download.log. Falta: Continuidad de endpoints no garantizada. Recalcular si: Recurso oficial estable/reproducción desde snapshot.
- Complejidad de formatos y limpieza: scripts/readers.py; audit.py; phase3_validate.py. Falta: QA final y claves específicas. Recalcular si: Costo de transformación se confirma en implementación, no horas medidas aquí.
- Pipeline offline existente y evidencia de preparación: scripts/phase3_run.py; results/phase3/run.log. Falta: Carga finalMongo y contrato. Recalcular si: Fallo de reproducción invalida crédito correspondiente.

### C8. Riesgo y esfuerzo de implementación (10 puntos)

| Subcriterio / peso | Madrid: rating y justificación | Nueva York | Londres |
|---|---|---|---|
| Dependencias externas bloqueantes (mayor = menor riesgo) / 4 | 2/4 — Metadatos administrativos/docente ydiccionario, sin cambiar núcleo si acepta límites | 1/4 — Clave DOT requiere proveedor y volumen extra; retraso no acotado | 1/4 — PermisoLAQN/geografía LCL son bloqueos no solucionables con limpieza |
| Viabilidad de calendario (juicio de ingeniería) / 4 | 3/4 — 54-84h-persona estimadas Sprint1 bajo aceptación, reutiliza artefactos | 1/4 — 72-118h-persona estimadas más esperaDOT/adquisición | 2/4 — 64-104h-persona estimadas más licencia/timezone/TfL |
| Gobernanza y publicación / 2 | 3/4 — CC BY núcleo; accidentes minimizar datos personales, faltantes docentes | 2/4 — 311privacidad y términosNYC/EPA sin cierre publicación | 1/4 — LAQNsin redistribución ysin zonasLCL limita despliegue |

**Evidencia, faltantes y sensibilidad del criterio:**
- Dependencias externas bloqueantes (mayor = menor riesgo): 03_integration_gaps.md; 03_feasibility_report.md. Falta: Respuesta de proveedor/docente no obtenida. Recalcular si: Cerrar bloqueos antes 14oct; sin respuesta no garantizar10/10.
- Viabilidad de calendario (juicio de ingeniería): 04_implementation_feasibility.md (estimación, no benchmark). Falta: Disponibilidad horaria real del equipo. Recalcular si: Medir avance al17oct; si ruta crítica no cabe, replanificar.
- Gobernanza y publicación: 01_source_risks.md; 02_blockers.md. Falta: Aprobación de equipo yalcance publicación. Recalcular si: Revisar permisos y datos personales antes deexportar.


## Diferencias respecto a la propuesta inicial

| Alternativa | Puntuación inicial no medida | Evaluación actual | Qué cambió |
|---|---:|---:|---|
| Madrid |87 |63.665 |Tráfico ahora descargado; volumen SQL e integración probados. Se penalizan ausencias administrativas, meteo provisional, historia/zonas y energía horaria/KPIs faltantes |
| Nueva York |76 |46.345 |EPA local confirmado; se descubrieron conflictos DOT persistentes y mínimos adicionales no acreditados localmente |
| Londres |77 |49.345 |LCL ahora cardinalizado y útil para energía horaria; penalizaciones por permisos, reloj, ausencia geográfica e incidentes sin auditoría completa |
| Beijing |79 |No reevaluado |Fuera de las tres auditorías; no es respaldo plenamente validado |

I no desglosa ratings originales por criterio: **no se puede reconstruir una resta causal exacta de 87 a 63.665**. Cambian el paquete (LCL en Londres), los hallazgos y la base probatoria. No se toma el ranking preliminar como resultado experimental.

## Robustez y decisión independiente del total

Sin volumen(C5), sobre 90 puntos: Madrid 54.66, NYC 41.59, Londres 39.34. Sin compatibilidad espacial/temporal(C6):Madrid 56.16, NYC 41.34, Londres 46.84. La preferencia se mantiene: no depende únicamente de volumen o porcentajes de join.

Mover1rating en un criterio completo de 10 puntos cambia2,5 puntos; cambios acumulados y nueva evidencia pueden cambiar el orden. Confianza cualitativa **media-alta en la preferencia relativa**, **baja en cumplimiento completo sin aprobaciones**. No son porcentajes de probabilidad.

Vetos:rechazo docente de unidadcanal/estado/instalación sin fuente real; todos losKPIs estrictos sin complementos; derechos incompatibles; mínimos útiles insuficientes en contrato aceptado; imposibilidad de ejecución nativa para 23oct. Mayor puntuación no supera veto. Ninguna alternativa está validada para todos los atributos estrictos actuales.

Madrid reduce trabajo incremental:datos locales suficientes, categorías reales e incidentes por expediente, mismo municipio e integración más específica entre redes. Londres es respaldo condicionado por volumen y energía horaria; NYC añade proveedor DOT y adquisición adicional a la ruta crítica. La elección exige aprobar alcance, no ocultar brechas. **Fase5no iniciada; no implementación del dataset.**
