# Las 20 consultas — Sprint 1

Esta matriz cubre las consultas, **no todo el avance**. El
[alcance confirmado](ALCANCE_CONFIRMADO_SPRINT1.md) incluye también modelos,
3FN, tablas/relaciones, índices, SQL avanzado, clases de documentos, siete
operaciones CRUD y Aggregation Framework. Lo transversal o ambiguo no se
convierte automáticamente en una implementación obligatoria para octubre.

**Ruta actual:** esquema `smartcity`, paquete local `expanded-v2-2025-01`.
La validación PostgreSQL normalizada corresponde a
`python scripts/validar_postgresql_3nf.py`; sus resultados están en
`sprint1/postgres/evidencias/3nf/`. La entrada
`bash scripts/validate_sprint1.sh --datos` reproduce la ruta v2 anterior y MongoDB,
con informes en `research/datasets/results/expanded-v2-2025-01/execution-*.json`.
No sustituye la validación del DDL normalizado. Un informe con error no acredita PASS.

SQL de entrega: `sprint1/postgres/queries_v2_3nf.sql`. El SQL anterior se conserva
para reproducir sus informes. [Cierre normalizado](../../sprint1/postgres/cierre_3nf.md):
PG01–PG10 completas contra Python, 748.889 lecturas y reconciliación. Mongo: `sprint1/basico/consultas_mongodb_v2.js`.
Las consultas no equivalen automáticamente a aceptación académica del alcance.

**Antecedente PostgreSQL:** [fichas PG01–PG10 y resultados v2](https://github.com/Alpizar28/SmartCity/blob/9d84a34e529a72b316c540bff549080c906b0126/sprint1/postgres/evidencia_final_postgresql.md),
[normalización formal](https://github.com/Alpizar28/SmartCity/blob/9d84a34e529a72b316c540bff549080c906b0126/sprint1/postgres/normalizacion_3fn.md) y
[PG07: pruebas y evidencia física requerida](https://github.com/Alpizar28/SmartCity/blob/9d84a34e529a72b316c540bff549080c906b0126/sprint1/postgres/pg07_limite_evidencia.md).
El PASS masivo PostgreSQL se cotejó con el paquete privado y un cálculo Python
independiente; tres reportes separan auditoría completa, SQL controlado y
subconjunto observado v2. Esos tres informes históricos no certifican el DDL
normalizado; su nueva evidencia se referencia arriba. Tampoco acreditan actividad física.

**Cierre MongoDB actual:** [MG01–MG10, CRUD, índices y límites](../../sprint1/mongodb/evidencia_final_mongodb.md).
`execution-d26e40706dcd.json` acredita PASS masivo de 748.889 lecturas; las diez
consultas fueron contrastadas con Python, con replay y limpieza. La reconciliación original usa el informe PostgreSQL previo. El nuevo cierre
normalizado vuelve a confirmar su huella contra esa misma ejecución MongoDB.
La [demostración académica aislada](../../sprint1/mongodb/academico/README.md)
complementa MG01 y MG07 con sensores, tipos y lecturas sintéticos; también
verifica texto narrativo, atributos heterogéneos y revisiones. Su ejecución
`20261028T161057-eff98453` tiene resultados completos contrastados con Python.
No se suma al volumen público ni altera las consultas históricas por canal y magnitud.

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
| MG01 | Lecturas de un sensor | `academico/consultas_demo.js: lecturasPorSensor`; sensor sintético explícito, dos documentos completos; canal público conservado como adicional. |
| MG02 | Lecturas por fechas | BSON Date; ventana semiabierta de enero en Madrid. |
| MG03 | Máximos y mínimos | Aire válido, separado por variable y unidad. |
| MG04 | Eventos críticos | Implementada: eventos derivados de intensidad >2.000 veh/h, regla demo no oficial. |
| MG05 | Alertas por zona | Implementada: emisiones actuales de replay a colección local, no avisos oficiales de 2025. |
| MG06 | Promedio por zona | Excluye zonas nulas; no acredita vigencia histórica del inventario. |
| MG07 | Promedio por tipo | `academico/consultas_demo.js: promediosPorTipo`; lectura–sensor–tipo, tres grupos sintéticos separados por magnitud/unidad; no dispositivos físicos acreditados. |
| MG08 | Incidentes por categoría | Implementada: accidentes reales de 2026, un documento por expediente anonimizado. |
| MG09 | Agregación | Conteos por fuente y calidad. |
| MG10 | Filtros múltiples | Fecha, fuente, flag, umbral y zona conocida. |

## Cómo se comprueban

- SQL normalizado: las diez consultas se comparan en todas sus filas con Python;
  el informe conserva conteos y huellas de resultados. Las pruebas controladas
  contrastan además los límites de PG07. Los informes históricos conservan sus
  muestras y alcances propios.
- Mongo: el informe guarda parámetros/resultados, no banderas constantes.
  `scripts/validar_v2.py` compara conteos, promedios, extremos, categorías y filtros
  con cálculos Python sobre los archivos verificados.
- Laboratorio: Python verifica los 18 documentos, MG01, MG07 y selecciones narrativas; el replay y 13 rechazos se registran con su mecanismo. Los códigos 121/11000 corresponden a validación/índices; referencias y unidades se comprueban en la aplicación.
- Ambas cargas deben conservar los mismos IDs/payloads que el ledger, reimportar
  sin duplicados y eliminar únicamente sus contenedores y volúmenes propios.

**Pendiente de datos:** PG07 no se cierra inventando que un sensor demo produjo
una lectura pública. La regla de eventos es un ejercicio, las alertas solo se
guardan localmente y las zonas no tienen vigencia histórica confirmada.
Estos alcances requieren revisión docente antes de afirmar cumplimiento académico.

La evidencia anual v1 conserva sus estados históricos (incluidas MG04/05/08
bloqueadas). No se reescribe: la nueva ejecución v2 aporta evidencia separada.
