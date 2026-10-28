# ADR-001 — Recomendar Madrid como núcleo condicionado

**Estado:** propuesta de recomendación técnica, **pendiente de ratificación**. Fecha documental: 10 de octubre de 2026, según reloj del entorno. Responsables de revisión: José, Daniel, Kembly y Fernanda. No hay firmas, acta de aceptación ni respuestas docentes acreditadas.

## Contexto

El proyecto requiere fuentes urbanas/IoT, modelos relacional y documental, consultas obligatorias y reutilización distribuida posterior. La investigación de 30 fuentes y las auditorías de Madrid, Londres y Nueva York muestran que ninguna cubre todos los atributos y KPIs estrictos con fuentes acreditadas. Volumen por sí solo no resuelve identidad física, administración, licencias o integración.

## Recomendación propuesta

Usar aire, meteorología y tráfico de Madrid en **enero de 2025**, con inventarios auxiliares versionados. Mantener accidentes de 2026 y energía mensual como complementos separados. `madrid-draft-v1` es el contrato histórico revisado por este ADR; el contrato provisional vigente es [`madrid-draft-v1-frozen`](../../CONTRATO_PROVISIONAL_DATASET.md). No llamar sensor a un canal ni fabricar datos faltantes.

La comparación histórica de Fase 4 otorga Madrid **63,665/100**, Londres **49,345/100** y Nueva York **46,345/100**. Son puntuaciones técnicas de planificación, no notas académicas. Madrid reduce trabajo incremental y ofrece procedencia municipal, licencia documentada, snapshots locales y relaciones exploratorias defendibles. Evidencia: [selección y matriz](../datasets/seleccion_dataset.md), [04_scores.csv](../../research/datasets/04_scores.csv), [subcriterios](../../research/datasets/results/phase4/subscores.csv).

## Alternativas

- **Londres:** reserva condicionada por volumen energético y granularidad semihoraria; no resuelve geografía fina de hogares, clock LCL ni redistribución LAQN.
- **Nueva York:** diversidad documental y campañas reales; identidad conflictiva DOT, cobertura parcial, CRS y volumen adicional pendientes.
- Otras fuentes permanecen investigadas, no auditadas al mismo nivel ni listas para sustituir silenciosamente el núcleo.

## Condiciones necesarias para ratificar

1. Acta de los cuatro integrantes con fuentes, período, entidad de consulta, nulos aceptados y responsabilidades.
2. Cierre técnico de unidades meteo, clocks meteo/tráfico, CRS y vigencia geográfica; migración de IDs si cambia interpretación temporal.
3. Fuente física real o aceptación docente explícita para canal/sitio, instalación/estado, organismos y usuarios. NULL visible no implica cumplimiento automático.
4. Política versionada de críticos/alertas y evidencia de emisión o replay aprobado; consulta separada de incidentes de 2026.
5. Confirmación docente del alcance de KPIs sin fuente: CO₂ ambiental, energía horaria y recorridos; fuentes complementarias con otras fechas y recomendación de dos repositorios.
6. Cómputo acordado de mínimos/100 MB y ejecución posterior autorizada: ≥100.000 SQL, ≥500.000 MongoDB, ≥1.000.000 Spark. Enero **832.668** no basta para Spark; 5.000 en pruebas no acredita las cargas finales.
7. Permisos de publicación, privacidad, prueba cruzada y planificación revisada. Fechas internas de P no se convierten en mandatos docentes.

No existe aprobación implícita por la autorización del usuario para preparar/documentar.

## Consecuencias y límites

Reutilizar evidencia y pipeline evita reinvestigar o sintetizar volumen; obliga a mantener observación, dispositivo, canal y ubicación separados. Los modelos y diagramas son preliminares. HDFS, Spark, dashboard, backup/restore y benchmark remoto siguen pendientes. No autoriza tocar Compose, Coolify, Tailscale, credenciales, volúmenes ni bases compartidas.

## Revisar o rechazar si

El docente rechaza la entidad/alcance sin una fuente física viable; hay derechos incompatibles; el contrato final reduce volumen útil sin ampliación real posible; o los KPIs estrictos requieren fuentes que no se acreditan. Cambiar de ciudad solo si el respaldo resuelve el problema: Londres/NYC no eliminan bloqueos comunes. Cualquier cambio necesita decisión conjunta y nuevo ADR, no migración unilateral.

## Registro de aprobación

| Evidencia requerida | Estado |
|---|---|
| José | Pendiente |
| Daniel | Pendiente |
| Kembly | Pendiente |
| Fernanda | Pendiente |
| Respuestas docentes sobre excepciones/alcance | Pendientes |
| Autorización de implementación definitiva/remota | No concedida por este ADR |
