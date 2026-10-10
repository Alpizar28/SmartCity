# Fase 2 — Integraciones medidas

Programa: `scripts/integrate.py`. Inputs normalizados de `private_results/*.parquet`, denominadores y resultados numéricos en `results/*-integration.json`. Todos los originales se conservan. Se seleccionan valores numéricos/flags elegibles y claves no ambiguas; duplicados idénticos se deduplican **solo en derivados**. Grupos conflictivos se excluyen del join, nunca se «resuelven» sumando sin identidad física. Validación `one_to_one`/`many_to_one` evita producto cartesiano.

## Madrid aire–meteorología

Entidades independientes porred;13 sitios con **mismo código corto y coordenadas publicadasdistancia<1m**. Esto demuestra co-localización de puntospublicados, no equivalencia de analizadores ni instalación simultánea. Inventarios24aire/26meteo; muestra23sitiosaire. 56.52% desitiosambientales de muestra se co-localizan.

NO2 magnitud8 ytemperatura83, enero/julio2025. H01 esfin deprimerahora;H24media23–24h se lleva a00hdel día siguiente. Datos enhora local Madrid, ambosmisma semántica; períodos fuera deDST. Se conserva magnitud/unidad, no se mezclanvariables.

De33 821 observaciones NO2 elegibles,19 099están en sitios co-localizados(56.47%);14 722sin co-localización. Se relacionan **19 087**, 56.44% del totalNO2 elegible. Entre19 099 observaciones espacialmente mapeadas:12sintemperatura válida; cobertura temporal99.94%. Del lado meteo:16 904 observaciones sinNO2 del par. Se pierden sitios no co-localizados, otrasvariables yflags noV; no se rellenanfaltantes.

## Madrid tráfico–aire

Inventario porIDreal, decimal lat/lonpublicados;242 puntos enmuestra,240conlecturasflagsNelegibles;239deestosconcoordenadas.76 puntos elegibles dentrode1km del sitioambiental máscercano: **31.67%**. Radioexploratorio elegido para prueba, no equivalencia causal ni unazonaoficial. Publicadas coordenadasdecimales ≠precisiónGPS/acreditación de exactitud; inventarioactual no prueba vigenciaenero 2025.

674704 intervalos elegibles:213688vinculados espacialmente(31.67%),461016fuera/singeografía. Se agregan por hora y sitio de contexto, asignando timestamp de tráfico como inicio de intervalo y aire como fin dehora. **13918/14093 grupos** conNO2válido(98.76%);175sin correspondencia. Del lado NO2enero:2967 grupos sintráfico seleccionado.

`periodo_integracion`varía1–30min; el promedio de intensidad en esta prueba es **promedio de señales reportadas**, no total de vehículos ni estimador ponderado deexposición. Antes de correlación válida cerrar semántica inicio/fin, duración/coberturade intervalos y ponderación. Se pierde información de puntos/direcciones eintervalos al agregar; no sumarlas tasasveh/h como conteos.

## NYC DOT–EPA–311

DOT campaña/segmento/dirección, no sensor permanente. Se excluyen9534 filas declave ambigua con valoresdistintos:75572elegibles. EPA estado36ycondados005/047/061/081/085; cinco sitios soloenBronx/Brooklyn/Queens. FechaGMT se convierte aAmerica/New_Yorkpara coincidir con calendarioNYC; `Date Local`EPAes hora estándar, no relojDST. DOT/311calendario local es supuesto a cerrar condiccionario; join diario reduce pero no elimina elriesgo fronterizo.

Correspondencia espacial mediante **borough declarado**; conversion WKT2263→4326solo hipótesis auditada (bbox plausible), no usada para joins. 311boroughnormalizado capitalización; `Unspecified`queda sin coincidencia enDOT. No hay referencia de311a sensor, ni se inventa. EPAtecnologías/POCse mantienen al cargar; para agregados promediar por sitio primero ydespués porborough con iguales pesos de sitio, perdiendo detail/horas/metodos.

| Join | Grupos izquierdos | Grupos derechos | Ambos | Izq sin match | Der sin match | Cobertura izq | Cobertura der |
|---|---:|---:|---:|---:|---:|---:|---:|
| DOT–EPA borough/día | 322 | 883 | 146 | 176 | 737 | 45.34% | 16.53% |
| DOT–311 borough/día | 322 | 96 | 11 | 311 | 85 | 3.42% | 11.46% |

Tresfuentes: **1grupo**,0.31% de los gruposDOT. Muestra31116 fechas no es eluniverso; consultasadicionales de mismosmeses podrían aumentarlo, pero no se inventan resultados. DOTsumas son conteos en intervalos observados, no volumen total delborough; campañas/díasdiscontinuos sesgan correlaciones. 311created_datees fecha de reporte, no fecha de hecho necesariamente. No hay causalidad ni alertas automáticas acreditadas.

## Londres aire–consumo

LAQNNO2de5 sitios yLCL120hogaresanónimos. Contextogeográfico común **Londres ciudad de lamuestra**, no coordenadas individuales. **Prueba de hogar→borough/zona fina fallida:0%**, sincolumna paraasignar, no se infiere a partir deestación próxima.

Deduplicación de233repeticiones idénticas a347314intervalosenergéticos. Sumados solamentedos intervalos únicos de30min por hogar/hora;44 horas/hogar parciales excluidas. Agregado de cohorte eléctrica por hora, concentración media de los sitios conlectura; no «consumo total de Londres». Cohorte varía108–119 hogares por horacoincidente; dinámica de panelcontamina tendencias si no se selecciona cohorte estable posteriormente.

**1488horasizq/1488der/1488coincidentes,0sin match,100% temporal por timestampsinterpretados**. Enero744horasGMTconcordantes; julio744concordancia **condicional** a timezoneLCLno acreditada. LAQNesGMT; relojLCLpodría serUTC/localBST. Si se desplaza1hora los resultados/fases cambiarán: no afirmar sincronización real ni correlaciones hastaresolverlo. Apertura/cierre desitios valida período2013, no fechas de medidores.

Se pierden variación geográfica, hogar/cohorteindividual, medias horas, máximoslocales ambiental y panel completo; no se rellenan missing valores con0. Integraciónestacional no garantiza interanualidad. Exportaciones integradas permanecen ignoradas por Git porprudencia deprivacidad/licenciaLAQN.

## Resultado

Hay pruebasreales de almenosdos fuentes por alternativa; no todos los joinsniómbitos tienen éxitopleno. Madridco-localización valida una relaciónmásespecífica que mera ciudad; NYCdemuestra coincidenciaparcial; Londrespermite cohorteciudad pero **nozona fina**. Los porcentajes no sonpuntajes deldataset ni comparables sin susdenominadores.
