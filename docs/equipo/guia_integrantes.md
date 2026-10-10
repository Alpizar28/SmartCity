# Guía de revisión y handoff del equipo

Este paquete describe **artefactos disponibles**, no tareas individuales ya terminadas por Daniel, Kembly o Fernanda. La automatización previa y la documentación no acreditan revisión independiente de cada integrante. Asignación propuesta en P, pp. 1–5; [handoff de Fase 5](../../research/datasets/05_team_handoff.md).

## Lo disponible, preliminar y pendiente

| Estado | Contenido |
|---|---|
| Evidencia ejecutada | Investigación/auditorías fases 0–4; preparación de enero; pruebas locales limitadas SQL/Mongo; 82 pruebas históricas y manifiestos |
| Borrador para revisión | Contrato/diccionario, DDL de doce tablas, colecciones, consultas, diagramas, pipeline acotado y texto académico |
| Sin evidencia de cierre | Ratificación, revisión individual de modelos/documentos, excepciones docentes, unidades/clocks/CRS, cargas definitivas, veinte consultas completas, respaldo/restauración y revisión cruzada humana |
| No implementado | Hadoop/HDFS, Spark distribuido y dashboard; sin benchmark remoto |

## José — fuentes, pipeline e ingestión

1. Revisar [fuentes/versiones](../datasets/fuentes_y_procedencia.md), [calidad](../datasets/calidad_y_limitaciones.md) y [preparation.json](../../research/datasets/results/phase5/preparation.json). Entregar una ficha firmada con ventana, filtros, QA y licencias; ratificación de Madrid aún pendiente.
2. Cerrar unidades meteo, clocks meteo/tráfico, CRS por grupo de campos y vigencia histórica. Entregar referencia técnica, regla y pruebas; no reemplazar NULL/hipótesis sin versionar y, si cambia UTC, planear migración de IDs.
3. Reproducir [dry-run y pruebas](../arquitectura/pipeline.md) con insumos autorizados; documentar requisitos de un clon. El script actual limita exportación; no cargar millones ni bases compartidas por esta guía.
4. Diseñar con Daniel/Kembly manifests por lote, conciliación, tratamiento de correcciones, recursos y respaldo/restauración. Ejecutar ingestión completa **solo después de revisión y autorización explícita futura**.

**Salida esperada:** fuentes/metadata cerradas o brechas justificadas, contrato versionado, instrucciones y conteos reproducibles. Nada aquí declara aprobados geografía, tiempos ni ingestión final.

## Daniel — PostgreSQL

1. Revisar [modelo](../arquitectura/modelos.md), [DDL](../../research/datasets/scripts/phase5_postgresql.sql) y [E-R](../arquitectura/diagramas.md) contra dependencias funcionales/3FN, nulos, cardinalidades, PK/FK, UNIQUE y trigger. La revisión humana de Daniel no está acreditada todavía.
2. Contrastar [muestra nativa](../../research/datasets/results/phase5/postgresql_sample.json) con restricciones, catálogos, vista y función; reproducir opcionalmente en copia local autorizada. No poblar sensores/usuarios para ocultar ausencia de evidencia.
3. Preparar diez consultas con propósito, SQL, resultado, evidencia y estado exacto: [queries](../../research/datasets/scripts/phase5_postgresql_queries.sql), [brechas](../../research/datasets/05_postgresql_design.md). Resolver PG03/04/06/07 y aceptación de canales antes de afirmar 10/10.
4. Proponer índices/EXPLAIN, vista materializada y particionamiento solo si justificados. Validar mínimo final, staging e idempotencia en una fase posterior autorizada.

**Salida esperada:** diseño revisado, diez fichas por consulta y resultados semánticamente aceptados; no únicamente SQL que ejecuta sobre tablas vacías.

## Kembly — MongoDB

1. Revisar [colecciones y tipos](../arquitectura/modelos.md) y [contrato/diccionario](../../research/datasets/05_data_contract.md); mantener un documento por intervalo de tráfico y `sensor_id=NULL` sin identidad física.
2. Contrastar [prueba nativa](../../research/datasets/results/phase5/mongodb_execution.json), validator, índices y explain natural; usar [phase5_mongo_test.js](../../research/datasets/scripts/phase5_mongo_test.js). Reproducir solo en copia local autorizada, CRUD en `crud_demo`, no originales.
3. Entregar diez fichas Mongo con filtros/agregaciones/índices/resultados/alcance. Siete diseños ya tienen evidencia técnica; MG04/MG05 necesitan reglas/emisión y MG08 una prueba separada con accidentes de 2026. No declarar esas tres tareas finalizadas.
4. Revisar estándar frente a time-series, coherencia de referencias SQL, lotes/replay y backup/restore. Carga ≥500.000 posterior y autorizada; la muestra de 5.000 no la acredita.

**Salida esperada:** modelo revisado, CRUD reproducible aislado y diez consultas con estados honestos, sin alertas ficticias.

## Fernanda — informe, actas y trazabilidad

1. Adaptar [texto académico](../academico/texto_para_informe.md), [declaración de IA](../academico/uso_ia.md) y referencias al formato institucional. Confirmar normativa/identidad del curso; esta adaptación/revisión no está acreditada como finalizada.
2. Revisar [cinco diagramas](../arquitectura/diagramas.md) con Daniel/Kembly; recoger correcciones y firmas sin inventar entidades, FK o estados.
3. Consolidar [preguntas al profesor](preguntas_profesor.md), respuestas reales y acta de ratificación del [ADR-001](../decisiones/ADR-001-madrid.md). Las casillas pendientes no son aprobaciones.
4. Usar [índice de evidencias](../datasets/indice_evidencias.md) para la matriz requisito–responsable–archivo–evidencia–estado. Mantener separación de pruebas locales, mínimos finales y desempeño distribuido.
5. Coordinar revisión cruzada: otro integrante reproduce cada bloque y registra entorno, comandos, outputs, límites y fecha. Revisar [publicación segura](revision_repositorio.md) antes de preparar una entrega.

**Salida esperada:** sección académica revisada, diagramas validados por responsables, acta/respuestas y matriz trazable. No se declara que Fernanda ya realizó esa revisión.

## Hitos propuestos y siguientes pasos

P propone cierre de modelos/IDs el 14 de octubre, carga inicial el 17, mínimos/backups el 20, veinte consultas el 23, revisión cruzada el 24 e informe el 25; congelamiento/demo el 26–27 y avance el 28. Son **hitos internos propuestos**, no avance efectivamente ejecutado ni fecha docente confirmada. La entrega final de E es 25 de noviembre de 2026. Detalle y páginas: [00_requirements.md](../../research/datasets/00_requirements.md).

Orden práctico: revisar esta documentación → resolver preguntas/metadata → ratificar contrato/ADR → autorizar implementación y acceso → ejecutar pruebas/cargas con evidencia → revisión cruzada → publicación coordinada. Si no se cierra una condición, mantener PARCIAL/NO_CUMPLE y replanificar. No hay commits, push, PR, merge o autorización de redeploy derivados de esta guía.
