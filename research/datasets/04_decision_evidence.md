# Fase 4 — Evidencia de decisión

## Autoridad y revisión

E=enunciado28páginas:dosfuentesp6, cincoentidadesp8–9, PGp10, Mongop12, HDFSp13–14, Sparkp15–16,21KPIs/visualizaciónp18–19, mínimosp26, rúbricap28. Página3infográfica sintexto completo:usar p26para mínimos. P=plan6páginas:responsabilidades p.1–4/hitosp4–5. I=propuesta5páginas:pesosp1/notas87/79/76/77p2, expresamente no medidas. La rúbricaI no es la académicaE.

Se leyeron completos todos los entregablesMD00/01/02/03, matricesCSV, resultados priorizados y los tresPDF. Textos extraídos en `results/phase4/E_original.txt`, `P_original.txt`, `I_original.txt`;SHA/path/páginas en `evidence_checks.json`. READMEprevio y JSON03sinselección describen su fase histórica;no se sobrescribieron.

## Afirmación → artefacto → significado

| Hallazgo | Artefacto/campo | Interpretación y límite |
|---|---|---|
| SQL2/10estrictas,6/10condicionadas | `phase3/summary.json`→postgresql_strict_verified/postgresql_functional_logical_scope; `03_compliance_matrix.csv` |PG09/10nativas;no30cumplimientos por 30diseños |
| Mongo8/7/7factibles,0nativas | `summary.json`→mongodb_data_supported_not_native/mongodb_native_executed |Python no BSON/CRUD/Aggregation Framework |
| Cargas993374/112070/354637 | `phase3/postgres_execution.json`→cities.*.loaded_readings; `prepared_data.json`→eligible_unique_readings |Hechos nativos en prueba local con PK/FK;no cargas finales/remotas |
| ReferenciasSQL iguales aPython | `postgres_execution.json`→cities.*.queries.*.equals_python_reference; `*_expected_sql.json`; `proof_queries.sql` |Mismo alcance, referencia independiente, no calidad global |
| Raw13351700/247526/4007440 | `phase3/validation.json`→recounted_primary_raw_rows; `phase2_summary.json` |Granularidades distintas, no sensores ni claves únicas |
| Madrid 19087/33821 y13 sitios | `Madrid-integration.json`→air_row_spatiotemporal_matched/eligible_air_NO2_rows/co_located_sites; `phase3/madrid_no2_losses.csv` |14722sinco-localización,12sinT;56,435351%NO2elegible, no tasa de falla |
| Tráfico674704 intervalos elegibles | `Madrid-integration.json`→traffic.normalization; `MAD-TRAFFIC-summary.json` |MuestraID%20,0duplicados;13,2Mrawno cardinalizados globalmente |
| Aire1795279 slots V | `MAD-AIR-annual_counts.json`→flags_full_year.V/raw_duplicate_keys |2025–ago2026;normalizaciónDST/QA final, no Spark |
| DOT4767conflictos | `phase3/dot_conflicts.json`→groups/conflicting_rows/candidate_duplicate_extras/campaigns_with_conflicts |9534 filas,2campañas;descriptores no resuelven contador, cero duplicados idénticos |
| NYC 146/322 y11/322 | `NYC-integration.json`→DOT_EPA/DOT_311; `phase3/validation.json`→NYC.joins |Borough/día,16fechas311, no fracción de solicitudes ni fallas |
| NYC 531503IDs311consultables | `02_volume_analysis.md`;respuestas APIdeenero/julio en `02_download_manifest.csv` |242173+289330IDs de meses disjuntos, no todosdescargados/cargados |
| LCL3997252 claves/0conflictos | `phase3/validation.json`→London.expanded.unique_keys/conflicting_extra_values;SQLiteprivado |4CSV/121hogares,2748extrasidénticos,119faltantes, no167M/ZIPentero |
| Londres 100%temporal/0%geográfico | `London-integration.json`→coverage/household_fine_zone_mapping_pct; `validation.json`→London.join |1488 horas interpretadas, clockjulio pendiente, panel108–119 |
| Unidades aire vsmeteo | `phase3/unit_history_checks.json`→Madrid; `madrid_dictionary_provenance.json` |Aire confirmado;nombre de magnitud no acredita unidad meteorológica |
| Incidentes14388,2categoríaNULL | `phase3/incident_checks.json`→Madrid; `MAD-CRASH-incidents.json` |33322detalles no accidentes, solo2026auditado |
| DerechosMadrid/LAQN | `01_source_risks.md`; `02_blockers.md`;probesM25/L11-refresh en manifiesto |CCBYmunicipal conatribución;uso LAQNeducativo no redistribución general |
| 42 pruebas previas | `phase3/legacy_tests.xml`22 +`phase3/tests.xml`20; `run.log` |Sin fallos/errores/omisiones;no pruebas deMongo/Spark/remoto |
| AislamientoSQL/cleanup | `postgres_execution.json`→network/published_ports/container_removed/anonymous_volumes_removed |Contenedor único sin red, no servicios existentes alterados |

## Verificaciones nuevas sin repetir auditoría completa

Se verificaron hashes/tamaños de **todos** los archivos en `phase3/inputs_manifest.csv` y `outputs_manifest.csv`, incluidosraw yderivados, y los cinco recursos de datos seleccionados. Se reconcilió matriz153 filas conresumenJSON, conteosnativos/denominadores/conflictos yJUnit42 pruebas;no se repitióescaneo de 13Mtráfico/4MLCLnicargaPG. Copiar textoPDF yhash no modifica originales. Cero red/descargas nuevas;presupuesto Fase2sinconsumo adicional.

Comandos desde `research/datasets/`:

```bash
.venv/bin/python scripts/phase4_evaluate.py
.venv/bin/python scripts/phase4_reports.py
.venv/bin/python -m pytest tests/test_audit.py tests/test_saved_evidence.py tests/test_phase3.py tests/test_phase4.py -q --basetemp=/tmp/opencode/smartcity-phase4-tests --junitxml=results/phase4/tests.xml
.venv/bin/python scripts/phase4_finalize.py
```

Se volvieron a ejecutar las42 pruebas anteriores y se agregaron6de Fase4: reconciliación de pesos/subcriterios/totales por ciudad, ausencia de crédito nativo/aprobación humana, sensibilidad y entregables/cobertura de 20brechas. Las pruebas03 leen resultados PostgreSQL guardados y originales; no lanzan contenedor ni consultan remoto. No usar `phase3_run.py`/`run_offline.py` en esta fase, pues repetirían cargas/regeneraciones previas. Dependencias: entorno Python3.11.16/lock existente y pdftotext; ninguna infraestructura o paquete nuevo.

Resultados: `evidence_checks.json`, `subscores.csv`, `scores_summary.json`, `sensitivity.json`, snapshots seleccionados CSV, JUnitnuevo y `final_checks.json`/`outputs_manifest.csv`. Puntajes reproducibles desde misma evidencia;horas-persona/riesgos son juicios, no benchmarks. No se recibieronfirmas, respuesta docente ni permisos jurídicos nuevos;licencias no fueron reconsultadas enred, no garantía indefinida.
