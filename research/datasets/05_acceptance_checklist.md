# Fase 5 — Lista de aceptación de la fase, no de producción

| Criterio solicitado | Estado / evidencia |
|---|---|
| Contrato definido para revisión |Cumplido como borrador `madrid-draft-v1`; no ratificado |
| Origen/transformación/disponibilidad por atributo |DiccionarioCSV75entradas, fuente/versión y NULL explícitos |
| Modelos SQL/documental preliminares |DDL/consultas y diseños05; tablas físicas vacías y colecciones pendientes visibles |
| Estrategia devolumen justificada |832668elegibles estructurales enero y674704tráfico;5k nativas, no cargasmínimas definitivas |
| Pipeline inicial reproducible |Dry-run, preparación/lotes/cache/ledger/locks/ID/proveniencia/replay y exportaciónlimitada; ingestióncompleta/distribuida propuesta |
| Mongo nativo local si posible |True; versión7.0.43,5k,Aggregation Framework,CRUDdemo,índices/explain,cleanup |
| Prueba SQL adicional limitada |True;5k,DDL/FK/trigger/vistas/función,catálogos iguales;cleanup |
| Diferencias de fecha/granularidad |Enero conH24;accidentes2026 yenergíamensual separados;no CO2/recorridos ficticios |
| Aprobacionespendientes explícitas |Matriz05_academic_decisions y actapendiente cuatro/docente; clocks/unidades/CRS/inventarios no cerrados |
| Plan concreto Sprint1 |Handoff porintegrante ypuertas14/17/20/23/24–28oct |

Continuidad: las 48 pruebas anteriores fueron reproducidas (baseline_tests.xml). Pruebas finales heredadas+nuevas aprobadas: **82**, con cero fallos, errores u omisiones cuando el JUnit está aprobado. Conteo exacto y resultados en `results/phase5/tests.xml` y `final_checks.json`. Hashes de fases0–4 verificados, sin sobrescrituras. El primer enum incompleto de tipos de tráfico se conserva en superseded_type_filter.json: se corrigió URB antes de la prueba aceptada, no se descubrieron 611153 filas inválidas. La preparación anterior al ajuste de proveniencia es evidencia supersedida, no otra población.

**No producción:**faltan aprobación, estado/instalación/organismos/usuarios,meteo/clocks/geografía,MG04/05/08nativas,mínimos cargadosdefinitivamente,backup/restore,benchmarkremoto,HDFS/Spark/dashboard. No remoto,Coolify,Tailscale,cargamasiva,medicionessintéticasmasivas,commit/push/merge ni implementación definitiva. **Detenerse al finalizar Fase5.**
