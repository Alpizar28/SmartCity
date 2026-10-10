# Fase 5 — Volumen sin inflación ni síntesis masiva

| Fuente enero2025 | Registros/slots seleccionados | Elegibles estructurales únicos | Rechazados | Duplicados/conflictos |
|---|---|---|---|---|
| MAD-AIR | 93720 | 91959 | 1761 | 0/0 |
| MAD-METEO | 69408 | 66005 | 3403 | 0/0 |
| MAD-TRAFFIC | 677724 | 674704 | 3020 | 0/0 |

**832668 observaciones estructurales únicas de enero**, no993374 enero+julio. Tráfico conserva un documento por intervalo con variables juntas. Reglas precisas en manifiesto/prepare; no aumentar por raw diario+horas, atributos separados, cross products, fixtures o exportaciones redundantes.

| Objetivo | Disponible bruto | Elegible validado | Efectivamente probado en motor | Pendiente |
|---|---|---|---|---|
| PostgreSQL≥100000 |93720slotsaire+69408meteo+677724tráfico seleccionado |832668; solo tráfico674704 basta estructuralmente |5000 hechos en draft5;993374 en modelo local anterior, no reutilizar como carga nueva |Aceptar hechos como registros; unidad/clock/catálogos y carga autorizada después |
| MongoDB≥500000 |677724intervalos tráfico del estrato |674704,0duplicados/conflictos,3020flagsdesconocidos excluidos |5000documentos mixtos,3000tráfico; no500k |Margen174704=34,94%; clocks/tipo/granularidad y carga nativa masiva posteriores |
| Spark≥1000000 |1795279slotsVaire del histórico local2025–ago2026, más otros |No cardinalidad UTC/QA anual definitiva en esta fase; núcleoenero832668<1M |0registros ejecutados por Spark |Ampliar real al histórico, controlar DST/sitios/unidades/panel comparable y ejecutar distribuido |

Cantidad observada no es aceptabilidad científica plena: meteo66005 con unidadNULL; reloj provisional meteo/tráfico; ubicación histórica pendiente. Datos para sensores físicos estrictos: **0identidades acreditadas**, no674704sensores. No filtrar zonasNULL para aparentar precisión; si el contrato final las exige, recontar elegibles antes de prometer mínimos.

## Almacenamiento y estimaciones separadas

Cinco archivos originales principales/complementos de Madrid:145308605bytes de Fase4, distinto de bytes del núcleo restringido y almacenamientoDB. Cache y hashes privados en preparation.json. La muestra tiene tamaño medido JSON/CSV/Parquet; cualquier estimación de500k BSON/índices/disco parte de esta muestra y debe etiquetarse estimación, nunca benchmark remoto. No se aseguró funcionamiento en512MiB/0,25CPU del Compose estático; prueba local1GiB/1CPU.

En results/phase5/storage.json se separan bytes reales de sample y cache, promedioJSON y proyección lineal para674704documentos de tráfico. No incluye índices,WAL,buckets,réplicas,backups ni distribución. No sumar ledger+cache+exportación como nuevas mediciones. La ampliación histórica es procedimiento pendiente, no volumen anual normalizado ya acreditado.

**Síntesis de mediciones:0generada y0necesaria para potencialSQL/Mongo.** Para Spark ampliar fuentes reales antes de plantear síntesis. No hay necesidad demostrada de generador sintético; por eso no se generan semillas/distribuciones como solución aprobada. Si después faltan datos, presentar por separado modelo, semilla, restricciones/distribuciones/autocorrelación/unidades/origen y evaluación contra reales para autorización. Tres fixtures CRUD no métricos no cuentan como sensores, usuarios ni lecturas.
