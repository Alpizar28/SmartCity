# Fase 1 — Riesgos, atributos sin fuente y límites de aceptación

No hay dataset definitivo ni datos sintéticos generados. Las afirmaciones de [investigación](01_research.md), [catálogo](01_sources_catalog.csv) y [arquitecturas](01_candidate_architectures.md) son evidencia de investigación, no importaciones/resultados de consultas.

## 1. Qué información real se encontró y qué no

| Necesidad | Información real utilizable localizada | Campo exacto faltante / tratamiento lícito propuesto |
|---|---|---|
| Instalación de sensores | LAQN `DateOpened`/`DateClosed` de **sitio**; Chicago implantación colectiva verano 2025; openSenseMap `createdAt` registro de caja | `sensor.installation_date` por dispositivo físico no acreditado en los tres finalistas. Mantener nulo/TBD. `site.opened_at`, `platform_registered_at`, `first_observed_at` pueden conservarse separados. **Solo sustituir bajo decisión explícita docente/equipo; jamás presentarlos como instalación real** |
| Estado activo/inactivo | LAQN fechas de operación de sitios; flags de validez Madrid; 311 estado de trámite; Chicago reporting_status de edificio | `sensor.administrative_status`, `status_effective_at` faltantes. `active_in_window`/`last_observed_at` son derivados analíticos; flag inválido no sensor apagado, trámite Open no sensor activo |
| Organismo responsable | LAQN `DataOwner`/`DataManager`/autoridad por sitio; DOT/DOB/NYCEM/OTI; direcciones municipales Madrid; NOAA/EPA con proveedores | `sensor.owner_org_id` requiere relación física acreditada; publicador/archivador no siempre dueño. `org.responsible_person` (persona/cargo concreto) no acreditado; no inventar nombres ni correos |
| Usuarios del sistema | Ningún dataset de sensores es directorio de usuarios de aplicación | `user.id/name/email` deben provenir de cuentas reales consentidas del proyecto posteriormente, no de víctimas/solicitantes 311. Si se opta por identidades ficticias, serían **sintéticas**, sujetas a autorización y etiquetado; no se hicieron |
| Consumo energético | Madrid `SENSOR/CONSUMO/UNIDADES` mensual; NYC LL84 energía por propiedad/año; Londres LCL `KWH/hh` semihorario; China raster estimado mensual | `energy.hourly_value` real no encontrado para Madrid/NYC. No derivable de total mensual/anual sin modelo estimativo. Londres permite sumar intervalos observados, pero `household.zone_id` no está disponible: no asignar borough ni coordenadas inventadas |
| CO₂ | NYC LL84 GHG en toneladas **CO₂e**, reales reportadas/calculadas por proveedor; búsqueda London CO₂ y China modelos sin serie urbana compatible acreditada | `ambient.co2_concentration_ppm`/serie local no acreditada. NO2, CO, PM2.5 o toneladas CO₂e no sustituyen CO₂ ambiental. Conversión energía→emisión requiere factores/geografía/período y sería **estimación derivada**, no sensor de concentración |
| Incidentes urbanos | Madrid expedientes de accidentes, NYC 311 solicitudes, TfL accidentes y Chicago crashes | Tipos reales disponibles, pero `incident.sensor_id` generalmente no existe. No fabricar vínculo con sensor próximo; asociación espacial es derivada y no causal. Fecha de solicitud no necesariamente fecha del incidente |
| Alertas/eventos emitidos | NYCEM publica schema de mensaje emitido (`date_and_time`, título/cuerpo/tipo), aunque muestra 503 | `alert.zone_id` explícito y `alert.sensor_id` no publicados en ese schema. Alertas ambientales/automáticas en Madrid/Londres no comprobadas. `event.rule_id/threshold/severity` podrían derivarse de lecturas con método aprobado, pero `historical_alert.emitted_at` **no se puede reconstruir** como emisión real |
| Movilidad | Madrid D velocidad/carga/ocupación, pero histórico403; NYC conteos; DfT conteos de campañas; Chicago velocidad GPS estimada; accidentes reales | `travel_time` no encontrado en fuentes finalistas probadas; `speed` faltante en NYC/DfT. Conteo no determina velocidad ni congestión. Carga/ocupación/velocidad de Madrid requieren diccionario/cobertura por tipo. Modelos estimados se etiquetan, no reales |
| Tasas de recepción | Fechas de observación en todas las redes, no timestamps de recepción históricos | `received_at` histórico faltante. `ingested_at` real puede registrarse al cargar después; lecturas/hora del histórico no son tasa de recepción en vivo. No copiar observed_at como received_at |

**No hay campo cuya síntesis sea obligatoria por naturaleza.** Si un atributo exigido carece de fuente, las opciones son buscar otra fuente, dejarlo faltante y declarar incumplimiento, solicitar ajuste/aceptación de derivado, o generar sintéticos **solo con autorización posterior explícita**. La investigación identifica los campos que quedarían ficticios si se exigiera rellenarlos: instalación individual, estado administrativo, responsable personal/usuarios inventados, geografía de hogares LCL, energía horaria a partir de anual/mensual, concentración CO₂ y mensajes históricos de alerta no publicados. No se ofrece un generador ni se atribuye realidad a esos valores.

Los eventos por umbral, normalización de unidades, agregados de energía semihoraria, correlaciones y zonas obtenidas de coordenadas con cartografía oficial son **derivaciones de observaciones reales**, no necesariamente sintéticos. Deben conservar input, método, versión, tiempo de cálculo y distinguirse de emisiones históricas/publicadas. Disgregación estadística de consumo mensual a horas es una estimación modelada, no una medición horaria.

## 2. Registro priorizado

Prioridades cualitativas, no probabilidades ni puntuaciones medidas.

| ID | Nivel | Fuentes | Riesgo / evidencia | Control o puerta de aceptación |
|---|---|---|---|---|
| F1-01 | Crítico | Todas | Ningún finalista satisface sin condiciones los atributos mínimos instalación/estado y todos los KPIs | Decisión expresa sobre atributos faltantes antes de aceptar esquema; no dar 20/20 por probado |
| F1-02 | Alto | MAD-TRAFFIC | Tres ZIP403 y ficha posterior403; diccionario no prueba descargabilidad de datos | Auditar acceso oficial limitado; si persiste y movilidad depende del archivo, no aceptarlo |
| F1-03 | Alto | MAD-AIR/METEO | Inventario espacial independiente no comprobado; punto de muestreo meteo vacío | Conseguir geografía oficial y vigencia; evaluar zona/proximidad; no unir por ESTACION numérica entre redes |
| F1-04 | Alto | Madrid/NYC | Energía mensual/anual no responde energía por hora | Fuente adicional horaria o decisión docente; no repartir por número de horas y llamar lectura real |
| F1-05 | Alto | LON-ENERGY | Sin borough/coordenadas de hogares | Limitar a ciudad/cohorte no geográfica; si energía por zona estricta, bloqueo de aceptación |
| F1-06 | Alto | LON-AIR | Condiciones educativas/informativas, prohibición operativa/comercial; propiedad de autoridades | Revisar redistribución/despliegue/documentación de permisos; no marcar CC BY |
| F1-07 | Alto | NYC-AIR | Prefijo nacional no acredita un solo sitio NYC ni cantidad local útil | Filtrar estado/condado, validar sitios, POC/métodos, unidades y cobertura antes de aceptar |
| F1-08 | Alto | NYC-COUNTS | WKT proyectado y archivo de errores ATR; campañas discontinuas | Acreditar CRS, corregir con fuente oficial, medir errores y cobertura; no convertir números a grados |
| F1-09 | Alto | NYC-ALERT | Esquema200, datos503, sin zona explícita | Datos/mensajes reales, período y territorio verificables; extracción desde texto con evaluación y etiqueta derived |
| F1-10 | Alto | Todas | CO₂ ambiente no localizado; CO₂e anual y CO no equivalentes | Mantener KPI no cubierto o aprobar alternativa de emisiones claramente distinta |
| F1-11 | Alto | Todas | Los maestros no alcanzan100k; conteos globales no prueban volumen de ventana común | Conteos por tabla/colección, válidos/únicos y año; hechos reales; no duplicar ni contar producto cartesiano |
| F1-12 | Alto | Madrid/LCL/NOAA | DST, H24, medias horas, múltiples reportes y QC/sentinelas | Fecha/hora y zona documentadas; reglas de reportes, horas parciales y nulos; no rellenar ceros |
| F1-13 | Alto | MAD-ENERGY/NYC-ENERGY | Unidades distintas y medidores/propiedades jerárquicas pueden duplicar consumo | Separar variable/unidad; nivel de agregación único; no sumar activa+reactiva+gas ni padres+hijos |
| F1-14 | Alto | Accidentes/311 | Una fila persona no accidente; queja no incidente confirmado | Claves de expediente/colisión/solicitud y semántica; minimizar campos personales |
| F1-15 | Alto | Todas | Join por proximidad/hora sin exposición/cobertura produce sesgo o multiplicación | Reglas uno-a-uno/uno-a-muchos justificadas, número de matches/no-matches y cobertura; no causalidad automática |
| F1-16 | Medio | LCL/EPA | Archivos grandes pese a muestras pequeñas; LCL ignoró Range | Presupuesto explícito fase2; streaming con cap; no repetir descarga grande por diagnóstico |
| F1-17 | Alto | London/Chicago | DfT campañas; Chicago aire2025 y tráfico terminado2026-04; años incompletos | Comparar ventanas equivalentes; presentar exposición y faltantes; no tendencias anuales completas ficticias |
| F1-18 | Alto | Beijing | UCI420768 filas y una sola descarga integrada; NOAA no garantiza500k; sin movilidad | Conteos reales/otra fuente compatible; no expandir variables solo para alcanzar mínimos |
| F1-19 | Medio–alto | BCN/OpenAQ | Timeouts; clavev3; licencia/ciudad/proveedor desconocidos | Acceso autorizado oficial y licencia por proveedor; no cuentas/credenciales automáticas |
| F1-20 | Alto | openSenseMap | Caja Berlin con -37.41 repetido; PMantiguo/extremo; metadata registro no instalación | Auditar sensor/calibración/continuidad; no generalizar de una caja ni inventar reparación |
| F1-21 | Medio | Todas | Cambios de datos/licencias/endpoints tras esta fecha | Guardar snapshots pequeños permitidos, hash/fecha/manifest y revisión de condiciones |
| F1-22 | Crítico | Operación | Confundir shortlist con aprobación e iniciar fase2/cargas privadas | Detenerse; autorización independiente de auditoría, descarga masiva y acceso remoto |

## 3. Licencias y responsables: condiciones no negociables

- Madrid/Barcelona: CC BY 4.0 documentada; atribución y versión. No heredar licencia de otro organismo cuando se agregue un complemento.
- UCI/UKPN/Figshare: CC BY 4.0 documentada; modelos raster son estimaciones externas y conservan esa procedencia.
- LAQN: condiciones explícitas restringidas. No comparar «API pública» con «licencia abierta de redistribución».
- DfT: OGL v3 enlazada; TfL requiere revisión propia. NOAA/EPA: verificar condiciones de datos públicos y excepciones/proveedor, no asumir CC0 para todo.
- NYC/Chicago: condiciones municipales específicas pendientes de cierre, no CC BY inferida porque usen Socrata.
- openSenseMap: PDDL1.0 documentada por senseBox, condiciones actuales por confirmar. OpenAQ depende de cada proveedor; conservar identidad y evitar doble conteo del mismo monitor.
- Organismo publicador, operador, propietario y gestor deben ser campos distintos cuando difieran. LAQN facilita DataOwner/DataManager; una agencia 311 encargada de resolver una solicitud no necesariamente administra un sensor.

## 4. Qué tendrá que medir una fase 2 autorizada

Sin fijar umbrales de calidad que el enunciado no define:

1. Acceso reproducible y licencia aplicable; muestras acotadas con hash completo/fecha/versión.
2. Cabeceras, encoding, unidades, flags, rangos físicos y sentinelas.
3. Claves naturales: unicidad, duplicados, dispositivos/sitios/campañas, relaciones con inventarios y fechas de vigencia.
4. Cobertura por fuente/variable/zona/año; intersección temporal y espacial real, cardinalidad de joins y sesgos de muestreo.
5. Cantidades **distintas** de raw filas, observaciones válidas/únicas, documentos previstos, hechos relacionales y registros Spark; tamaño comprimido/descomprimido por separado.
6. Cada atributo exigido mapeado a columna de origen, evidencia, derivación aceptada o vacío; ninguna fecha/identidad ficticia.
7. Capacidad de una muestra para las20 consultas, sin ejecutar cargas privadas por defecto. Importación local/remota y pruebas de rendimiento necesitan alcance específico.
8. Presupuesto/tiempo y criterios de rechazo por alternativa. Si falla una, auditar reserva compatible con autorización, no improvisar sustitución silenciosa.

**Estado final:** riesgos reconocidos, no mitigados por ejecución. Fase 2 pendiente de autorización.
