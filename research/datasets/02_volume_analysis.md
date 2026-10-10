# Fase 2 — Volumen real y estimaciones

No se cargóPG/Mongo/Spark ni se crearon sensoresficticios. Se examina capacidad de alimentación, no cumplimiento de ejecución de losmotores. Maestros pequeños no alcanzan100k: PGnecesita hechos estructurados históricos reales. Granularidad horariaMadrid representa horaspublicadas, no división artificial devariablespara inflarregistros. Raw diario yobservacionesnormalizadas no son nuevas fuentes ni se sumancomo25mediciones.

## Cantidades medidas

| Alternativa | Registros efectivamente procesados | Unicidad / utilidad acreditada | Límites |
|---|---|---|---|
| Madrid aire/meteo | 76 513+56 383 filas; 1 836 312+1 353 192 slots horarios publicados | 0duplicados diarios; 1 795 279+1 333 092slotsV | Recurso2025–ago2026, unidades, DST/semánticaV/M; no sensores adicionales |
| Madrid tráfico | 13 218 804 filas enero 2025,4 701 puntos | Muestra 677 724,0duplicados de(id,fecha,tipo);674704flagsN | Unicidad deTODOel ZIPno medida: no llamar13,2Mlecturas únicas |
| NYCconteos | 85106filas2023 | 80339 claves,4767conflictivas,75572no ambiguas | Totalendpoint1 875 154no acreditado único globalmente |
| EPA NYC | 9 350 315 filas nacionales recorridas para filtrar 38 290 locales | 38 290 claves UTC únicas, 36 498 observaciones sin qualifier | Solo tres boroughs; filas nacionales NO cuentan como NYC |
| 311 | 124 130 filas de16 días | Todas unique_key únicas enmuestra | Son solicitudes, no lecturas de dispositivo |
| Londres energía | 4 000 000 filas de4CSVcompletos,121 hogares | **3 997 252 claves únicas medidas** porSQLiteen disco;119valoresausentes/no numéricos | Conflictos devalor globales no perfilados; muestraJan/Julsolo233 extras idénticos |
| Londres aire | 7440slots5 sitios/2 meses | 7323 valores numéricos,0duplicados | Flags de ratificación adicionales no publicados enendpoint; presencia numérica no garantizaQA |

311 consultaagregada enero 2023:242 173 filas y242 173unique_keydistintos; julio:289 330y289 330. **531 503 solicitudes únicas consultables** en dosmeses disjuntos: evidencia deAPI, no todos descargados. Si changed-live-table, recuentos/versiónpuedenvariar; no se afirma snapshottransaccional.

## Umbrales por tecnología

- **Madrid100kPG/500kMongo/1MSpark:** capacidad real acreditada por slots horariosV de aire/meteo delrecurso completo (cadafuente>1M); hay clavesdiariasúnicas yhorasdistintas. Tráficomuestraya>500kintervalos únicos elegibles. Estas conclusiones no requieren síntesis ni multiplicacióncartesiana; la representación deobservaciónhoraria debe aceptarse académicamente. Energía/movilidad/KPIscompletos siguenotrascondiciones.
- **NYC100kPG:** muestra de hechos no ambiguosDOT+EPA supera112k; 311añade124130 solicitudes únicas, sincontarcomo sensores. **500kMongo:**531503unique_keyde311comprobados poragregadoAPIenenero+julio, suficiente para documentosdesolicitud si se acepta esagranularidad. **1MSpark:** condicionado; DOTglobal1,875Mfilasconsultables y añosextras reales, pero unicidad/QAglobal sinmedir. Extrapolando exclusivamente para planificación la razón dedatosDOTno ambiguos2023(75572/85106≈88,80%) alendpointglobal se esperaría≈1,665M; **estimación,no prueba**. Alternativamente311otrosmeses requiere contarIDsdistintos antesdeafirmar1M. Losconteos2023+EPA+311descargados no alcanzan1M.
- **Londres100kPG/500kMongo/1MSpark:** **3 997 252 claves energéticas únicas locales** enmiembros completos; incluso descontando conservadoramente todoslos119faltantes supera1M. Capacidad real, no extrapolación de167Mpublicados. No implica energía por zona ni instalación demedidor; fechaentidad hogarno persona.

Maestros: Madrid24sitiosaire/26meteo/5083 puntos tráfico, LAQN258 sitios históricos/actuales; conteosno equivalen a dispositivosactivos. SQLhechos ydocumentos deben preservar claves, unidad, fuente, flags y tiempo; no diseñamos esquemasfinales aquí.

## Almacenamiento

EPAZIP completo76 998 372 bytes →CSV2 625 915 829 bytes (~34,1×). Se leyóstreaming; **no se materializó CSVnacional** en disco. ZIPtráfico93 223 315 bytes contieneCSVcuyo tamañodecompresión está en `MAD-TRAFFIC-full_counts.json`. LCL20MBdeprefixred generó4CSVcompletos de~50MBcadauno; SHA/CRC ybytes en `02_artifact_manifest.csv`. El almacenamiento lógico/descomprimido no es descarga red.

| Fuente | Filas Parquet medidas | Bytes Parquet medidos | JSON estimado bytes/doc | JSON estimado500k |
|---|---:|---:|---:|---:|
| MAD-AIR | 187 464 | 276 212 | 187.8 | 93.9 MB |
| MAD-METEO | 138 960 | 224 910 | 190.9 | 95.5 MB |
| MAD-TRAFFIC | 677 724 | 1 565 770 | 207.0 | 103.5 MB |
| NYC-COUNTS | 85 106 | 449 526 | 197.3 | 98.6 MB |
| NYC-AIR | 38 290 | 188 214 | 217.3 | 108.6 MB |
| NYC-311 | 124 130 | 3 485 399 | 217.2 | 108.6 MB |
| LON-AIR | 7 440 | 36 307 | 182.3 | 91.1 MB |
| LON-ENERGY | 347 547 | 727 459 | 192.9 | 96.4 MB |

EstimaciónJSON:1000índicesuniformes por muestra normalizada, serializaciónUTF8yfechasISO; no BSON, índices, WAL, réplicas ni overheadMongo/PG. Parquetbytes son archivos reales medidos, no equivalentes a uso deDB. Datatypes/control de compresión pueden alterar ratios; **no existe benchmark de rendimiento remoto**. `results/storage_estimates.csv` separa columnasmeasured/estimated.

Períodos adicionales: Madrid recurso2025–2026ya auditado ycatálogohistórico; tráfico unmesaporta granvolumen; NYCaños2000/2006–2026discontinuosagregados en `DOT-years` (no todoslosaños desde2000); LCL2011–2014enmiembrosauditados, LAQN2013coincide. Para comparación interanual auditar ventanas equivalentes/canales estables; volumen no resuelve cobertura/intersección ni licencias.

**Síntesis: ninguna generada y ninguna necesaria para obtener volumen potencial deestasfuentes; ausenciasdeatributos/KPIs no se rellenan por eso.**
