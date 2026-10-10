# Fase 4 — Brechas y viabilidad del primer avance

**Estimaciones, no ejecución.** Hitos14/17/20/23/28oct2026 de P pp.4–5, no rúbrica docente independiente. Entrega25nov sí consta en E. Supuesto de capacidad:desde 10hasta23oct,4integrantes×2 horas productivas/día≈112 horas-persona brutas;80–96útiles al reservar coordinación. Disponibilidad real no confirmada. Esperas de proveedor/docente no acotadas y excluidas de bandas activas.

## Esfuerzo incremental estimado

| Trabajo restante | Madrid | NYC | Londres | Dependencia/complejidad |
|---|---:|---:|---:|---|
| Contrato, metadatos, limpieza, modelado compartido |10–16h |20–34h |16–28h |Madrid limpieza/integración media;NYC alta por conflictos/exposición;LCL limpieza media y geografía no resoluble |
| SQL Daniel:3FN/FK/index/consultas/vistas/funciones/tests |12–18h |14–22h |12–20h |Contrato, organismos, instalación/estado aprobados, inventario independiente |
| Mongo Kembly:BSON/CRUD/consultas/pipelines/índices |16–24h |18–28h |18–28h |Entorno autorizado, IDs/fechas/documentos/reglas alertas |
| ETL/lotes/conteos/backup+restore José |8–14h |10–18h |10–16h |Modelos aprobados/recursos;NYC adquisición extra, LCL otros meses |
| Informe, revisión cruzada, demo Fernanda+todos |8–12h |10–16h |8–12h |Resultados auténticos/modelos/matriz,20consultas |
| **Total horas-persona** |**54–84h** |**72–118h** |**64–104h** |No tiempo transcurrido ni benchmark;no espera externa ni Sprint2/complementos de todos los KPIs |

Las filas de brechas siguientes son un desglose orientativo, **no sumarlas otra vez** al total. Madrid cabe mejor en80–96h útiles si las condiciones se cierran14oct;NYC/Londres pueden exceder capacidad y dependen de esperas. Ninguna banda garantiza20/20.

Medido anteriormente:pico RSS offline948904KiB,42tests, conteos/planes SQL guardados. **No se midió tiempo de implementación/carga Mongo/backups o infraestructura remota.** PostgreSQL de prueba1GB/CPU1no acredita Compose estático512MiB/0,25CPU ni configuración efectiva Coolify. Capacidad/índices/disco/restore deben probarse después, no extrapolar.

## Clasificación de pendientes

C1=Datos reales disponibles, transformación pendiente;C2=Datos derivados de observaciones;C3=Datos sintéticos necesarios;C4=Fuente complementaria necesaria;C5=Decisión de modelado pendiente;C6=Confirmación del profesor necesaria;C7=Bloqueo técnico. Varias categorías pueden coexistir. **Ningún requisito tiene demostrada necesidad inevitable de C3**:NULL/fuente/alcance aprobado preceden a inventar datos.

## PostgreSQL: de 2/10verificadas a10/10funcionales

Ruta A:inventario histórico real de dispositivos con instalación/estado/operador. Ruta B:docente acepta canales/sitios, actividad/alta como consultas alternativas **explícitamente diferenciadas**. B no cambia alta de sitio a instalación real. Sin A/B PG03/06permanecen NO_CUMPLE aunque la consulta vacía ejecute. No existe limpieza que garantice20 atributos ausentes.

| Consulta | Pendiente y particularidades por ciudad | Clase | Horas activas estimadas / dependencia | Prueba de aceptación posterior |
|---|---|---|---|---|
| PG01: tipo |Categorías reales;aceptar canal. NYC solo EPA, Londres LAQN, no campañas/hogares |C1, C5, C6 |1–2;contrato |COUNT DISTINCT vs catálogo/version, identidad semántica |
| PG02: ubicación |Madrid cartografía/vigencia;EPA borough/CRS DOT;LAQN autoridad, LCL NULL |C1, C4, C5, C6 |1–3SQL+4–6GIS Madrid;fuente CRS |FK sin huérfanos, zona con fuente, UNKNOWN visible, no tarifa=zona |
| PG03: estado |Administrativo individual ausente en las3;inventario A o actividad en ventana B aceptada |C4, C2, C6 |2–4+espera indefinida;inventario/ventana |Fecha/estado acreditados o criterio aceptado;NULL≠inactivo, ausencia de campaña≠falla |
| PG04: organismo |Madrid gestor/vínculo;NYC operador EPA;LAQN owner/manager de sitio, no persona individual |C1, C4, C5, C6 |2–4+fuente;granularidad |Relación/cargo con evidencia, vigencia y desconocidos visibles |
| PG05: ranking de ubicación |Catálogo independiente, no conteo de lecturas como sensores |C1, C5, C6 |1–2;PG01/02 |Ranking/empates correctos, conteo no crece por nuevas lecturas |
| PG06: instalados por año |Todas instalación ausente;alta/apertura/primera lectura separadas |C4, C5, C6 |1–2query+espera fuente/aceptación |Solo DATE verificada oconsultaaltade sitio aprobada y rotulada, no fechas inventadas |
| PG07: sin actividad |Catálogo independiente Madrid/LAQN;NYC EPA requiere externo;universo/ventana justificados |C1, C4, C2, C5 |2–4+inventario;PG03 |NOT EXISTS sobre catálogo independiente, no0tautológico;sin muestra≠falla |
| PG08: zonas |CTE/rank funcional;zona/cobertura Madrid, borough EPA, autoridad LAQN |C1, C2, C5, C6 |1–2;PG02/05 |Conteos y DENSE_RANK empates vs referencia, pérdidas/exposición |
| PG09: vista |Patrón nativo ya probado;adaptar al contrato final |C1, C5 |0,5–1+tests;modelo |VIEW vs base;materializada/refresh aparte |
| PG10: función |Patrón probado;parámetros fecha/zona útiles |C1, C5 |0,5–1+tests;modelo |Función nativa, inputs NULL/rango/vacío, resultado esperado |

Cinco entidades:usuarios del equipo consentidos, organismo gestor/cargo documentado, ubicación/categoría/sensor según alcance;C1/C4/C5/C6. Incluido12–18h SQL Madrid, con diagrama3FN/PK/FK/índices/planes/materializada/partición justificados. Maestros pequeños+hechos reales, no100k sensores ni usuarios. PG09/10prueba03no equivale esquema final aprobado.

## MongoDB: de factibilidad a consultas nativas

Prerequisitos C1/C5/C7:entorno aislado autorizado/versión acordada, JSON/BSON desde QA real, ID estable y location/channel/catalog_version compartidos. Instante UTC solo cuando acreditado, reloj local explícito;índices únicos/lotes e idempotencia. Capturar conteos inserted/rejected/unique y countDocuments, checksum de valores/resultado vs original. No ocultar conflictos agregando el valor a PK.

| Consulta/operación | Qué falta y diferencias | Clase | Horas activas estimadas / dependencia | Evidencia requerida |
|---|---|---|---|---|
| MG01: sensor |Filtro canal real Madrid/EPA/LAQN, no hogar/campaña |C1, C5, C6 |0,5–1;colección/catálogo |find nativo, IDs/orden/valores vs raw |
| MG02: rango |Fechas BSON, clock, bordes [desde, hasta), H24/DST |C1, C5 |1–2;contrato temporal |Tests UTC/NULL/fronteras, conteos vs referencia |
| MG03: extremos |QA por variable/unidad;retener extremos/nulos |C1, C5 |0,5–1;QA |min/max nativos, not NULL=0, IQR no implica erróneo |
| MG04: críticos |Regla válida: unidad/duración/QA aprobada, no IQR crítico |C2, C5, C6 |2–4+espera aprobación |rule_version/inputs/severidad/bordes;evento derived no confirmado, umbral no elegido para fabricar un caso |
| MG05: alertas por zona |Sin fuente histórica;fuente oficial o emisión actual/replay aprobado |C4, C2, C5, C6 |2–4+busqueda4–8no garantizada |emitted_at actual/observed_at histórico, zona real, prueba de emisión, no vacío cumple |
| MG06: zonas |Promedio por unidad, Madrid zona acreditada, EPA boroughugh, LAQN autoridad, no LCL fino |C1, C2, C4, C5, C6 |1–2;PG02/time |$group vs Python, pesos, cobertura/NULL declarados |
| MG07: tipo |Categoría/variable/unidad, no media heterogénea |C1, C2, C5 |0,5–1;catálogo |Resultados por clase/unidad vs original |
| MG08: incidentes |Madrid 14388 expedientes/2NULL;NYC solicitud aceptada o NYPD;Londres TfL a auditar |C1, C4, C5, C6 |Madrid 1–2;otras3–6+adquisición |Una ID por incidente, detalle de persona separado, sin incident.sensor_id inventado, categoría UNKNOWN |
| MG09: aggregation |Diseño existe, no pipeline ejecutado |C1, C5, C7 |1–2;colección/índice |Aggregate/explain nativos/etapas/salida y referencia |
| MG10: filtros |AND canal/fecha/valor/QA, proyección/orden |C1, C5 |0,5–1;MG01/02/03 |Intersección de filtros/BSON correcto/explain |
| CRUD/index/schema/≥500k |Todos pendientes;alteración solo copias desechables |C1, C5, C7 |Incluido16–24h Mongo Madrid |insertOne/Many, find/findOne, updateOne/Many, deleteOne;variabilidad, idempotencia, índices,≥500k únicos, no atributos |

## Otros requisitos pendientes

- **Volúmenes:**100k SQL nativo actual C1/C5;500k Mongo Madrid/Londresdatos locales C1/C7, NYC adquisición real API C1/C4/C7;1M Spark Madrid normalización anual C1/C5, Londres histórico únicoC1, NYC descarga/QA C1/C4, ejecución distribuida todas C7.
- **Fuentes administrativas/cartografía/CRS/reloj:**C4/C5/C6, dictamen unidades meteo Madrid, CRS DOT, reloj LCL y catálogo independiente;nombre de columna/bbox no acredita CRS.
- **CO2/recorridos/energía horaria/alertas históricas:**C4/C6;búsqueda inicial4–8h sin garantía de hallazgo compatible, fuera del total si alcance completo adicional. CO/CO2e no concentración;no energía mensual dividida por horas. Energía LCLpor zona fina C4/C6, no coordenadas ficticias.
- **Usuarios/responsable:**C1/C5si cuentas consentidas/cargo documentado;vínculo gestor–sensor C4/C6. Hasta4cuentas demo opcionales serían synthetic solo autorizadas, namespace/demo@example.invalid,0generadas;no C3necesidad ni volumen.
- **HDFS/batch/Spark/UI:**C1/C2/C5/C7y KPI faltantes C4/C6;fuera del totalSprint1, asignar Sprint2 y probar1M, distribución, comparación anual y4gráficos, uno Spark real. No simplemente copiar archivo/Python.

## Fechas, dependencias y puertas por alternativa

Ruta crítica: **respuesta docente+aprobación fuentes/IDs →contrato14 →carga inicial17 →QA/conteos/backups20 →consultas semánticas/CRUD/planes23 →prueba cruzada24 →informe25 →freeze26/demo27 →avance28**. No dependencias externas cotizadas como«2h». Daniel/Kembly pueden trabajar en paralelo en borradores, no cerrar atributos por anticipado.

| Hito | Madrid | NYC | Londres |
|---|---|---|---|
|14contrato |Riesgo moderado bajo aceptación de canales/faltantes;cerrar meteo/zonas |Alto:DOT identidad/CRS, campañas y volumen |Alto:permisos/reloj/geografía de cohorte/TfL |
|17primera carga |Factible estimada, reutilización CSV de prueba;BSON por validar |SQL factible, Mongo requiere adquisición adicional |SQL factible, LCL otros meses/clock explícito, sin zona falsa |
|20mínimos/respaldos |Datos suficientes, recursos/restauración no probados |Alto:menos500k locales;únicos/versión/adquisición |Volumen amplio, index/QA/permisos aún pendientes |
|23cierre técnico |Moderado si PG03/06y MG04/05resueltos, si no NO20/20 |Alto si proveedor DOT/adquisición en ruta crítica |Alto por TfL/permisos/clock/alcance docente |
|28primer avance |Viable condicionado, doc/revisión8–12h previstas, no certificación |Condicionado con riesgo alto y posible exceso118h |Condicionado con riesgo alto/espera externa |

Después17evitar migrar núcleo completo;después 20cambio solo por bloqueo irreversible decidido por equipo/docente y plan revisado. Si23faltan consultas, documentar NO_CUMPLE/PARCIAL, no«listo»ni resultados ficticios. **No esquemas/cargas/remotos/Fase5implementados en esta fase.**
