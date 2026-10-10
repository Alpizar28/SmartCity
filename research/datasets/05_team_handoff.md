# Fase 5 — Entrega al equipo y arranque concreto Sprint1

## José — Fuentes, limpieza, generación y cargas

1. Revisar manifiesto05 y conteos de enero:832668 elegibles,674704 de tráfico. Conservar originales/hashes y coordinar ratificación conjunta.
2. Acreditar unidades meteo, relojes meteo/tráfico, CRS/vigencias del inventario y reglas de opcionales por URB/M30/C30; corregir mediante versión revisada, no silenciosamente.
3. Reproducir dry-run/prepare y preparar exportación/lotes completos **solo después de autorización futura**; esta herramienta limita salida5k. No generador sintético necesario por ahora.
4. Con Daniel/Kembly definir manifests por lote/replay/reconciliación; medir recursos/disco y respaldo/restauración antes de mínimos20oct. Esta fase no autoriza carga definitiva remota.

## Daniel — PostgreSQL

1. Revisar DDL draft5 y3FN; validar cardinalidades, tipos, constraints/trigger e índices; recibir muestra/catálogos compartidos de José.
2. Reproducir5k nativas y rechazo PK/FK/fuente; completar relaciones físicas solo con inventario acreditado. Usuarios/organismos no se rellenan artificialmente.
3. Preparar PG01–10 y dejar explícito alcance canal/NULL/bloqueos PG03/04/06/07; acordar alternativas con docente antes de afirmar cumplimiento.
4. Tras revisar:staging/idempotencia, vista materializada/refresh, particionamiento si justificado, EXPLAIN y prueba100k autorizada; cierre23oct.

## Kembly — MongoDB

1. Reproducir prueba nativa7.0 con sample.extjson y IDs exactos SQL. Revisar estándar frente a time-series y validator/índices.
2. Completar diseño/readings y CRUD exclusivamente sobre copias; consultar explain natural y evidencia MG01/02/03/06/07/09/10.
3. Proponer política MG04/MG05 con linaje/emisión y fuente; no eventos críticos ni alertas históricas por conveniencia. Ingerir incidentes2026 separadamente para prueba MG08 después de autorización.
4. Con José validar lotes≥500k reales, referencias/snapshot/payload y respaldo/restauración en entorno autorizado futuro; no confundir5k nativas con500k ni canal consensuado con sensor físico.

## Fernanda — Diagramas, documentación, evidencia y trazabilidad

1. Consolidar acta y preguntas al profesor de05_academic_decisions; conservar firmas pendientes y matriz sin falsas aprobaciones.
2. Dibujar E-R y documental con DDL/colecciones de esta fase y verificar con Daniel/Kembly; distinguir sensor/sitio/canal/observación. Los diagramas del avance siguen para revisión, no son arquitectura aprobada.
3. Enlazar diccionario CSV, versiones/hash, JSON/logs nativos y veinte casos con estados; registrar meteo/clock/geografía provisionales.
4. Coordinar prueba cruzada24oct, informe25, freeze26, demo27 y avance28 según P y confirmación docente. HDFS/Spark/UI para asignación posterior, no ejecutados aquí.

## Puertas y qué puede empezar ya

Ya: revisión del contrato, reproducción local acotada, consultas/diseños sobre muestra y preguntas al docente. Antes14: modelos/IDs/alcance aceptados;17: carga inicial futura autorizada;20: mínimos reales y restauración;23: cierre técnico con veinte consultas;24–28: revisión y entrega. Mantener margen de esfuerzo54–84h-persona de Fase4 como estimación revisable con avances reales; tiempos nativos medidos no reemplazan estimación de trabajo.

Cada integrante entrega instrucciones, resultados y limitaciones para que otro las reproduzca. Ninguna tarea de este listado autoriza automáticamente cambios en Coolify/Tailscale/producción/commit/push/merge. Fase5 se detiene al entregar este paquete preliminar.
