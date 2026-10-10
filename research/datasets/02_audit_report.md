# Fase 2 — Auditoría real de tres alternativas

**Auditoría ejecutada; sin ganador, sin esquemas finales y sin fase 3.** Existen pruebas descargadas y analizadas de las ocho fuentes principales. La viabilidad del proyecto completo sigue **condicionada** para las tres alternativas: la auditoría no acredita atributos que no existen.

## Alcance, descarga y trazabilidad

Se releeron todos los entregables 00/01, README y bitácora antes de programar; se inspeccionó Python y se creó un entorno aislado (Python 3.11.16). No se modificaron los documentos previos; hashes en `results/prior_files_hashes.json`. Los requisitos confirmados son 10 consultas PG, 10 Mongo, 100k PG / 500k Mongo / 1M Spark y dos fuentes; no se ejecutaron motores de datos. No surgió una contradicción académica que requiriese reabrir los PDF oficiales.

**12 fuentes de observaciones/reportes descargadas y analizadas**, ocho principales y cuatro complementarias: energía e incidentes Madrid, LL84 NYC y DfT Londres. **Cuatro inventarios adicionales**: aire, meteo y puntos de tráfico Madrid; sitios LAQN. Total: 16 fuentes perfiladas. Un ZIP con cuatro CSV LCL no se cuenta como cuatro fuentes independientes; dos ventanas por sitio LAQN siguen siendo la misma fuente.

Transferencia de cuerpos realmente leídos: **311 375 862 bytes (311.38 MB decimales)**, incluyendo prefijos, errores, reintentos y documentación. Límite 1 000 000 000 bytes, restante 688 624 138. Esto no cuenta overhead TLS/TCP ni dependencias Python; estas últimas tampoco acercan el total al límite. Manifiesto con 168 intentos y 165 archivos cuyos SHA/tamaños se verificaron. Las solicitudes Range completas tienen `complete_response=True`, **no significa dataset completo**. La integridad de EPA ensamblado y de cada miembro LCL está documentada separadamente en `02_artifact_manifest.csv`.

Fechas reales UTC del manifiesto: 2026-10-10T02:33:49.865853+00:00–2026-10-10T03:51:14.359477+00:00. Los logs usan hora local del sistema. Se preservaron respuestas sin alteraciones en `raw/` ignorado; Parquet, joins y SQLite de cardinalidad en `private_results/` ignorado. No se redistribuyen lecturas LAQN ni solicitudes individuales 311.

## Muestreo progresivo

- **A:** prefijos 4–8 KiB, metadatos y licencias. Se cotejó parseo, cabecera y tipo real, no solo HTTP.
- **B Madrid:** enero y julio **2025**, todas las estaciones/variables publicadas; tráfico completo enero 2025, muestra determinista de puntos con `id % 20 == 0` a lo largo de los 31 días. No representa todas las vías uniformemente: ID no es aleatorio y distribución por distrito puede sesgarse.
- **B NYC:** todos los conteos 2023 en páginas de 10k (85 106 filas), EPA todo 2023 filtrado por estado/condado; 311 16 días completos, semana consecutiva 6–12 enero más días 1/8/15/22/29 de enero/julio. Se amplió esa semana tras medir baja coincidencia de campañas. El patrón inicial favorece domingos en enero/sábados en julio: **no extrapolar frecuencias de categorías como si fuera muestra aleatoria**. Campos proyectados omiten direcciones/narrativas innecesarias.
- **B Londres:** NO2 horario, cinco sitios LAQN y dos meses completos (enero/julio 2013); energía de todos los hogares presentes en enero/julio en cuatro miembros completos iniciales del ZIP. Selección de hogares no aleatoria, no equivalente a muestra representativa de todo Londres.
- **C:** CSV Madrid completos (aire/meteo 2025–agosto 2026), ZIP tráfico completo, ZIP EPA nacional ensamblado por rangos y procesado por chunks, cuatro miembros LCL completos con CRC. Nunca se descargó el ZIP LCL completo (~796 MB).

EPA tuvo una interrupción tras 11 862 016 bytes durante la descarga monolítica inicial; ese registro no tiene `error` relleno debido a una excepción de urllib3 anterior a la corrección del manejador, pero `complete_response=False` y el log acreditan el fallo. Se continuó mediante rangos verificables de 1 MiB, con tres desconexiones transitorias/reintentos. No se declaró válido el ZIP hasta ensamblarlo y leer el miembro completo validando CRC. Se añadieron captura de excepciones de transporte y nombres de archivo inmutables por intento. No hubo evasión de restricciones.

## Registros efectivos y calidad de las muestras normalizadas

Cada fila de Madrid H01–H24 es una observación horaria distinta publicada, no sintética; no se cuentan a la vez fila diaria y 24 horas como 25 mediciones. Los números de esta tabla son **muestras normalizadas**, no filas de todos los archivos.

| Fuente | Observaciones muestra | Entidades de la fuente | Valor ausente/no numérico | Extras de clave duplicada | Coordenadas válidas de observaciones |
|---|---:|---:|---:|---:|---:|
| MAD-AIR | 187 464 | 23 | 0 | 0 | 100.00% |
| MAD-METEO | 138 960 | 26 | 0 | 0 | 100.00% |
| MAD-TRAFFIC | 677 724 | 242 | 0 | 0 | 99.56% |
| NYC-COUNTS | 85 106 | 150 | 0 | 4 767 | 0.00% |
| NYC-AIR | 38 290 | 9 | 0 | 0 | 100.00% |
| NYC-311 | 124 130 | 124 130 | 0 | 0 | 98.52% |
| LON-AIR | 7 440 | 5 | 117 | 0 | 100.00% |
| LON-ENERGY | 347 547 | 120 | 0 | 233 | 0.00% |

`entity` no implica sensor físico: en DOT es campaña/segmento/dirección; en LCL hogar anónimo; en 311 solicitud. En `02_quality_metrics.csv` se encuentran atributos originales, tipos inferidos/declarados, nulos, cardinalidad y estadísticas. Los JSON `*-summary.json` contienen estadísticas por variable/unidad, flags y geografía; `*-coverage.csv` contienen series por canal/mes, huecos, duplicados y frecuencia observada. Para 311 son eventos por zona/día, **no una cadencia esperada de sensor**. Cobertura temporal calculada entre primeros/últimos puntos de cada canal/mes no equivale a cobertura del mes completo ni de la red entera.

### Madrid

- Aire: 76 513 filas diarias, 1 836 312 slots reales, 23 estaciones y 126 pares estación/magnitud; 1 795 279 slots V, 41 030 N y 3 M. Cero duplicados de clave diaria; cero referencias de estación ajenas al inventario actual. Los invalidantes permanecen en raw, incluso cuando el valor es 0.
- Meteo: 56 383 filas, 1 353 192 slots, 26 estaciones/94 pares; 1 333 092 V y 20 100 N. `PUNTO_MUESTREO` **100% vacío**, por lo que no es clave válida; usar namespace/red + estación/magnitud/fecha/hora. Los inventarios explicitan VV81/DV82/T83/HR86/PB87/RS88/P89. Las unidades meteo del normalizador son contrato provisional a cerrar con diccionario técnico; no declarar toda unidad validada solo por el rótulo del inventario.
- **Tráfico accesible:** los antiguos recursos 161/160 ahora devolvieron ZIP 200/prefijos válidos; el recurso 137 da 404. Se escogió el recurso 73, enero de 2025, del catálogo oficial para coincidir con aire/meteo. ZIP de 93 223 315 bytes, 13 218 804 filas y 4 701 puntos; miembro CSV leído completamente con CRC. Muestra por estrato de ID: 677 724 intervalos, cero duplicados de (id, fecha, tipo). `periodo_integracion` varía **1–30 minutos**: no es siempre 15. Intensidad es tasa veh/h, no conteo; la integración solo usa promedio de señal, no total de vehículos.
- Inventario de tráfico: 5083 IDs únicos; en muestra normalizada 242 puntos, parte no localizada en inventario vigente. El join cartográfico usa columnas decimales publicadas; se conservan UTM y ETRS89 originales. No se inventan distritos ambientales ni se transforma un punto cercano en la misma estación.
- Energía municipal: 35 803 filas; ID de edificio vacío en 65,553%, GRUPO vacío en 91,649%, consumo ausente en 0,053%. Hay 100 extras bajo una clave candidata que incluye campos opcionales: **no prueba de 100 mediciones duplicadas**. Replantear clave/jerarquía antes de sumar. Consumo mensual y unidades heterogéneas.
- Accidentes 2026: 33 322 filas de detalle y 14 388 expedientes únicos; 18 934 repeticiones del expediente esperables en personas/vehículos, no duplicados de incidente. No se emparejan con enero de 2025 como si coincidieran.

### Nueva York

- DOT 2023: 85 106 filas, 127 segmentos/150 canales campaña-segmento-dirección; 80 339 claves temporales únicas. **4 767 grupos con dos valores distintos**, incluso agregando WKT; cero filas completas idénticas. No se resolvieron sumando/escogiendo arbitrariamente: 9 534 filas se excluyen solo del join conservador, no de raw. Quedan 75 572 observaciones no ambiguas.
- EPA 88101: 9 350 315 filas nacionales examinadas en streaming, 104 903 del estado de Nueva York, **38 290 NYC** y cinco sitios. Solo condados 005 (Bronx), 047 (Brooklyn), 081 (Queens); **cero registros Manhattan/Staten Island para este parámetro/archivo**, no ausencia de toda la red EPA. Todas las unidades son µg/m³ (LC), datum WGS84. **Cero duplicados reales** de clave canal/fecha UTC. Hay 1 792 filas con qualifier; 36 498 observaciones numéricas/sin qualifier se usan conservadoramente. Un qualifier no significa automáticamente medición inválida: exclusión provisional para join, no borrado. La validación detectó que quitar timezone antes de comprobar claves producía cinco falsos duplicados el 5 de noviembre; se corrigió conservando UTC y se añadió regresión DST. Las dos horas locales 01:00 son instantes distintos, no conflictos de la fuente.
- PM2.5 máximo: 412 µg/m³; 1 999 candidatos IQR. No se eliminó el extremo ni se afirmó causa; distinguir un episodio ambiental real de error requiere QA/publicador. Concentración de CO₂ no existe aquí.
- 311: **124 130 solicitudes únicas auditadas**, 16 fechas; 149 casos con `closed_date` anterior a `created_date`; coordenadas ausentes en 1,477%. Son problemas/semántica de trámites a revisar, no estado de sensores. Categorías y agencias reales en `NYC-311-categories.json`; se agregan sin afirmar que todos los reportes sean eventos confirmados.
- WKT proyectado DOT: EPSG 2263→4326 como **hipótesis**; 85 106 puntos quedan en un bbox plausible, pero falta declaración oficial de CRS. Los adjuntos referenciados por assetId dieron 404 en la ruta probada. El join aceptado utiliza borough publicado, no esa transformación sin confirmar.
- Energía LL84: 200 reportes de 2023 perfilados; dos extras de (propiedad, año), granularidad anual. El esquema declara electricidad kWh/kBtu y emisiones CO₂e. La búsqueda oficial «hourly energy» devuelve principalmente LL84 anual, no una fuente horaria urbana acreditada. No convertir consumo anual en lecturas horarias.

### Londres

- LAQN: 7 440 slots NO2 de cinco sitios; 117 vacíos (1,57%), cero duplicados. Cinco sitios abiertos antes de 2013, ninguno cerrado antes del período. Dos valores negativos hasta −0,5 µg/m³ conservados como señales QA/instrumentales por revisar, no errores borrados. `Latitude/Longitude` plausibles; campos llamados `LatitudeWGS84` contienen metros/proyección y **no se interpretan como grados**. Apertura/cierre de sitio no es fecha de instalación del analizador.
- LCL: **4 000 000 filas efectivamente leídas**, 121 hogares en cuatro miembros, rango 2011-12-06 13:00:00–2014-02-28 00:00:00; 119 valores no numéricos/ausentes, cero negativos. Cardinalidad exacta en SQLite local: **3 997 252 claves hogar/timestamp**, 2 748 extras. No se afirmó CRC/integridad del ZIP entero: solo miembros extraídos completos, tamaño/CRC/SHA verificados. El último miembro truncado del prefijo no se analizó.
- Enero/julio: 347 547 filas, 120 hogares; 233 extras idénticos, cero conflictos de valor, 347 314 intervalos únicos. Al integrar se deduplican idénticos sin modificar fuente y se rechazan 44 horas/hogar incompletas. No hay coordenadas/borough de hogar: integración fina **fallida (0%)**. Cohorte total no es consumo total de Londres.
- DfT: 100 filas complementarias de 2013 analizadas, 32 columnas, sin duplicados de (punto, fecha, hora, dirección); 16 956 registros del filtro según API previa. Es muestra inicial de acceso/esquema, **no muestra representativa de 30 días**; conteos de campañas, no monitoreo diario ni velocidad.

## Resultados de integración

Madrid aire–meteo: **19 087 pares sitio/hora**, 56.44% de observaciones NO2 elegibles; en sitios co-localizados, 99.94% de coincidencia temporal. Tráfico–aire: 13 918 grupos en radio exploratorio de 1 km; 31.67% de los puntos elegibles y 98.76% de grupos temporales relacionados. No equivalencia dispositivo/estación.

NYC DOT–EPA: **146/322 borough/día**, 45.34%. DOT–311: 11/322 grupos, 3.42%; las tres fuentes simultáneas: 1 grupo (0.31%). No confundir este bajo porcentaje con imposibilidad de obtener 311 más días: limita la muestra.

Londres: **1 488/1 488 horas coincidentes (100%)**, 744 de enero y 744 de julio; ciudad/contexto de procedencia, **0% correspondencia hogar→zona fina**. Enero GMT es plausible; julio exige confirmar timezone LCL (o estudiar desplazamiento de una hora). La coincidencia numérica sin timezone acreditada no prueba sincronización real.

Detalle de reglas, denominadores, pérdidas y fallos en `02_integration_results.md` y `*-integration.json`; filas integradas reproducibles pero ignoradas por Git. Sin producto cartesiano ni enlacesficticios.

## Validación y estado

22 pruebas, 0 fallos, 0 errores; evidencia JUnit `results/tests.xml`, pruebas de presupuesto/reintentos/403/ZIP/CRC/granularidad/duplicados/geografía/joins. `verify.py` valida hashes, presupuesto y conservación de fases anteriores. Proceso completo offline por chunks de 100k; pico RSS de la ejecución completa en `results/runtime.json`. No es benchmark de Spark ni estimación de recursos Coolify.

Madrid: **auditable, condicionado** por QA/unidades, inventarios vigentes y KPIs sin fuente; el bloqueo 403 histórico ya no impide el tráfico auditado. NYC: **auditable, condicionado** por conflictos de claves, cobertura EPA parcial y campañas. Londres: **auditable a nivel ciudad, bloqueado para energía por zona fina con estas fuentes**, timezone y licencia pendientes. Todos superan investigación superficial; ninguno queda aceptado al 100% para el proyecto.

Antes de fase 3: cerrar granularidad/semántica admitida, atributos administrativos/usuarios, licencia/redistribución, CO₂/alertas/velocidad/recorridos y energía por zona/hora; verificar vigencia histórica de inventarios, timezone, claves conflictivas y volumen de ventanas comunes. **No hay ganador. No hubo conexión remota, generación sintética, commit/push/merge o comienzo de fase 3.**
