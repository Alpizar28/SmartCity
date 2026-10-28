# Alcance del Sprint 1 — PostgreSQL y MongoDB — 28/10/2026

## Autoridad y criterio de aceptación

Según la aclaración comunicada por Kembly el 28/10/2026, el profesor indicó
**«Sección de PostgreSQL y MongoDB»**, sin proporcionar una rúbrica independiente.
La referencia principal son las secciones **«Uso de PostgreSQL» y «Uso de
MongoDB»** del enunciado oficial, páginas 8–12. El avance no se reduce a ejecutar
las veinte consultas.

Se incluyen como objetivos los mínimos generales vinculados a estos motores:
**100.000 registros PostgreSQL y 500.000 documentos MongoDB** (p. 26). Demostrar
el volumen por motor; no sumar replay, administración, incidentes ni generaciones
diferentes para inflarlo.

La aclaración procede de la comunicación del usuario: no se atribuye al profesor
una rúbrica, aprobación de datos o instrucción adicional no aportada. Se consultó
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
| Ubicaciones: ID, zona, distrito y coordenadas | p. 8 | `locations`, `zones` y estaciones; preservar nulos y límites de vigencia geográfica |
| Categorías: ID y nombre | p. 8 | `sensor_categories` y `sensor_types`; clasificación demo independiente de `measurement_types` |
| Usuarios: ID, nombre y correo | p. 9 | `users`; administración sintética autorizada, no personas tomadas de datasets |
| Organismos: ID, nombre y responsable | p. 9 | `organizations`; demo no acredita operadores municipales reales |
| Normalización hasta 3FN | p. 9 | **Corregida en el nuevo DDL**: separación de fuente, reloj, contrato y asignaciones; cierres de DF sobre las catorce relaciones y verificación nativa separada |
| Tablas, llaves primarias/foráneas, relaciones e índices apropiados | p. 9 | Catálogo normalizado: 14 PK, 17 FK y 25 índices; el catálogo histórico de doce tablas se conserva identificado |
| SELECT, WHERE, ORDER BY, DISTINCT | p. 9 | Código y [trazabilidad SQL](../../sprint1/postgres/evidencia_final_postgresql.md#trazabilidad-de-operaciones-sql-exigidas) |
| JOIN, INNER JOIN y LEFT JOIN | p. 9 | Consultas/vista contractual y evidencia nativa identificada en esa trazabilidad |
| GROUP BY, HAVING, COUNT, SUM, AVG, MIN y MAX | p. 9 | Consultas canónicas y complemento observado; separar fuentes, magnitudes y unidades |
| Subconsultas, CTE, funciones de ventana, fechas y consultas utilizando índices | p. 9 | PG07/PG08, SQL complementario y planes; no omitirlos por no ser otra lista de diez consultas |
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
| Modelo documental/NoSQL y justificación de su uso | p. 10 | Explicar desnormalización, estructuras variables y acceso por canal/fecha con ejemplos reales y esquema efectivo |
| Lecturas de sensores | p. 11 | `readings`: 748.889 observaciones; adaptación por canal lógico con sensor desconocido, pendiente de aceptación semántica |
| Eventos detectados | p. 11 | `derived_events`: 10.841; regla demo versionada, no eventos oficiales históricos |
| Alertas automáticas | p. 11 | `alerts`: 10.841 generadas automáticamente por el pipeline local; replay actual, sin notificación externa ni carácter oficial |
| Incidentes urbanos | p. 11 | `incidents`: 14.388 expedientes anonimizados de 2026, separados de enero de 2025 |
| Información dinámica no estructurada | p. 11 | **Parcial / cobertura pendiente de precisar**: existen `measurements` y `provenance` anidados y atributos opcionales; falta justificar qué ejemplos satisfacen la expresión. No se exige una colección llamada `dynamic_metadata` ni se cumple automáticamente por almacenar JSON |
| insertOne, insertMany, find, findOne, updateOne, updateMany y deleteOne | p. 11 | **PASS nativo actual** sobre `practica_crud`, con siete marcadores, comprobaciones y `readings` intacta |
| Filtros y operadores | p. 11 | MG01/MG02/MG10 y `$match`; parámetros y resultados nativos |
| Proyecciones y ordenamiento | p. 11 | `buscar()` y pipelines; salidas y planes MG01/MG10 |
| Agregaciones, agrupaciones y Aggregation Framework obligatorio | p. 11 | MG03/MG05–MG09 y generación `$project`/`$merge`; contraste con Python |
| Índices | p. 11 | **Verificado**: 13 índices en siete colecciones; plan MG01 selectivo y MG10 con recorrido de todo el tráfico; no afirmar optimización completa |
| Diez consultas obligatorias | p. 12 | **PASS técnico actual MG01–MG10**, con límites semánticos por consulta |
| Mínimo 500.000 documentos | p. 26, incorporado al avance por esta aclaración | **Verificado**: 748.889 lecturas observadas, sin sumar incidentes ni derivados |

Evidencia actual: [cierre técnico MongoDB](../../sprint1/mongodb/evidencia_final_mongodb.md)
y [resumen para Fernanda](../../sprint1/mongodb/evidencias/20261028T055755-3fea400d/RESUMEN_FERNANDA.md).
El PASS no sustituye la justificación documental ni la aceptación de las
adaptaciones. Primero precisar/documentar la cobertura de información dinámica;
no crear una colección o funcionalidad adicional por precaución.

## Aspectos transversales o pendientes de confirmación

| Aspecto | Clasificación y tratamiento en octubre |
|---|---|
| Fuentes, licencia, limpieza, IDs, fechas y consistencia SQL/Mongo | Transversal a los motores: documentar procedencia y reconciliación actual. Hay dos fuentes; no confundirlo con integración final de cuatro tecnologías |
| Vistas materializadas, particionamiento y optimización de objetivos generales (p. 2) | **Transversal o pendiente de confirmación para este avance**. La sección PostgreSQL sí exige vista, función, SQL avanzado e índices; una vista ordinaria no demuestra una materializada. No implementar materializadas/particiones por precaución |
| Big Data y «almacenamiento distribuido» dentro de Uso de MongoDB (p. 11) | Volumen acreditado; ejecución local aislada. **Componente distribuido transversal o pendiente de confirmación**: no presentar standalone como cluster ni deducir obligación confirmada de sharding/replica set para octubre |
| Autenticación, presentación en servidor compartido, backups y concurrencia de producción | Documentar el entorno probado y confirmar cualquier exigencia concreta de demostración. No atribuir esas condiciones adicionales al profesor sin evidencia |
| Sensor físico, instalación/estado demo, zonas y reglas de eventos/alertas | Pendiente de aceptación académica; mantener requisito y adaptación visibles, sin inventar vínculos ni resultados |
| Recomendaciones de bytes, escenarios avanzados o más de cinco millones de registros | No reemplazan los mínimos por motor ni crean automáticamente otra meta obligatoria para el 28/10 |

## Implementaciones que se dejan para noviembre

Por instrucción expresa, no iniciar ahora Hadoop/HDFS, MapReduce/Hive, Apache
Spark, pipelines o análisis distribuidos, dashboard completo, comparación final
entre cuatro motores ni funcionalidades exclusivas de la segunda entrega.
Su ausencia no constituye un bloqueo confirmado del Sprint 1.

Se conservan los contratos y referencias de arquitectura existentes para la
continuación de noviembre, sin afirmar integración distribuida ya ejecutada.

## Documentación y regla de cierre

La entrega debe reunir: este alcance; E-R/DDL/relaciones/índices y auditoría 3FN;
modelo y justificación documental MongoDB, incluidas sus cinco clases de
información; código oficial de las veinte consultas, SQL avanzado y siete CRUD;
resultados, parámetros, muestras, volúmenes, replay, reconciliación, hashes,
versiones, entorno y limitaciones. Separar fixtures, observaciones, derivados y
administración sintética. No adjuntar datasets privados ni credenciales.

Los mínimos por motor, las veinte consultas y la normalización 3FN tienen
evidencia técnica dentro de sus alcances declarados. La aceptación académica
global no está acreditada: permanecen las adaptaciones semánticas y la cobertura
parcial de información dinámica MongoDB. Su registro se conserva en la
[auditoría documental interna](AUDITORIA_DOCUMENTAL_SPRINT1.md), junto con los
límites de las pruebas negativas y la identificación de las evidencias históricas.
