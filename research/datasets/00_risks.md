# Fase 0 — Contradicciones, riesgos y decisiones pendientes

Fecha: 2026-10-09. Ninguna puntuación, volumen de candidato ni calidad de muestra está verificada. Referencias E/P/I en [README.md](README.md).

## 1. Contraste cuerpo–rúbrica

| Hallazgo | Evidencia | Conclusión / acción |
|---|---|---|
| Aparente «10 frente a 15 consultas» | E pp. 10, 12, 16 enumera diez; p. 28, fila 3, columna **Pts = 15** | **No existe esa contradicción en el PDF suministrado.** Revisión visual de p. 28 confirma que 15 es ponderación; el descriptor dice acceso efectivo a las consultas de cada tecnología, sin cuantificarlas. No añadir cinco consultas por motor como obligación inventada |
| Documento de atributos con dos significados | E p. 27 pide aplicación/impacto/retroalimentación de AF y aprendizaje continuo, al menos un párrafo por atributo; rúbrica p. 28 pide atributos, tipos, fuentes y restricciones | Inconsistencia real. Preparar ambos: reflexión de atributos del graduado y diccionario de datos; confirmar expectativa docente |
| Diseño gráfico no central, pero descriptor profesional | E pp. 17, 19–20 excluye diseño gráfico profesional obligatorio; p. 28 fila 10 valora diseño profesional | Tensión de evaluación. Priorizar claridad, funcionalidad y filtros; preguntar nivel visual esperado, sin sobredimensionar UI |
| Mapa condicional frente a descriptor general | E p. 19 condiciona mapa a coordenadas; p. 28 fila 2 incluye mapa para excelente | Seleccionar coordenadas reales si es viable; confirmar excepción si no se dispone de ellas |
| Dashboard e interfaz aparecen en dos criterios | E p. 28: Dashboard 14 puntos, Interfaz Gráfica Analítica 7 | Solapamiento, no permiso para omitir uno. Vincular evidencias a ambos; pedir delimitación |
| 100 MB y mínimos por registros | E p. 7 tabla con «Propuesta»; p. 26 conteos por motor | No son umbrales intercambiables. Registrar bytes y conteos por separado; confirmar si 100 MB es global, comprimido o lógico y qué cuenta como registro |
| Alcance temático amplio con ejemplos de dos fuentes | E p. 6 ejemplos aire/tráfico o energía; p. 18 exige KPIs de movilidad, ambiente, energía e IoT | Dos fuentes no garantizan cubrir todos los KPIs. Mantener lectura estricta del dashboard hasta aclaración; no declarar energía opcional |
| Streaming en objetivos generales frente a opcional | E p. 1 near-real-time; p. 2 Structured Streaming opcional; p. 22 reto adicional | Diferenciar objetivo general de implementación opcional; confirmar cómo demostrar velocidad sin exigir streaming completo |
| Identificación CE3101 frente a CE-3191 | Nombre del archivo frente a E p. 1, P e I | Confirmar identificación de curso; no afecta extracción técnica |

La rúbrica E p. 28 tiene ponderaciones que suman 100: comparación 7, dashboard 14, consultas 15, documento técnico 10, código 2, PostgreSQL 7, MongoDB 7, HDFS 7, Spark 7, interfaz 7, defensa 15 y atributos 2. Esos números son **puntos**, no cantidades de consultas o archivos.

No se encontró rúbrica del primer avance en E. P no puede acreditarla. La lista Spark termina con «dashboard o reporte», pero el apartado 7 sigue exigiendo interfaz integrada: entregar únicamente reporte no satisface automáticamente el proyecto completo.

## 2. Registro de riesgos

Prioridades cualitativas de esta investigación, no probabilidades ni notas medidas.

| ID | Prioridad | Riesgo / efecto | Tratamiento antes de aceptar fuentes |
|---|---|---|---|
| R01 | Alta | Sin instalación/estado/inventario real, PG03/06/07 y modelo mínimo quedan sin sustento | Buscar catálogo oficial; separar instalación de primera lectura y estado de actividad. Si no existe, registrar vacío y pedir decisión docente |
| R02 | Alta | Responsable, organismo y usuarios no documentados; atribuciones o identidades ficticias | Verificar operador y relación sensor–organismo; definir datos de aplicación reales y mínimos. No inventar personas/correos |
| R03 | Alta | Alertas, eventos críticos e incidentes confundidos | Distinguir observación, evento derivado, alerta emitida y reporte ciudadano; conservar regla, fecha y procedencia. Confirmar aceptación de derivados |
| R04 | Alta | Sin energía ni CO₂, candidatos ambientales/tráfico incumplen KPIs | Identificar complementos reales con zona/período compatibles; CO no sustituye CO₂ |
| R05 | Alta | Conteos vehiculares no contienen velocidad/recorrido/congestión/accidentes necesariamente | Revisar diccionarios; agregar fuentes compatibles o pedir ajuste de alcance. No inferirlos sin modelo validado |
| R06 | Alta | Join geográfico/temporal arbitrario genera correlaciones engañosas | CRS, zona horaria, ventanas, proximidad y cardinalidad explícitos; medir cobertura. No emparejar Madrid con NYC como misma ciudad |
| R07 | Alta | Beijing inferior a 500 000 documentos con fila=documento, según I; ningún volumen candidato comprobado | Medir filas/bytes/períodos reales; validar granularidad. No duplicar filas, expandir variables para inflar cifras ni generar sintéticos aquí |
| R08 | Alta | Catálogos pequeños no alcanzan 100 000 filas PostgreSQL | Modelar hechos estructurados reales además de maestros; confirmar qué tablas cuentan. No crear 100 000 sensores ficticios |
| R09 | Media | 403 en raíz NYC o restricciones/licencia/API obstaculizan acceso | Probar endpoint público específico y documentación solo con autorización fase 1; no eludir controles ni extrapolar el 403 al dataset |
| R10 | Alta | Puntuaciones I tomadas como pruebas o portales HEAD como cobertura | Mantener todas las celdas pendientes hasta muestra y metadatos; guardar evidencia independiente |
| R11 | Media | Mezclar estación, sensor y variable cambia conteos y modelo | Diccionario de granularidad e IDs; controlar observaciones únicas y normalización |
| R12 | Alta | Nulos, flags, unidades, frecuencia desigual y cambios de red sesgan promedios/tendencias | Perfilado por variable/período; métricas de cobertura; comparar años equivalentes y no equiparar faltante a cero |
| R13 | Media | Falta entorno analítico local; posible costo de dependencias | Python estándar basta para fase 0; planear entorno aislado reproducible, sin instalar servicios por anticipado |
| R14 | Alta | Invasión de alcance: carga remota, instalación o síntesis prevista en P/I | Restricciones del usuario prevalecen en esta fase; no ejecutar accesos, cargas, respaldos ni generación propuestos en PDF |
| R15 | Media | Solo archivos locales grandes sin demostrar distribución | Diseñar futura evidencia HDFS y Spark, procesamiento batch y comparación; no afirmar resultados de rendimiento |
| R16 | Media | Marcas de observación usadas como tiempos reales de recepción | Separar `observed_at` de `ingested_at`; documentar tasa histórica frente a tasa de ingestión real |
| R17 | Alta | Congelar modelos el 14 sin validar cobertura completa produce rediseño en sprint 2 | Revisar desde fase 1 interanualidad, correlación, eventos, movilidad y KPIs; reservar extensión del contrato sin afirmar cobertura |

## 3. Aclaraciones que solicitar al docente/equipo

1. Confirmar fecha y rúbrica del avance del 28 de octubre, y alcance PostgreSQL/MongoDB.
2. Confirmar KPIs de todos los dominios frente a selección de un caso urbano específico; energía y CO₂ son vacíos prioritarios.
3. Acordar si alertas/eventos **derivados de datos reales** satisfacen consultas y cómo deben identificarse; sin asumir que 311 sean alertas.
4. Resolver datos administrativos de sensores/usuarios y tratamiento de atributos sin fuente real; no autorizar sustituciones implícitas.
5. Precisar cómputo de 100 MB y de registros/documentos mínimos, granularidad admitida y evidencia esperada de distribución.
6. Precisar los dos sentidos de «documento de atributos», mapa y criterios solapados de UI.
7. Acordar definición de promedios de mediciones, ranking de zonas, inactividad y «cantidad de información».

No hace falta pedir «10 o 15 consultas» como si ambas cifras fueran exigencias: la revisión visual ya resuelve la lectura del PDF. Solo una instrucción docente adicional, no disponible aquí, podría cambiar el número.

## 4. Preparación y puerta de entrada a fase 1

**Listo ahora:** tres PDF localizados y leídos, requisitos con página, matriz de 20 consultas del sprint 1 y restricciones posteriores, candidatos separados de evidencia, repositorio localizado y entorno/conectividad inspeccionados.

**No acreditado:** ninguna muestra de datos, licencia concreta, número de filas, integridad, correspondencia geográfica, cobertura de campos, consulta ejecutada, conexión remota o rendimiento. No hay fuente seleccionada/aprobada.

Propuesta para fase 1, **no ejecutada y sujeta a autorización**:

- Comparar Madrid y NYC automatizado con metadatos y muestras pequeñas, no archivos grandes. Beijing queda como respaldo y Londres como alternativa ambiental; sus notas no deciden aceptación.
- Para cada fuente registrar URL exacta, publicador/operador, licencia, período, frecuencia, esquema, unidades, CRS, flags y granularidad.
- Medir muestra: filas, nulos, duplicados, IDs, cobertura temporal/geográfica y atributos útiles. No extrapolar totales sin método y evidencia.
- Comprobar claves de integración, períodos comunes y cardinalidad; revisar al menos dos años para Spark.
- Actualizar cada consulta con mapeo atributo → columna real → evidencia, separando observado/derivado y vacíos. Obtener fuentes complementarias de energía, CO₂, movilidad e incidentes cuando hagan falta.
- Presentar decisión conjunta al equipo; si un atributo obligatorio no existe, marcar incumplimiento o pedir aclaración, no fabricar cobertura.

Las pruebas pequeñas de importación remota previstas en I p. 4 **no están autorizadas** por esta fase ni por esta propuesta de investigación. Cualquier acceso remoto o modificación posterior necesita alcance explícito.

**Detención:** fase 0 finalizada. No avanzar a fase 1 sin autorización del usuario.
