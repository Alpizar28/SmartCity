# Checklist de cierre — Sprint 1 — 28/10/2026

Autoridad y requisitos completos: [alcance confirmado](ALCANCE_CONFIRMADO_SPRINT1.md).
La «Sección de PostgreSQL y MongoDB» no se reduce a veinte consultas y no incluye
implementar ahora los componentes exclusivos de noviembre.

| Frente | Estado | Evidencia / condición de cierre |
|---|---|---|
| PostgreSQL: mínimo 100.000 registros | Verificado también en modelo normalizado nuevo | 748.889 filas; `20261028T071812-55791345.json`, DTO sin diferencias y replay correcto |
| MongoDB: mínimo 500.000 documentos | Verificado en ejecución actual | 748.889 lecturas; `execution-d26e40706dcd.json`, con hashes y limpieza |
| Modelo E-R, entidades mínimas, tablas, PK/FK e índices | Documentado y probado con límites | [Cierre PostgreSQL](../../sprint1/postgres/evidencia_final_postgresql.md); mantener nulos, procedencia demo y restricciones efectivas visibles |
| Normalización hasta 3FN | **Verificada en DDL normalizado** | [Cierre 3FN](../../sprint1/postgres/cierre_3nf.md): catorce relaciones, cierres de DF, 748.889 lecturas y PG01–PG10 nativas |
| SQL básico, relacional, analítico y avanzado | Evidencia disponible | Trazabilidad SELECT/WHERE/ORDER/DISTINCT/JOIN/GROUP/HAVING/agregados/subconsultas/CTE/ventanas/fechas/índices del cierre PostgreSQL |
| PG01–PG10, vista y función | Ejecución técnica verificada; límites semánticos | [Matriz](MATRIZ_CONSULTAS_SPRINT1.md); PG07 sin vínculo físico acreditado; no declarar cumplimiento físico total |
| Modelo documental/NoSQL y cinco clases de información MongoDB | Documentado parcialmente | Lecturas, eventos, alertas e incidentes con evidencia; falta precisar/justificar información dinámica no estructurada y la flexibilidad del modelo |
| MG01–MG10, filtros, proyecciones, orden y Aggregation Framework | PASS técnico actual | [Resumen MongoDB](../../sprint1/mongodb/evidencias/20261028T055755-3fea400d/RESUMEN_FERNANDA.md), con adaptación canal/tipo de medición y reglas demo |
| Siete operaciones CRUD | PASS nativo actual | `practica_crud` aislada; `readings` permanece en 748.889; colección de práctica eliminada |
| Índices/validadores MongoDB | Configuración y planes capturados | 13 índices; cuatro colecciones con validador, tres administrativas sin él; no equivale a pruebas negativas/autenticación |
| Replay y consistencia entre motores | Reconciliación actual verificada | Conteo y huella iguales; referencia PostgreSQL previa y ejecución MongoDB nueva identificadas por hash |
| Fuentes y administración sintética | Procedencia documentada; aceptación semántica separada | Aire/tráfico reales; 1 organización, 5.133 usuarios y 5.133 sensores demo. La [autorización](EVIDENCIA_AUTORIZACION_DATOS_SINTETICOS.md) no autoriza mediciones inventadas ni prueba sensores físicos |
| Vistas materializadas, particiones y componente distribuido MongoDB | **Transversal o pendiente de confirmación** | Tratamiento explícito en el alcance; no implementarlos por precaución |
| Informe y evidencias de ambas secciones | Integrados; cierre documental registrado por separado | PDF revisado y manifiesto de revisión; [auditoría interna](AUDITORIA_DOCUMENTAL_SPRINT1.md). La auditoría académica general conserva los límites abiertos |
| Servidor compartido / autenticación de clientes | Entorno de demostración pendiente de confirmar | No acreditados por los contenedores desechables; no son cargas compartidas ejecutadas |
| Hadoop/HDFS, Spark, dashboard, análisis distribuidos y comparación final | **Fuera de la implementación actual** | Continuación de noviembre; no bloquear el avance por su ausencia |

## Regla de cierre

No declarar ambas secciones académicamente completas mientras haya requisitos
explícitos pendientes, como la justificación de información dinámica, o
adaptaciones semánticas sin aceptar. Distinguirlos de las pruebas técnicas ya
aprobadas y de los puntos transversales por confirmar.

La ausencia de Hadoop/Spark/dashboard o comparación final no es un bloqueo
confirmado del avance del 28/10. Los resultados anuales v1 y los FAIL previos se
conservan como antecedentes, sin reemplazar la evidencia v2 actual.
