# Checklist de cierre — Sprint 1

| Frente | Estado | Evidencia / siguiente condición |
|---|---|---|
| Carga PostgreSQL completa | completado | `results/expanded-2025/postgresql_full.json`; 1.076.813 observaciones reales. Debe regenerarse si cambia el cargador. |
| Carga MongoDB completa | completado | `results/expanded-2025/mongodb_full.json`; 1.076.813 lecturas reales. Debe regenerarse si cambia el cargador. |
| Entidades administrativas | completado | 1 organización, 5.133 usuarios y 5.133 sensores deterministas con `data_origin=synthetic`. |
| Autorización docente | completado | [EVIDENCIA_AUTORIZACION_DATOS_SINTETICOS.md](EVIDENCIA_AUTORIZACION_DATOS_SINTETICOS.md). No autoriza mediciones inventadas. |
| Evidencia de PG/MG | en curso | `MATRIZ_CONSULTAS_SPRINT1.md`; regenerar los informes de ambos motores tras añadir `query_evidence`. |
| Segunda fuente real (tráfico) | requiere aprobación | [PROPUESTA_MADRID_DRAFT_V2.md](../decisiones/PROPUESTA_MADRID_DRAFT_V2.md) requiere aprobación explícita de contrato, alcance URB/M30, migración aislada y semántica de integración antes de aceptar o cargar datos. |
| Spark/Hadoop | pendiente fuera de este cambio | Requisito separado si la rúbrica lo exige. |
| CI pública | en curso | Workflow sin datos privados en `.github/workflows/validate.yml`. |

## Regla de cierre

No declarar Sprint 1 completo mientras el requisito de segunda fuente o Spark permanezca obligatorio en la rúbrica y no tenga evidencia ejecutada. No reemplazar ese requisito con entidades administrativas sintéticas.
