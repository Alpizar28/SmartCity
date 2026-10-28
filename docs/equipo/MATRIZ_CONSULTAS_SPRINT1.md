# Las 20 consultas — Sprint 1

**Ruta actual:** esquema `smartcity`, paquete local `expanded-v2-2025-01`.
Ejecutar `bash scripts/validate_sprint1.sh --datos`. El estado de la carga está
en `research/datasets/results/expanded-v2-2025-01/execution-*.json`;
un informe con error no cuenta como ejecución aprobada.

SQL: `sprint1/postgres/queries.sql`. Mongo: `sprint1/basico/consultas_mongodb_v2.js`.
Las consultas no equivalen automáticamente a aceptación académica del alcance.

| ID | Consulta | Datos y límite |
|---|---|---|
| PG01 | Sensores por tipo | Entidades administrativas sintéticas autorizadas. |
| PG02 | Sensores por ubicación | Sensores demo ligados al catálogo de estaciones. |
| PG03 | Cantidad de activos/inactivos | Estados demo; NULL permanece desconocido. |
| PG04 | Sensores por organismo | Organismos demo; incluye organismos sin sensores. |
| PG05 | Ubicaciones con más sensores | Ranking de inventario demo. |
| PG06 | Sensores instalados por año | Fechas demo; se excluyen fechas desconocidas. |
| PG07 | Sensores sin actividad | SQL probado; no evaluable en datos observados sin relación sensor–canal. |
| PG08 | Ranking de zonas monitoreadas | Sensores demo y distritos del inventario disponible. |
| PG09 | Consulta con vista | `channel_activity` sobre lecturas reales. |
| PG10 | Consulta con función | `channels_at_station()` cuenta canales, no dispositivos físicos. |
| MG01 | Lecturas de un sensor | Alternativa por canal lógico con snapshot explícito. |
| MG02 | Lecturas por fechas | BSON Date; ventana semiabierta de enero en Madrid. |
| MG03 | Máximos y mínimos | Aire válido, separado por variable y unidad. |
| MG04 | Eventos críticos | Implementada: eventos derivados de intensidad >2.000 veh/h, regla demo no oficial. |
| MG05 | Alertas por zona | Implementada: emisiones actuales de replay a colección local, no avisos oficiales de 2025. |
| MG06 | Promedio por zona | Excluye zonas nulas; no acredita vigencia histórica del inventario. |
| MG07 | Promedio por tipo | Por fuente/variable/unidad; no por dispositivo físico acreditado. |
| MG08 | Incidentes por categoría | Implementada: accidentes reales de 2026, un documento por expediente anonimizado. |
| MG09 | Agregación | Conteos por fuente y calidad. |
| MG10 | Filtros múltiples | Fecha, fuente, flag, umbral y zona conocida. |

## Cómo se comprueban

- SQL: el informe guarda cantidad de filas y muestra de cada consulta. La prueba
  controlada independiente contrasta resultados esperados y los límites de PG07.
- Mongo: el informe guarda parámetros/resultados, no banderas constantes.
  `scripts/validar_v2.py` compara conteos, promedios, extremos, categorías y filtros
  con cálculos Python sobre los archivos verificados.
- Ambas cargas deben conservar los mismos IDs/payloads que el ledger, reimportar
  sin duplicados y eliminar únicamente sus contenedores y volúmenes propios.

**Pendiente de datos:** PG07 no se cierra inventando que un sensor demo produjo
una lectura pública. La regla de eventos es un ejercicio, las alertas solo se
guardan localmente y las zonas no tienen vigencia histórica confirmada.
Estos alcances requieren revisión docente antes de afirmar cumplimiento académico.

La evidencia anual v1 conserva sus estados históricos (incluidas MG04/05/08
bloqueadas). No se reescribe: la nueva ejecución v2 aporta evidencia separada.
