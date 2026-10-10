# Fase 2 — Bloqueos y condiciones pendientes

## Acceso y validación de fuentes

- **Resuelto para el recurso auditado:** tráfico Madrid ya no403; recurso73enero 2025ZIPcompleto/CRCválido. 161/160200actualmente,137404. No generalizar a todocatalogo ni afirmar que se evadió elbloqueo: se usaronURLs oficiales sin proxies/credenciales.
- **Resuelto EPA:** ZIPnacional ensamblado por rangosdespuésdefallotransitorio; CRCdelCSVcompleto verificado. FiltroNYCreal38 290 filas, no lasnacionales.
- **LCLZIP entero no validado:** prefijo20MBcon4 miembros completos; CRC/tamaño/SHA propios, último truncado ignorado. Núcleoenergético síauditado, no auditoría exhaustiva5567 hogares.
- **CRSDOTpendiente:** WKTproyectado candidatoEPSG2263, bboxconsistente insuficiente; rutaadjuntosporassetId404. Join porboroughesposible, mapas/proximidad requieren declaraciónoficial.
- **LAQNlicencia restringida:** condiciones«informational and educational purposes only» y«NOT for operational or commercial purposes». Usoeducativo local es compatible con la finalidad declarada; nohay permiso general de redistribución acreditado. Se conserva raw e integraciones ignorados; métricas agregadas no copian tablascompletas. Antesdepublicar/downloaddashboard revisar permiso publicador/propietarios; no CC BYasumida.
- MadridCCBY4.0confirmada; UKPNCCBY4.0enficha, DfTOGLv3enpáginaoficial. NYCterms y EPAdisclaimer descargados para revisión; no asumirlicenciaCCBYporSocrata. DatosEPApúblicos/condiciones originales, revisar excepciones y citar proveedor.

## Semántica y calidad

1. **Madridrecursos móviles:** aire ymeteo contienen2025-01-01–2026-08-31, no «anual2025»como sugería laprimera fila deFase1. Se documenta esta corrección aquí sin sobrescribir00/01históricos. URLs/hashes/período realdeestaauditoría sonautoridad sobre alcanceactual.
2. Inventariosaire/meteoactuales muestran13co-localizaciones; conservarred/canal, no declarar dispositivos equivalentes. Fechas«alta»deaire son altasdesitio, no instalación deanalizador. VigenciahistóricadeinventariotráficoJan 2025aúnnoacreditada.
3. MadridmeteoPUNTO_MUESTREO100% vacío; necesitaclavecompuesta propia. HoraH24 esfin23–24h, DSTMadridelimina lahora repetida según diccionarioM13. No forzar24 horas reales cada díaDST. Enero/julioseleccionados evitanambigüedad.
4. Tráfico integra1–30min: intensidadveh/h, velocidadnohomogénea por tipo, promedio de señal enprueba no total decarros; requiere ponderación/cobertura antesdeanalítica definitiva. ErrorNesNoErrorpor diccionario; valorabsurdono seborra solo porIQR.
5. DOT4767 grupos con valores diferentespara misma claveincluso WKT. Identidaddecontadorfísico/número decarril no publicado; revisión conDOT/diccionario necesaria. Añadirvalor ala PKpara ocultarconflictos no losresuelve.
6. Un qualifier EPA no siempre es invalidante. El join conservador excluyó 1 792 registros calificados; revisar su significado antes de usar extremos/imputar. EPA no tiene duplicados reales de clave UTC en la muestra: quitar timezone creaba cinco falsas colisiones durante el cambio de hora de noviembre; se corrigió y probó. La ausencia de 88101 en Manhattan/Staten Island no equivale a falta de todo tipo PM2.5: otros parámetros/tecnologías no fueron auditados, no inventar cobertura.
7. 311created_datees reporte;149cierres anterioresacreación enmuestra, coordenadasausentes1,477%, categoríasheterogéneas. No son todosaccidentes ni alertasdeIoT. Claveunique_keyúnica realenla muestra.
8. LCL233duplicadosidénticosJan/Jul, 119valoresno numéricos/faltantes en4Mexpandidos; timestampssemihorarios sin zona explícita. JulioGMTvsBSTtodavía indeterminado. Deduplicaciónoriginalno automática; raw intacto.
9. **Londresenergíazona fina bloqueada:** ningún borough/lat/lonhogar;0% demapeofino. Total decohorte varía108–119 hogares/hora; no totalde Londres. No asignarloshogaresaestaciones/zonas inventadas.
10. DosvaloresLAQNnegativos, PM2.5EPAmáximo412 eIQRtráficopicos son **señalesrevisables**, no prueba dedatoerróneo. No eliminaciónautomática.

## Cobertura académica transversal

Instalaciónindividual, estado administrativo, responsable personal, usuarios de aplicación, concentración CO₂, alertas históricasemitidaspor zona ytiempo de recorrido siguen sin fuenteacreditada. NYCenergía LL84anualno horaria; Madridenergíamensualno horaria; Londreshorariaderivableperosin zona fina. ConteosNYC/DfTno velocidad. Una tasa histórica de observaciones no tasa derecepción en vivo.

Resolverconequipo/docente camposfaltantes/derivadosaceptados, no con síntesisautorizada implícitamente. Ningún paquete es«100% listo». Capacidad1MSparkNYCcondicionada a cardinalidad/QA ampliada; otrasdos acreditan >1Mobservaciones/claves reales con lasrestriccionesindicadas.

## Cobertura de auditoría y límites

Ochofuentes principales realmenteanalizadas;12 fuentes de observaciones/reportes+4inventariosperfilados. DfT100 filas yLL84200son pruebascomplementariasdegranularidad/esquema, **no muestrasrepresentativas deperíodoscompletos**. No hay conexión remota/pruebasdeDB/rendimientoSpark. Estadísticos exactos se refieren alalcancede cada JSON, no a fuenteentera. LCLmiembros inicialessesgados, tráficoestratoIDdeterminista,311díasseleccionados.

Las tres auditoríasdelasfuentes centrales fueron ejecutadas; integraciónfinaLondresfalla explícitamente. El alcance deFase 2está documentado y cerradoconcondiciones, **no aceptación definitivade datasets ni selección ganadora**. Fase3necesita autorización nueva.
