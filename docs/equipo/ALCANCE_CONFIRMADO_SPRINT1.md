# Alcance del Sprint 1 — PostgreSQL y MongoDB — 28/10/2026

## Autoridad y criterio de aceptación

Según la aclaración docente del 28/10/2026 comunicada al equipo, el avance comprende
la **«Sección de PostgreSQL y MongoDB»**, sin rúbrica independiente.
La referencia principal son las secciones **«Uso de PostgreSQL» y «Uso de
MongoDB»** del enunciado oficial, páginas 8–12. El avance no se reduce a ejecutar
las veinte consultas.

Se incluyen como objetivos los mínimos generales vinculados a estos motores:
**100.000 registros PostgreSQL y 500.000 documentos MongoDB** (p. 26). El volumen
se acredita por motor, sin sumar replay, administración, incidentes ni generaciones
diferentes.

La aclaración fue comunicada al equipo; no se dispone aquí de una rúbrica
independiente ni de aprobación docente adicional de los datos o las adaptaciones.
Se consultó
la transcripción del enunciado dentro del ZIP privado,
`research/datasets/results/phase3/academic_original.txt`, SHA-256
`b9b7e402c54e83890c14623a162b49c8eaefd485f6e33991bf0662bc4f1080f0`.
No se copia el original académico ni su transcripción completa a la entrega.

Un PASS acredita el comportamiento probado dentro de su alcance; no convierte
una adaptación semántica, limitación del modelo o requisito sin evidencia en
cumplimiento académico completo.

## PostgreSQL: requisitos explícitos

| Requisito | Fuente | Cobertura y condición de cierre |
|---|---|---|
| Modelo entidad-relación y justificación del diseño | pp. 8–9 | [E-R normalizado completo](../arquitectura/diagrama_3nf.md) y [DF/impacto](../../sprint1/postgres/impacto_3nf.md); catorce tablas, incluidas dos auxiliares |
| Sensores: ID, nombre, tipo, instalación y estado | p. 8 | `sensors`; atributos administrativos demo con procedencia sintética, no inventario físico |
| Ubicaciones: ID, zona, distrito y coordenadas | p. 8 | `locations`, `zones` y estaciones; nulos y límites de vigencia geográfica documentados |
| Categorías: ID y nombre | p. 8 | `sensor_categories` y `sensor_types`; clasificación demo independiente de `measurement_types` |
| Usuarios: ID, nombre y correo | p. 9 | `users`; administración sintética autorizada, no personas tomadas de datasets |
| Organismos: ID, nombre y responsable | p. 9 | `organizations`; demo no acredita operadores municipales reales |
| Normalización hasta 3FN | p. 9 | **Corregida en el nuevo DDL**: separación de fuente, reloj, contrato y asignaciones; cierres de DF sobre las catorce relaciones y verificación nativa separada |
| Tablas, llaves primarias/foráneas, relaciones e índices apropiados | p. 9 | Catálogo normalizado: 14 PK, 17 FK y 25 índices; el catálogo histórico de doce tablas se conserva identificado |
| SELECT, WHERE, ORDER BY, DISTINCT | p. 9 | [Consultas normalizadas](../../sprint1/postgres/queries_v2_3nf.sql) y [SQL avanzado verificado](../../sprint1/postgres/cierre_3nf.md#evidencia-nueva-de-ejecución) |
| JOIN, INNER JOIN y LEFT JOIN | p. 9 | Consultas/vista contractual del DDL normalizado y evidencia nativa identificada en el cierre 3FN |
| GROUP BY, HAVING, COUNT, SUM, AVG, MIN y MAX | p. 9 | Consultas normalizadas y complemento observado, separados por fuente, magnitud y unidad |
| Subconsultas, CTE, funciones de ventana, fechas y consultas utilizando índices | p. 9 | PG07/PG08, SQL complementario y planes registrados como cobertura adicional a la lista de diez consultas |
| Diez consultas obligatorias, incluida vista y función/procedimiento | p. 10 | [Matriz PG01–PG10](MATRIZ_CONSULTAS_SPRINT1.md); ejecución documentada; PG07 carece de vínculo físico acreditado y PG10 cuenta canales |
| Mínimo 100.000 registros | p. 26, incorporado al avance por esta aclaración | **Verificado**: evidencia masiva v2 de 748.889 filas; no es una carga nueva del servidor compartido |

La **verificación técnica de 3FN está completada** para las catorce relaciones
del DDL normalizado. Los cierres exhaustivos se calculan sobre las DF declaradas
en `dependencias_3nf.json`, con sus claves candidatas, y el inventario se coteja
con las 83 columnas del catálogo PostgreSQL. JSONB se considera un dominio SQL
tipado indivisible; no se afirma normalización recursiva de sus propiedades.
Los opcionales NULL no se usan como claves candidatas ni se infieren DF de
coincidencias del lote. La evidencia masiva del validador actual es
`20261028T071812-55791345.json`; las muestras previas corresponden a versiones
anteriores del script y conservan sus hashes originales.

La reconstrucción de las 748.889 lecturas y las pruebas nativas complementan la
demostración formal; no prueban por sí solas que la cobertura declarada contenga
toda dependencia semántica imaginable ni acreditan dispositivos físicos.
La corrección usa un DDL nuevo para bases locales nuevas, sin migrar bases
compartidas ni cambiar el contrato documental. La auditoría del modelo anterior
permanece como antecedente y no describe el DDL normalizado.

## MongoDB: requisitos explícitos

| Requisito | Fuente | Cobertura y condición de cierre |
|---|---|---|
| Modelo documental/NoSQL y justificación de su uso | p. 10 | Desnormalización, estructuras variables y acceso por canal/fecha documentados en el [cierre técnico](../../sprint1/mongodb/evidencia_final_mongodb.md) y el modelo del informe |
| Lecturas de sensores | p. 11 | `readings`: 748.889 observaciones con sensor físico desconocido; la consulta por identidad de sensor se demuestra adicionalmente con lecturas sintéticas aisladas |
| Eventos detectados | p. 11 | `derived_events`: 10.841; regla demo versionada, no eventos oficiales históricos |
| Alertas automáticas | p. 11 | `alerts`: 10.841 generadas automáticamente por el pipeline local; replay actual, sin notificación externa ni carácter oficial |
| Incidentes urbanos | p. 11 | `incidents`: 14.388 expedientes anonimizados de 2026, separados de enero de 2025 |
| Información dinámica no estructurada | p. 11 | Demostrada con tres textos sintéticos, atributos heterogéneos y revisiones en el [laboratorio aislado](../../sprint1/mongodb/academico/README.md); selección completa contrastada con Python. Los objetos `measurements`/`provenance` públicos siguen siendo semiestructurados |
| insertOne, insertMany, find, findOne, updateOne, updateMany y deleteOne | p. 11 | **PASS nativo actual** sobre `practica_crud`, con siete marcadores, comprobaciones y `readings` intacta |
| Filtros y operadores | p. 11 | MG01/MG02/MG10 y `$match`; parámetros y resultados nativos |
| Proyecciones y ordenamiento | p. 11 | `buscar()` y pipelines; salidas y planes MG01/MG10 |
| Agregaciones, agrupaciones y Aggregation Framework obligatorio | p. 11 | MG03/MG05–MG09 y generación `$project`/`$merge`; contraste con Python |
| Índices | p. 11 | **Verificado**: 13 índices en siete colecciones; plan MG01 selectivo y MG10 con recorrido de todo el tráfico; sin acreditación de optimización completa |
| Diez consultas obligatorias | p. 12 | **PASS técnico actual MG01–MG10**, con límites semánticos por consulta |
| Mínimo 500.000 documentos | p. 26, incorporado al avance por esta aclaración | **Verificado**: 748.889 lecturas observadas, sin sumar incidentes ni derivados |

Evidencia actual: [cierre técnico MongoDB](../../sprint1/mongodb/evidencia_final_mongodb.md)
y [comprobación de la ejecución pública](../../sprint1/mongodb/evidencias/20261028T055755-3fea400d/comprobacion_cierre.json).
El PASS no sustituye la justificación documental ni la aceptación de las
adaptaciones. La información narrativa y las consultas por sensor/tipo cuentan
ahora con una demostración sintética separada y su contraste independiente.
La demostración de almacenamiento distribuido sigue abierta.

## Aspectos transversales o pendientes de confirmación

| Aspecto | Clasificación y tratamiento en octubre |
|---|---|
| Fuentes, licencia, limpieza, IDs, fechas y consistencia SQL/Mongo | Transversal a los motores: procedencia y reconciliación actual documentadas. Las dos fuentes no acreditan integración final de cuatro tecnologías |
| Vistas materializadas, particionamiento y optimización de objetivos generales (p. 2) | **Transversal o pendiente de confirmación para este avance**. La sección PostgreSQL sí exige vista, función, SQL avanzado e índices; una vista ordinaria no demuestra una materializada. No se implementaron vistas materializadas ni particionamiento; su exigencia para este avance permanece pendiente de confirmación |
| Big Data y «almacenamiento distribuido» dentro de Uso de MongoDB (p. 11) | **Requisito explícito; almacenamiento distribuido sin demostración**. Volumen y recursos acreditados en standalone. Modalidad suficiente pendiente de aclaración docente; no se acredita una topología específica ni se excluye automáticamente de octubre |
| Autenticación, presentación en servidor compartido, backups y concurrencia de producción | Entorno local probado documentado; las exigencias concretas de demostración compartida permanecen por confirmar, sin atribuir condiciones adicionales al profesor |
| Sensor físico, instalación/estado demo, zonas y reglas de eventos/alertas | Pendiente de aceptación académica; requisito y adaptación documentados, sin vínculos físicos ni resultados inventados |
| Recomendaciones de bytes, escenarios avanzados o más de cinco millones de registros | No reemplazan los mínimos por motor ni crean automáticamente otra meta obligatoria para el 28/10 |

## Implementaciones que se dejan para noviembre

Hadoop/HDFS, MapReduce/Hive, Apache Spark, pipelines o análisis distribuidos,
el dashboard completo y la comparación final entre cuatro motores corresponden
a la continuación de noviembre y no se implementaron en este avance.
Su ausencia no constituye un bloqueo confirmado del Sprint 1.

Se conservan los contratos y referencias de arquitectura existentes para la
continuación de noviembre, sin afirmar integración distribuida ya ejecutada.

## Documentación y regla de cierre

La documentación de entrega reúne: este alcance; E-R/DDL/relaciones/índices y auditoría 3FN;
modelo y justificación documental MongoDB, incluidas sus cinco clases de
información; código oficial de las veinte consultas, SQL avanzado y siete CRUD;
resultados, parámetros, muestras, volúmenes, replay, reconciliación, hashes,
versiones, entorno y limitaciones. Los fixtures, observaciones, derivados y
la administración sintética se identifican por separado. Los datasets privados
y las credenciales quedan fuera de la entrega pública.

Los mínimos por motor, las veinte consultas y la normalización 3FN tienen
evidencia técnica dentro de sus alcances declarados. La aceptación académica
global no está acreditada: permanece sin demostración el almacenamiento distribuido
MongoDB. El laboratorio sintético resuelve las demostraciones por sensor y tipo,
y la recuperación narrativa, sin acreditar inventario físico municipal. Sus resultados se registran en el
[laboratorio académico](../../sprint1/mongodb/academico/README.md) y su ejecución
`20261028T161057-eff98453`. Los límites de las pruebas negativas PostgreSQL
se describen en el [cierre 3FN](../../sprint1/postgres/cierre_3nf.md#cobertura-de-operaciones-negativas).
Las auditorías documentales anteriores conservan el alcance histórico de su fecha.


## Complemento académico aislado

La ejecución `20261028T161057-eff98453` demuestra MG01 con un sensor sintético
explícito y MG07 mediante lectura–sensor–tipo, separado por magnitud y unidad.
Se conservan las consultas públicas anteriores como funcionalidades adicionales.
El diagrama de las siete colecciones oficiales está en
`docs/avance_1/SmartCity_Sprint1_Entrega.tex`; el laboratorio se documenta por separado.
Las nueve lecturas sintéticas no se agregan al volumen Madrid v2.
