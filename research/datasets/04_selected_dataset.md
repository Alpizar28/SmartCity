# Fase 4 — Madrid: núcleo preferido condicionado

## Estado y confianza

| Nivel de decisión | Estado |
|---|---|
| Recomendación técnica |**Madrid**,63.665/100, por evidencia y menor trabajo incremental Sprint1 |
| Selección provisional |**Condicionada** para ratificación; no implementación autorizada |
| Aprobación del equipo |Pendiente de José, Daniel, Kembly, Fernanda; no firmas simuladas |
| Cumplimiento verificado |2/10SQL estrictas,6/10funcionales condicionadas, volumenSQLlocal;Mongo0/10nativas |

Confianza media-alta en la preferencia relativa; media en calendario si se cierran condiciones antes del 14oct; baja en cumplimiento completo sin docente/complementos. Bajo exigencia de todos los atributos/KPIs reales estrictos, **ninguna alternativa está plenamente aprobable ahora**.

## Fuentes concretas recomendadas

**Núcleo:** MAD-AIR(calidad del aire), MAD-METEO(meteorología), MAD-TRAFFIC(enero2025). **Complementos:** MAD-CRASH(expedientes2026) para incidentes y MAD-ENERGY(consumo municipal mensual) para energía limitada. **Auxiliares:** inventarios aire/meteo/puntos de tráfico. Son cinco datasets del mismo portal, no cinco repositorios; los inventarios no son otra medición física. E p.6 exige dos fuentes distintas y E p.23 recomienda dos repositorios: aclarar si el docente convierte la recomendación en requisito.

| Recurso/ID de manifiesto | URL oficial exacta | SHA256 snapshot | Archivo local |
|---|---|---|---|
| MAD-AIR-file | https://datos.madrid.es/dataset/201200-0-calidad-aire-horario/resource/201200-1-calidad-aire-horario-csv/download/201200-1-calidad-aire-horario-csv.csv | `9122af41d3e73e71f5a0e0a22b99a0cefbd4c7f8abe9e2fae344207482398471` | `raw/MAD-AIR-file.attempt1.bin` |
| MAD-METEO-file | https://datos.madrid.es/dataset/300352-0-meteorologicos-horarios/resource/300352-180-meteorologicos-horarios-csv/download/300352-180-meteorologicos-horarios-csv.csv | `ada9304d302ead850e45c404d279762b774cd6671391febfc531f6c3033f3852` | `raw/MAD-METEO-file.attempt1.bin` |
| MAD-TRAFFIC-Jan2025 | https://datos.madrid.es/dataset/208627-0-transporte-ptomedida-historico/resource/208627-73-transporte-ptomedida-historico-zip/download/208627-73-transporte-ptomedida-historico-zip.zip | `4c3aac6c95939995ca6afd3b90c96ac72e59beb8770c34c6da5c92c20d8d167c` | `raw/MAD-TRAFFIC-Jan2025.record89.bin` |
| 212629-0-estaciones-control-aire-inventory | https://datos.madrid.es/dataset/212629-0-estaciones-control-aire/resource/212629-0-estaciones-control-aire-csv/download/212629-0-estaciones-control-aire-csv.csv | `2c84ca974088a6d5de13509489196ddefeee83fcae4999798b00603aa951cd1b` | `raw/212629-0-estaciones-control-aire-inventory.record39.bin` |
| 300360-0-meteorologicos-estaciones-inventory | https://datos.madrid.es/dataset/300360-0-meteorologicos-estaciones/resource/300360-1-meteorologicos-estaciones-csv/download/300360-1-meteorologicos-estaciones-csv.csv | `a95a5d26d27912751589526dc13e6cf729cf49fd8222dc990d3030660acdb7c6` | `raw/300360-0-meteorologicos-estaciones-inventory.record41.bin` |
| MAD-TRAFFIC-META-file | https://datos.madrid.es/dataset/202468-0-intensidad-trafico/resource/202468-306-intensidad-trafico/download/202468-306-intensidad-trafico.csv | `2cd3a4e97a4e25589068616148cd84841dfa1db71844247f5bb874648e961286` | `raw/MAD-TRAFFIC-META-file.attempt1.bin` |
| MAD-ENERGY-file | https://datos.madrid.es/dataset/300430-0-consumo-energia-edificios/resource/300430-0-consumo-energia-edificios-csv/download/300430-0-consumo-energia-edificios-csv.csv | `3346b8bf8f5b46fe77180e993c255f530f2a9d4056b42dfac245b69a9a755578` | `raw/MAD-ENERGY-file.attempt1.bin` |
| MAD-CRASH-file | https://datos.madrid.es/dataset/300228-0-accidentes-trafico-detalle/resource/300228-34-accidentes-trafico-detalle/download/300228-34-accidentes-trafico-detalle.csv | `25a84e6af0b213d6194df7c378490ef9c68e0156c165e0761a0a6c7b7ae4e321` | `raw/MAD-CRASH-file.attempt1.bin` |

El hash, fecha y archivo del manifiesto fijan la versión aunque cambie la URL. Aire/meteo realmente cubren2025-01-01–2026-08-31, no solo2025 como el campo histórico`period`. Tráfico corresponde a enero2025. **Accidentes2026 no se unen a enero2025 como contemporáneos**: son otra colección fechada. Para una serie conjunta elegir y auditar el recurso2025 posteriormente, no acreditado aquí. Energía mensual solo se une a agregados del mes con jerarquía/unidad correctas.

Ventana Sprint1 propuesta: aire/meteo enero+julio2025 y tráfico enero2025, ya probados. Para MongoDB≥500k priorizar674704 intervalos de tráfico no ambiguos locales, un documento por intervalo con todas sus variables; otras colecciones aportan variabilidad. SQL≥100k hechos reales y catálogos pequeños. No son674704 sensores ni se prometen993374 filas en el esquema definitivo sin repetir controles de contrato/QA.

Cantidad real frente a mínimos: la carga SQL de prueba equivale a 9,93 veces 100k; los 674704 intervalos de tráfico representan 1,35 veces 500k, margen de 174704 antes de nuevos filtros del contrato. Para Spark la muestra elegible de 993374 queda 6626 por debajo de 1M: ampliar al histórico local de aire con 1795279 slots V y comprobar normalización anual/QA, no generar filas artificiales. Los cinco archivos originales seleccionados suman **145308605 bytes** contando cada snapshot una vez (tráfico ZIP comprimido); no es almacenamiento PG/Mongo ni presupuesto total de transferencia. Cumplimiento de la interpretación académica de 100MB aún requiere confirmación. Evidencia: `results/phase4/selected_storage_evidence.json`.

## Observado, derivado, sintético y ausente

- **observed:** Hxx/Vxx, variables de tráfico/flags/duración, coordenadas/códigos publicados, consumo mensual/unidad, expediente/categoría/fecha/distrito. Fecha de alta es observada únicamente como alta de sitio, no instalación de analizador.
- **derived:** IDs/namespaces, categorías, normalización de horas reales, agregados separados por variable/unidad y co-localización; actividad en ventana y zonificación por cartografía oficial futuras. Críticos requieren regla versionada aprobada; no se han ejecutado como críticos.
- **synthetic:** ninguna medición necesaria para volumen ni generada. Hasta cuatro cuentas demo opcionales, solo con autorización posterior y aisladas; preferir cuentas reales consentidas. No fechas/estados ficticios sobre sensores reales ni consumo mensual repartido a horas.
- **unavailable/unverified:** instalación/estado individual, operador/responsable personal completo, emisiones históricas de alertas, concentraciónCO2, recorridos, energía horaria, unidades meteo/vigencia histórica completas.

Replay futuro sobre historia: emitted_at sería fecha real de ejecución actual y observed_at histórico separado, origen derived/replay. **No acredita un mensaje que Madrid emitió en2025.** Necesita autorización y aceptación docente; el umbral no se elige para forzar una consulta no vacía.

## Consultas y Sprint 2

PG09/10 verificadas; PG01/02/05/08 funcionales sobre canales, requieren granularidad/ubicación aceptadas. PG03/06 no cumplidas; PG04 operador y PG07 inventario independiente parciales; Usuarios aún vacía. MG01/02/03/06/07/08/09/10 con datos/diseño, falta ejecución BSON/pipelines/índices/CRUD; MG04 política y MG05 emisión/alcance pendientes. Plan de todas en `04_implementation_feasibility.md`.

HDFS raw/exportaciones históricas viables, comandos/batch/distribución no ejecutados. Spark: 8/10 factibles y 2 parciales en Fase3. Normalizar histórico local ≥1M y comparar enero/julio 2025–2026 con panel equivalente; no comparar diciembre2026 inexistente. Correlación NO2–temperatura: 19087 pares, condicionada a unidad/semántica. Tráfico con radio de 1km exploratorio, no causalidad. Eventos/accidentes por distrito a su fecha, no sensor causante inventado.

Dashboard no completo: movilidad con intensidad/vmed/carga por tipo y exposición; PM2.5 real, temperatura/humedad pendientes de unidad; energía mensual, no horaria; IoT con canales/cadencia, no estado administrativo ni recepción original. CO2, tiempo de recorrido, energía horaria y alertas históricas exigen fuente real o alcance docente. El gráfico Spark debe provenir de ejecución Spark, no Python.

## Puertas de aceptación (futuras)

1. **Antes del 14oct:** aprobación conjunta y docente sobre entidad canal, PG03/06/usuarios/organismo, eventos/alertas/KPIs. Sin fuente o aceptación no garantizar 10/10.
2. **Antes del 17oct:** contrato de IDs/clock/QA/BSON y primera carga en entorno autorizado. José cierra diccionario/cartografía o alcance limitado aceptado; Daniel/Kembly comparan originales y referencias.
3. **Antes del 20oct:** ≥100k hechos SQL, ≥500k documentos únicos, cero huérfanos, conteos QA/duplicados y respaldo/restauración; recursos realmente medidos, no extrapolar PG local a Coolify.
4. **Antes del 23oct:** veinte consultas semánticamente aceptadas y ejecutadas, CRUD, planes/pipelines, resultados y prueba cruzada. Colecciones vacías o diagnósticos NULL no cierran PG03/06/MG05.

## Contingencia sin migración tardía

**Respaldo: Londres, condicionado**, por ≥1M claves energéticas locales y energía semihoraria; no por el 100% de join. Antes del 14oct debe resolverse permiso educativo/exportación, clock GMT/BST, aceptación de cohorte-ciudad sin energía por borough y TfL si se exigen incidentes. Sin esas puertas **no es respaldo listo para cargar**. NYC es tercera opción solo con identidad/cuarentena DOT aceptada y volumen ampliado verificado.

Disparadores de cambio temprano: rechazo del contrato que el respaldo sí resuelva con fuente real; imposibilidad de dos fuentes coherentes/QA útiles; prioridad de energía horaria aceptando alcance LCL; derechos incompatibles o integridad irrecuperable del núcleo; conteos bajo mínimos sin expansión real viable. Comprobar que el problema se resuelve en el respaldo: todos carecen de instalación individual/CO2/alertas históricas. No cambiar solo para ocultar un bloqueo común.

**Después del 17oct evitar migración completa; después del 20oct solo por problema irreversible legal/integridad/datos con decisión explícita equipo/docente y replanificación.** Problemas de infraestructura se tratan primero con lotes/índices/recursos, no otra ciudad. Preferir complemento real compatible con Madrid (accidentes2025, CO2, energía horaria, recorridos) para vacíos puntuales, aún no acreditado; no mezclar hogares Londres con zonas Madrid. Buscar un complemento no es aprobar el dataset ni autorizar una descarga. **Detenerse aquí, sin Fase5.**
