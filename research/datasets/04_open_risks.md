# Fase 4 — Riesgos abiertos

Severidad:Crítica impide aceptación legal/semántica, Alta amenaza mínimos/rediseño/fecha, Media exige QAacotada. Probabilidad **cualitativa estimada de persistencia sin mitigación**, no estadística de fallos. Esperas de proveedor/docente no son horas de implementación ni tienen SLA acreditado.

| ID/alternativa | Severidad/probabilidad | Impacto | Mitigación/responsable | Reconsiderar si… |
|---|---|---|---|---|
| R01Todas:instalación/estado/identidad |Crítica/Alta |PG03/06yunidadsensor no completas |Daniel+docente antes 14:dispositivo acreditado oalcance canal/sitio explícito;NULLvisible |Rechazaalcance yno hayfuente individual:ningunaaprobada, backupno resuelve la misma ausencia |
| R02Todas:críticos/alertas |Alta/Alta |MG04/05no cubiertas estrictas |Kembly+docente:regla válidaQA/unidad/duración, emisión actualreplay autorizada ofuente histórica oficial |Exige alertas históricas conzona sin fuente;no reinterpretar incidentes ni inventarmensajes |
| R03Todas:MongoDB nativo/recursos |Alta/Media |BSON, CRUD, pipelines,500k/backup no ejecutados |José+Kembly:entorno aislado autorizado, lotes/índices/count/restore, estimado2–4hconfiguración incluidoenplan |17octsinentorno ysinplan cabe fecha23;no migrarciudad porproblema de motor |
| R04Madrid:unidadesmeteo |Alta/Media |Temperatura/humedad/correlaciones provisionales |José:diccionario oficial ytests2–4h, excluirunidadno acreditada de análisis |14octsinunidad y dos fuentes coherentes dependen deella;usar aire+tráfico ocomplemento aprobado |
| R05Madrid:historia/operadores |Alta/Alta |PG04/07/zonasparciales |José+Daniel:AnexoI/códigos/vigencias/cargo documentado, inventario independiente4–6hactivo+espera |Docenteexige instalación/estado poranalizador sin fuente;no solucionable por limpieza |
| R06Madrid:espacial |Media/Alta |14722NO2sin co-localización;76/240 puntos tráfico≤1km |José:declarar13 sitios/NULL, pérdidas y radio exploratorio;cartografía oficial,4–6hGIS |Requiere todaslaszonas/mapeoperfecto, no admitepérdidas yno haycomplemento |
| R07Madrid:duración/vmed |Alta/Media |Intensidad no conteo,1–30min;vmedvaría portipo |Daniel+José:inicio/fin, solapes, pesos/cobertura/QA por tipo,2–4h |No haycampo válido paraKPIexacto;fuenteextra/alcance, no sumar tasascomoautos |
| R08Madrid:acceso/versiones |Media/Media |URLs móviles;403antiguo, no actual en ZIP auditado |José:snapshotsSHA/CRClocales;actualización oficial solo autorizada |Corrupción irrecuperable +recurso oficial inaccesible afecta2fuentes/mínimos |
| R09Madrid:energíahoraria/CO2/recorridos |Crítica/Alta siKPIsestrictos |Mensual no horaria, concentración/tiemposausentes |Fernanda+docente: acordar alcance;José: buscar complemento local4–8h sinhallazgo garantizado |TodosKPIs estrictos yno complementos aceptados;no aprobarpleno pornota63,67 |
| R10NYC:DOTclaves |Alta/Alta |4767grupos/9534 filas(11,20%raw)fuera del join conservador |Daniel:identidad de contador/carril o cuarentena aprobada,8–16h+esperaproveedor |14octsinclave/alcance yse exige contadorfísico, riesgo noaceptable para 23 |
| R11NYC:exposición/CRS/EPA |Alta/Alta |Campañas discontinuas, solo3boroughsEPA, CRSno confirmado |José:exposición por campaña, CRSoficial y311 fechas comunes,4–8h |Exige continuidad/5boroughs/comparación espacialfina sin fuente adicional |
| R12NYC:mínimos/interanualidad |Alta/Media-Alta |236200 locales<500k,1Msolo potencialraw |José+Kembly:IDsdistintos/QA/descargas posteriores autorizadas,6–12h+red |20octno cumplevolumen útil y no adquisición viable;no respaldo listo |
| R13Londres:licencia LAQN |Crítica/Media-Alta |Uso educativo plausible, exportación pública no acreditada |Fernanda+José:permiso/alcance, rawprivado,2–6h+espera |Publicación/uso operativo obligatorio incompatible opermisodenegado |
| R14Londres:clock LCL |Alta/Media-Alta |100%timestampno sincronía;Pearson cambia±1h |José:documentarGMT/BST/DSToficial ytests4–8h;seriesseparadas hasta entonces |17octsinclock y correlación a hora exacta obligatoria |
| R15Londres:geografía LCL |Crítica/Alta |0%hogares localizados, energíazonafina bloqueada |Docente+equipo:cohorte-ciudad aceptada ofuente real independiente;no GISfake |Energíaborough estricta sincomplemento, no migrarpara resolverhorarioa costa dezona |
| R16Londres:movilidad/incidentes/panel |Alta/Media-Alta |DfT100 filas, TfLno auditado, panel108–119 |José+Kembly:auditarTfL/díasDfT, panelcomparable6–10h |23octsinMG08/movilidad/aprobación, no20consultas completas |
| R17Todas:usuarios/personas |Media/Alta |Tabla usuarios vacía, responsable individual ausente |Equipo:cuentas reales consentidas/cargo documentado1–2h;confirmarNULL |Exigencia de fuente externa no disponible;no inventar identidades |
| R18Todas:Sprint2 |Alta/Media |HDFS/Spark/UIno ejecutados, volumen no distribución |Equipo:asignación posterior, panelinteranual ybenchmark/explain/particiones |25novsin1Mprocesadoni integración, no cumplimiento;noPython=Spark |

## Madrid: resolubilidad manteniendo núcleo

Unidades meteo se cierran con documentación/validación sin cambiar fuente de lecturas; si no se acreditan, excluir esas variables del análisis científico. Co-localización parcial se resuelve por alcance13 sitios y pérdidas declaradas, no fabricando matches; cartografía oficial puede añadir distritos. Historia de sitios tiene altas/bajas/recodificaciones documentadas, pero **no acredita instalación/estado individual**; esos campos necesitan otra fuente o decisión docente. Se puede conservar el núcleo bajo aceptación expresa, no declarar vigencia histórica completa tras unjoin.

## NYC: calendario

Cuarentena deja75572conteos/112070 hechos conEPA:suficienteSQL pero no identidad DOT resuelta. Riesgo aceptable solo con alcance aprobado y ampliaciónMongo/Spark comprobada. RespuestaDOT sinSLA **no es aceptable como dependencia crítica obligatoria de 23oct**. Campaña no representa continuidad de todo elborough;controlar exposición, no ausencia=falla.

## Londres: implementación académica válida condicionada

Demo educativa privada puede ser compatible conLAQN, pero no es permiso general de redistribución. Series de energía yambiente separadas son posibles;joinhourly y geografía tienen condiciones independientes. Clockconfirmado no crea boroughdehogares. Respaldo válido solo si docente/equipo aceptan cohorte-ciudad, derechos y fuentes complementarias;no todos losKPIsestrictos.

Revisión en14/17/20/23oct;responsable registra evidencia de mitigación/aceptación. Un plan no cierra riesgo. No tareas remotas, descargasnuevas niFase5ejecutadas ahora.
