# Índice de evidencias — fases 0–5

Esta guía es la navegación actual. Los entregables anteriores son snapshots históricos: frases como «Fase 2 no iniciada» o «MongoDB no disponible» describen su fecha, no un bloqueo vigente después de Fase 5. No se sobrescriben ni regeneran para producir esta documentación.

## Investigación y requisitos

| Fase | Lectura principal | Evidencia estructurada / reproducción |
|---|---|---|
| 0: autoridad y requisitos | [Requisitos](../../research/datasets/00_requirements.md), [riesgos](../../research/datasets/00_risks.md) | [Matriz oficial de consultas](../../research/datasets/00_query_matrix.csv); [PDFs E/P/I y hashes](../../research/datasets/README.md) |
| 1: investigación de fuentes | [Investigación](../../research/datasets/01_research.md), [shortlist](../../research/datasets/01_shortlist.md), [arquitecturas candidatas](../../research/datasets/01_candidate_architectures.md) | [Catálogo de 30 fuentes](../../research/datasets/01_sources_catalog.csv), [HTTP](../../research/datasets/01_http_evidence.csv), [métodos](../../research/datasets/01_download_methods.md), [riesgos](../../research/datasets/01_source_risks.md) |
| 2: auditoría real | [Reporte](../../research/datasets/02_audit_report.md), [integraciones](../../research/datasets/02_integration_results.md), [bloqueos](../../research/datasets/02_blockers.md), [volumen](../../research/datasets/02_volume_analysis.md) | [Descargas/URL/SHA](../../research/datasets/02_download_manifest.csv), [artefactos/CRC](../../research/datasets/02_artifact_manifest.csv), [calidad](../../research/datasets/02_quality_metrics.csv), [reproducción](../../research/datasets/02_reproduction.md) |
| 3: viabilidad académica | [Viabilidad](../../research/datasets/03_feasibility_report.md), [gaps](../../research/datasets/03_integration_gaps.md), [pruebas](../../research/datasets/03_tests_report.md) | [Cumplimiento por consulta](../../research/datasets/03_compliance_matrix.csv), [origen](../../research/datasets/03_data_origin_matrix.csv), [SQL](../../research/datasets/03_postgresql_matrix.md), [MongoDB](../../research/datasets/03_mongodb_matrix.md), [Spark futuro](../../research/datasets/03_spark_future_matrix.md), [dashboard](../../research/datasets/03_dashboard_coverage.md) |
| 4: comparación y recomendación | [Comparación](../../research/datasets/04_final_comparison.md), [selección](../../research/datasets/04_selected_dataset.md), [evidencia](../../research/datasets/04_decision_evidence.md) | [Puntuaciones exactas](../../research/datasets/04_scores.csv), [subcriterios](../../research/datasets/results/phase4/subscores.csv), [sensibilidad](../../research/datasets/results/phase4/sensitivity.json), [factibilidad](../../research/datasets/04_implementation_feasibility.md), [riesgos](../../research/datasets/04_open_risks.md), [decisiones](../../research/datasets/04_team_decisions.md) |
| 5: preparación limitada | [Manifiesto](../../research/datasets/05_dataset_manifest.md), [contrato](../../research/datasets/05_data_contract.md), [diccionario](../../research/datasets/05_data_dictionary.csv) | [SQL](../../research/datasets/05_postgresql_design.md), [MongoDB](../../research/datasets/05_mongodb_design.md), [pipeline](../../research/datasets/05_ingestion_plan.md), [volumen](../../research/datasets/05_volume_strategy.md), [prueba MongoDB](../../research/datasets/05_native_mongodb_test.md), [decisiones](../../research/datasets/05_academic_decisions.md), [handoff](../../research/datasets/05_team_handoff.md), [aceptación de fase](../../research/datasets/05_acceptance_checklist.md) |

## Resultados decisivos para citar

- Enero de 2025: [preparation.json](../../research/datasets/results/phase5/preparation.json), campos `counts.*.effective_documents`, `configuration`, `source_snapshots` y `cache`.
- PostgreSQL acotado: [postgresql_sample.json](../../research/datasets/results/phase5/postgresql_sample.json), `native_executed`, `counts`, `constraints`, comparación con referencia y cleanup.
- MongoDB acotado: [mongodb_execution.json](../../research/datasets/results/phase5/mongodb_execution.json), tipos BSON, consultas, replay, índices, `natural_explain` y cleanup.
- Ejemplos reales mínimos: [examples.extjson](../../research/datasets/results/phase5/examples.extjson). No son una nueva población ni lecturas de sensores físicos identificados.
- Pruebas históricas: [JUnit de Fase 5](../../research/datasets/results/phase5/tests.xml) y [sello de Fase 5](../../research/datasets/results/phase5/final_checks.json).
- Integración exploratoria: [Madrid](../../research/datasets/results/Madrid-integration.json), [Nueva York](../../research/datasets/results/NYC-integration.json), [Londres](../../research/datasets/results/London-integration.json). Cada porcentaje tiene un denominador diferente.
- Volumen ampliable: [aire completo](../../research/datasets/results/MAD-AIR-annual_counts.json), [cardinalidad de Fase 3](../../research/datasets/results/phase3/validation.json). El nombre `annual_counts` no restringe el recurso a un único año.
- Hashes y conservación: [manifiesto final de Fase 5](../../research/datasets/results/phase5/outputs_manifest.csv); los paths ignorados requieren insumos locales autorizados.

## Datos privados y evidencia histórica supersedida

`raw/`, `private_results/`, `.venv/`, caches y ledgers no se publican. Los PDFs E/P/I están originalmente en `/home/jp/Descargas/`; los hashes y páginas se conservan en [evidence_checks.json](../../research/datasets/results/phase4/evidence_checks.json). Sus transcripciones completas permanecen locales, ignoradas hasta confirmar autorización de redistribución; un clon no incluye todo lo requerido para verificar manifiestos privados.

[superseded_type_filter.json](../../research/datasets/results/phase5/superseded_type_filter.json) corresponde a un filtro anterior incompleto de tráfico; no usar su subtotal como población vigente. [preparation_before_provenance_refinement.json](../../research/datasets/results/phase5/preparation_before_provenance_refinement.json) tampoco se suma a la población actual. Los intentos fallidos de motores y las salidas repetidas se preservan para trazabilidad, no para inflar resultados.

Volver al [índice documental](../README.md).
