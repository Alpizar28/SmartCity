# Selección del dataset — recomendación condicionada de Madrid

## 1. Contexto y requisitos

SmartCity Analytics es un proyecto académico de arquitectura de datos urbanos: debe justificar el papel de PostgreSQL, MongoDB, Hadoop y Spark, no limitarse a instalarlos. Se necesitan fuentes urbanas/IoT con marcas temporales, variables interpretables y relaciones defendibles.

El enunciado exige al menos dos fuentes diferentes (E, p. 6), diez consultas PostgreSQL y diez MongoDB (E, pp. 10 y 12), y mínimos de 100.000 registros relacionales, 500.000 documentos y 1.000.000 registros procesados por Spark (E, p. 26). Recomienda dos repositorios (E, p. 23); no es lo mismo que dos fuentes. La propuesta de 100 MB y el alcance de los KPIs deben confirmarse con el docente. Las cinco entidades relacionales y sus atributos administrativos condicionan la selección: tener muchas lecturas no acredita instalación, estado ni identidad física. Autoridad, páginas y distinción obligación/recomendación en [00_requirements.md](../../research/datasets/00_requirements.md).

## 2. Metodología y alcance de investigación

La investigación progresó sin reiniciar ni sustituir evidencias:

1. **Fase 0:** extracción de requisitos del enunciado E, el plan P y la propuesta I; matriz de atributos y consultas, sin asumir verdaderas las puntuaciones iniciales.
2. **Fase 1:** identificación de recursos oficiales, inspección acotada de HTTP, muestras y diccionarios; separación de evidencia comprobada, documentada, estimada y pendiente.
3. **Fase 2:** adquisición con presupuesto, hashes, CRC de archivos comprimidos, auditoría de tipos, nulos, flags, claves, cobertura y joins sin productos cartesianos.
4. **Fase 3:** evaluación por consulta y contraste con resultados reales; prueba PostgreSQL aislada y referencias independientes; cardinalidad local, conflictos y límites por ciudad.
5. **Fase 4:** ponderación uniforme, comparación explicada y análisis de sensibilidad; recomendación condicionada.
6. **Fase 5:** contrato común de Madrid, selección restringida a enero de 2025, muestra reproducible y pruebas nativas locales PostgreSQL/MongoDB.

La [guía de evidencias](indice_evidencias.md) enlaza los entregables de cada etapa. Fase 6 solo organiza y redacta a partir de esos resultados; no recalifica ciudades ni inicia la implementación.

## 3. Treinta fuentes consideradas

El [catálogo de Fase 1](../../research/datasets/01_sources_catalog.csv) contiene **30 entradas** de ocho escenarios/repositorios investigados. Incluye fuentes de observaciones, complementos e inventarios, no treinta datasets completos descargados o aceptados.

| Grupo | IDs del catálogo | Papel y motivo para no sustituir las finalistas |
|---|---|---|
| Madrid | MAD-AIR, MAD-TRAFFIC, MAD-TRAFFIC-META, MAD-METEO, MAD-ENERGY, MAD-CRASH | Redes municipales con potencial de integración; energía mensual y administración física incompleta |
| Nueva York | NYC-COUNTS, NYC-AIR, NYC-WEATHER, NYC-311, NYC-ENERGY, NYC-ALERT, NYC-CRASH | Conteos DOT, EPA, NOAA y servicios; campañas, CRS y diferencias de granularidad |
| Londres | LON-AIR, LON-AIR-META, LON-ENERGY, LON-COUNTS, LON-WEATHER, LON-CRASH | Energía semihoraria e inventario ambiental; hogares sin zona y licencia LAQN restringida |
| Beijing | BJ-AIR, BJ-WEATHER, BJ-ENERGY | UCI ambiental, NOAA y estimación raster; integración GIS y movilidad no acreditada |
| Barcelona | BCN-AIR, BCN-TRAFFIC | Fichas ambientales útiles, pero extracciones y segunda fuente inestables |
| Chicago | CHI-AIR, CHI-TRAFFIC, CHI-ENERGY, CHI-CRASH | Reserva urbana sólida; ventana común aire–tráfico corta para comparación anual |
| openSenseMap | OSE-MAP | Caja concreta en Berlín, no complemento de Madrid; continuidad y QA por revisar |
| OpenAQ | OPENAQ | Agregador con acceso condicionado y licencias por proveedor; evitar doble conteo físico |

El detalle de formatos, organismos, URLs y limitaciones está en [01_research.md](../../research/datasets/01_research.md) y la [shortlist](../../research/datasets/01_shortlist.md). No se descartaron alternativas únicamente por tamaño o por una puntuación preliminar.

## 4. Evaluación profunda de las tres finalistas

La [auditoría real de Fase 2](../../research/datasets/02_audit_report.md) examinó **12 fuentes de observaciones/reportes y cuatro inventarios**; no todos con la misma amplitud. Madrid y EPA incluyeron archivos completos; Londres incluyó cuatro miembros completos de LCL, no el ZIP entero. DfT y LL84 fueron pruebas complementarias de esquema/granularidad, no auditorías exhaustivas.

| Aspecto medido | Madrid | Londres | Nueva York | Evidencia |
|---|---|---|---|---|
| Ventana comparativa principal | Aire/meteo enero y julio de 2025; tráfico enero | Aire/energía enero y julio de 2013 | Conteos/EPA 2023; 311 en fechas seleccionadas | [Auditoría](../../research/datasets/02_audit_report.md) |
| Hechos de prueba PostgreSQL en Fase 3 | 993.374 | 354.637 | 112.070 | [Ejecución nativa](../../research/datasets/results/phase3/postgres_execution.json) |
| Integración exploratoria | 19.087 de 33.821 observaciones NO₂ elegibles aire–meteo; 13 sitios co-localizados | 1.488 timestamps agregados coincidentes; correspondencia hogar→zona fina 0% | DOT–EPA: 146/322 grupos borough/día; DOT–311: 11/322 | [Integraciones y denominadores](../../research/datasets/02_integration_results.md) |
| Identidad/QA diferencial | Sin duplicados en selección auditada; unidades meteo y geografía histórica abiertas | 3.997.252 claves energéticas locales; reloj LCL y licencia LAQN pendientes | 4.767 claves DOT conflictivas; 9.534 filas excluidas del join conservador | [Validación](../../research/datasets/results/phase3/validation.json), [conflictos DOT](../../research/datasets/results/phase3/dot_conflicts.json) |
| Cobertura SQL estricta histórica | 2/10 (vista y función) | 2/10 | 2/10 | [Matriz por requisito](../../research/datasets/03_compliance_matrix.csv) |

Los porcentajes de integración no son comparables como tasas universales de calidad: cambian entidad, denominador, muestreo y supuestos temporales. Co-localización no prueba que dos redes compartan dispositivo, ni un join demuestra causalidad.

En Fase 4 todavía no había MongoDB nativo. Fase 5 añadió una prueba de Madrid con **5.000 documentos** en MongoDB 7.0.43 y **5.000 hechos** en PostgreSQL 16.15: siete diseños Mongo, BSON Date, índices, `explain`, CRUD desechable y consistencia con catálogos. Son avances técnicos posteriores; no alteran automáticamente el puntaje histórico ni acreditan las veinte consultas completas. Véanse [modelos y pruebas](../arquitectura/modelos.md).

## 5. Matriz comparativa y puntuaciones finales

Las puntuaciones de planificación usan los pesos de I, p. 1, no la rúbrica académica E, p. 28. Cada subcriterio recibe un rating de 0 a 4, con puntos `peso × rating / 4`; los créditos de cobertura penalizan factibilidad no ejecutada y estados parciales. Juicios de esfuerzo/riesgo se distinguen de métricas ejecutadas. La regla completa está en [04_final_comparison.md](../../research/datasets/04_final_comparison.md); las cifras exactas, sin redondeo intermedio, en [04_scores.csv](../../research/datasets/04_scores.csv) y [subscores.csv](../../research/datasets/results/phase4/subscores.csv).

| Criterio | Peso | Madrid | Londres | Nueva York |
|---|---:|---:|---:|---:|
| Consultas obligatorias | 20 | 8,200 | 7,600 | 7,800 |
| Integración tecnológica | 15 | 10,410 | 9,420 | 10,050 |
| Indicadores del dashboard | 15 | 5,055 | 2,575 | 3,495 |
| Calidad y trazabilidad | 10 | 8,000 | 6,500 | 6,500 |
| Volumen y escalabilidad | 10 | 9,000 | 10,000 | 4,750 |
| Compatibilidad espacial/temporal | 10 | 7,500 | 2,500 | 5,000 |
| Descarga y preparación | 10 | 9,000 | 7,250 | 5,750 |
| Riesgo/esfuerzo | 10 | 6,500 | 3,500 | 3,000 |
| **Total técnico / 100** | **100** | **63,665** | **49,345** | **46,345** |

Los tres decimales expresan precisión aritmética, no certeza estadística, probabilidad de éxito o nota universitaria. Los ratings uniformes siguen siendo convenciones revisables. La [sensibilidad](../../research/datasets/results/phase4/sensitivity.json) conserva la preferencia por Madrid al retirar volumen o compatibilidad espacial/temporal; una nueva evidencia o veto puede cambiar la recomendación.

## 6. Justificación de Madrid

Madrid ofrece el mejor equilibrio relativo entre fuentes municipales reales, trazabilidad con licencia documentada, preparación ya disponible y relaciones exploratorias más específicas entre redes. El tráfico inicialmente bloqueado por HTTP fue obtenido mediante un recurso oficial accesible y verificado, no mediante evasión. El estrato auditado ya aporta capacidad estructural para MongoDB sin dividir variables en documentos independientes. La reutilización de scripts y snapshots reduce trabajo incremental frente a resolver identidad DOT o permisos/geografía LCL.

No se recomienda porque «gane en todo»: Londres conserva ventaja en energía semihoraria y cardinalidad energética; Nueva York aporta diversidad documental. El menor riesgo incremental de Madrid no elimina bloqueos comunes de identidad física, estados, instalación, alertas y KPIs sin fuente. El [núcleo actual](fuentes_y_procedencia.md) contiene **832.668 observaciones elegibles de enero**, distinto del conjunto enero+julio de Fase 3; [preparation.json](../../research/datasets/results/phase5/preparation.json) es la autoridad del nuevo conteo.

## 7. Limitaciones, condiciones y aprobación

Antes de ratificar se necesitan: cierre técnico de unidades meteo, clocks meteo/tráfico, CRS e inventarios históricos; aceptación o fuente real para dispositivo físico, instalación, estado y responsables; usuarios consentidos; reglas de críticos y evidencia de emisiones; tratamiento explícito de energía mensual, accidentes de 2026 y KPIs faltantes. El núcleo de enero no alcanza por sí solo el millón de Spark. Las muestras nativas no cumplen mínimos definitivos ni prueban recursos del servidor compartido.

**Estado:** recomendación técnica condicionada, no decisión definitiva de José, Daniel, Kembly y Fernanda ni aprobación docente. El [ADR-001](../decisiones/ADR-001-madrid.md) registra puertas de ratificación y distingue decisiones internas de aprobación docente. Londres es reserva condicionada, no un dataset listo para migración automática. Ninguna alternativa satisface actualmente todos los requisitos estrictos con datos acreditados.

## 8. Fuentes y referencias

Los recursos oficiales de Madrid, EPA, NYC DOT/311, LAQN, UKPN y DfT, las condiciones de uso y la fecha de adquisición están reunidos en [fuentes y procedencia](fuentes_y_procedencia.md). Las fuentes primarias E/P/I conservan nombres, hashes y páginas en [README histórico](../../research/datasets/README.md); no se atribuyen aprobación ni análisis manual individual inexistentes. Esta documentación usa resultados guardados y reproducibles, sin nuevas descargas ni consultas remotas en Fase 6.
