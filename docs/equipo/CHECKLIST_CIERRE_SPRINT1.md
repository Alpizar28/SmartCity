# Checklist de cierre — Sprint 1 — 28/10/2026

Autoridad y requisitos completos: [alcance confirmado](ALCANCE_CONFIRMADO_SPRINT1.md).
La «Sección de PostgreSQL y MongoDB» no se reduce a veinte consultas y los componentes exclusivos de noviembre
corresponden a la continuación del proyecto.

| Frente | Estado | Evidencia / condición de cierre |
|---|---|---|
| PostgreSQL: mínimo 100.000 registros | Verificado también en modelo normalizado nuevo | 748.889 filas; `20261028T071812-55791345.json`, DTO sin diferencias y replay correcto |
| MongoDB: mínimo 500.000 documentos | Verificado en ejecución actual | 748.889 lecturas; `execution-d26e40706dcd.json`, con hashes y limpieza |
| Modelo E-R, entidades mínimas, tablas, PK/FK e índices | Documentado y probado con límites | [Modelo normalizado vigente](../../sprint1/postgres/cierre_3nf.md); nulos, procedencia demo y restricciones efectivas documentados |
| Normalización hasta 3FN | **Verificada en DDL normalizado** | [Cierre 3FN](../../sprint1/postgres/cierre_3nf.md): catorce relaciones, cierres de DF, 748.889 lecturas y PG01–PG10 nativas |
| SQL básico, relacional, analítico y avanzado | Evidencia disponible | [Cierre normalizado y SQL avanzado](../../sprint1/postgres/cierre_3nf.md); trazabilidad SELECT/WHERE/ORDER/DISTINCT/JOIN/GROUP/HAVING/agregados/subconsultas/CTE/ventanas/fechas/índices |
| PG01–PG10, vista y función | Ejecución técnica verificada; límites semánticos | [Matriz](MATRIZ_CONSULTAS_SPRINT1.md); PG07 sin vínculo físico acreditado; sin acreditación de cumplimiento físico total |
| Modelo documental/NoSQL y cinco clases de información MongoDB | Demostraciones documentadas con procedencia separada | Siete colecciones oficiales; laboratorio con texto libre, atributos variables y revisiones contrastadas con Python; diagrama oficial y laboratorio separados |
| MG01–MG10, filtros, proyecciones, orden y Aggregation Framework | Evidencia pública conservada y complemento académico PASS | MG01 por sensor y MG07 por tipo en [laboratorio sintético](../../sprint1/mongodb/academico/README.md); demás consultas conservadas, con reglas demo y límites territoriales |
| Siete operaciones CRUD | PASS nativo actual | `practica_crud` aislada; `readings` permanece en 748.889; colección de práctica eliminada |
| Índices/validadores MongoDB | Configuración y planes capturados | 13 índices; cuatro colecciones con validador, tres administrativas sin él; no equivale a pruebas negativas/autenticación |
| Replay y consistencia entre motores | Reconciliación actual verificada | Conteo y huella iguales; referencia PostgreSQL previa y ejecución MongoDB nueva identificadas por hash |
| Fuentes y administración sintética | Procedencia documentada; aceptación semántica separada | Aire/tráfico reales; 1 organización, 5.133 usuarios y 5.133 sensores demo. La [autorización](EVIDENCIA_AUTORIZACION_DATOS_SINTETICOS.md) no autoriza mediciones inventadas ni prueba sensores físicos |
| Vistas materializadas y particiones PostgreSQL | Pendiente de aclaración de alcance | No implementados; exigencia para este avance pendiente de aclaración docente |
| Almacenamiento distribuido MongoDB | **Requisito explícito sin demostración** | Standalone no lo acredita; modalidad suficiente pendiente de aclaración docente. No se demostraron replica set ni sharding |
| Informe y evidencias de ambas secciones | Integrados; cierre documental registrado por separado | [PDF y manifiesto vigentes](../README.md#informe-del-avance-en-latex); los cierres técnicos conservan los límites abiertos |
| Servidor compartido / autenticación de clientes | Entorno de demostración pendiente de confirmar | No acreditados por los contenedores desechables; no son cargas compartidas ejecutadas |
| Hadoop/HDFS, Spark, dashboard, análisis distribuidos y comparación final | **Fuera de la implementación actual** | Continuación de noviembre; su ausencia no constituye un bloqueo confirmado de este avance |

## Regla de cierre

Ambas secciones conservan requisitos académicos explícitos pendientes, como el
almacenamiento distribuido MongoDB, por lo que no se acredita aceptación académica
global. Las demostraciones sintéticas mantienen su procedencia y no acreditan
dispositivos físicos. Estos límites se distinguen de las pruebas técnicas
satisfactorias y de los puntos transversales por confirmar.

La ausencia de Hadoop/Spark/dashboard o comparación final no es un bloqueo
confirmado del avance del 28/10. Los resultados anuales v1 y los FAIL previos se
conservan como antecedentes, sin reemplazar la evidencia v2 actual.
