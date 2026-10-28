# MongoDB — entrega v2 y núcleo de práctica

El [cierre técnico vigente](evidencia_final_mongodb.md) integra la ejecución
pública v2 y el laboratorio académico del paquete A, con evidencias separadas.
La entrega utiliza `sprint1/basico/cargar_mongodb_v2.js`,
`consultas_mongodb_v2.js` y `crud_mongodb.js`. La
[evidencia nativa v2](evidencia_final_mongodb.md) comprende 748.889 lecturas,
diez consultas, eventos y alertas derivados, incidentes anonimizados y CRUD aislado.
Sus resultados no acreditan sensores físicos. El [laboratorio académico](academico/README.md)
aporta MG01 por sensor, MG07 por tipo y recuperación de texto libre con datos
enteramente sintéticos, versión propia y evidencia adicional. Las consultas
públicas por canal/magnitud y sus hashes se conservan. El almacenamiento
distribuido requerido en la sección MongoDB sigue sin demostración.

## Núcleo complementario de práctica

Los archivos `validator.js`, `indexes.js`, `queries.js` y `staging.js` de esta
carpeta pertenecen al núcleo de práctica descrito a continuación. Sus límites
no representan el estado de implementación de v2.

Importar los módulos CommonJS no crea colecciones, índices ni documentos.
`stageReading` escribe solo cuando se invoca con colecciones explícitas.
MongoDB 7.0.16 y BSON nativo se probaron en contenedor local desechable con tres
ejemplos publicados mediante `scripts/test_sprint1_engines.py`.

| Consulta | Propuesta | Límite |
|---|---|---|
| MG01/10 | `channelReadings` | Canal lógico, snapshot y calidad; parcial respecto a sensor físico |
| MG02/03 | `airRange`, `airExtrema` | Solo aire acreditado, canal/snapshot y fechas semiabiertas |
| MG07 | Agrupación de aire en `airExtrema` | Variable/unidad, no tipo físico; parcial |
| MG09 | `qualityCounts` | Conteos por canal/calidad comprobados en el motor |
| MG04/05/06/08 | Sin implementación en este núcleo | Funcionalidades disponibles por separado en la ruta v2, con sus límites documentados |

`validator.js` propone `$jsonSchema` más controles de evidencia y hash de fuente.
La aplicación debe ejecutar además el validador Python y validar catálogos:
MongoDB no impone FK entre colecciones. El esquema BSON no comprueba por sí solo
IDs canónicos, finitud numérica, reloj, fingerprint ni QA interna de tráfico.

`ReadingDTO.mongo_document()` transforma `observed_at: {"$date": "...Z"}` validado
en `datetime` UTC listo para codificación BSON por un futuro driver, y deja que
Mongo asigne un ObjectId **interno de staging**. No copiar
`measurement_id`/`_id` históricos ni reetiquetar documentos automáticamente.
La huella se calcula antes de esa conversión; el ObjectId y la clave local de
staging no integran el payload. El harness comprueba insertOne/insertMany/find/
findOne/updateOne/updateMany/deleteOne; las modificaciones y borrados se limitan
a `crud_scratch`, nunca a las lecturas aceptadas.

Los índices no contienen 2dsphere ni unicidad UTC. No se usa un índice único sobre
`source_key` array: sería multikey, no unicidad de la tupla completa. Se añade un
índice único **escalar** sobre `staging_key`, la serialización canónica de
fuente/snapshot/canal/clave original, creada por el DTO. Es un localizador de
reconciliación, no un ID científico. `stageReading` intenta insertar, captura
solo duplicados 11000 y compara huellas: replay o cuarentena, nunca sobrescritura.
Requiere lecturas append-only e índice/validador instalados. La cuarentena es una
escritura separada; si falla debe reintentarse la operación y no declararse éxito.
Se comprobó backup/restore lógico de documentos/tipos BSON, validadores e índices;
no estrés concurrente ni durabilidad tras reinicio. Véase [respaldos](../RESPALDOS.md).
Límites y
paginación de resultados siguen pendientes de la futura capa de aplicación.
