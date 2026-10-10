# Documentación — SmartCity Analytics

**Fase 6: documentación para revisión, no aprobación ni implementación definitiva.** Esta capa resume y enlaza la investigación inmutable de fases 0–5. Las fechas de verificación proceden del reloj del entorno, 9–10 de octubre de 2026; las URLs son referencias verificadas entonces, no garantías de disponibilidad futura.

## Rutas de lectura

| Necesidad | Documento |
|---|---|
| Incorporar una sección al informe | [Texto académico](academico/texto_para_informe.md) |
| Declarar apoyo de IA | [Transparencia sobre IA](academico/uso_ia.md) |
| Entender la recomendación | [Selección del dataset](datasets/seleccion_dataset.md) y [ADR-001](decisiones/ADR-001-madrid.md) |
| Citar fuentes, versiones y licencias | [Fuentes y procedencia](datasets/fuentes_y_procedencia.md) |
| Entender conteos, limpieza y límites | [Calidad y limitaciones](datasets/calidad_y_limitaciones.md) |
| Localizar investigación sin repetirla | [Índice de evidencias](datasets/indice_evidencias.md) |
| Revisar PostgreSQL y MongoDB | [Modelos preliminares](arquitectura/modelos.md) |
| Ver arquitectura, ETL y E-R | [Cinco diagramas Mermaid](arquitectura/diagramas.md) |
| Reproducir procedimientos existentes | [Pipeline y reproducción](arquitectura/pipeline.md) |
| Resolver bloqueos académicos | [Preguntas oficiales breves](../PREGUNTAS_PROFESOR.md) y [seguimiento detallado](equipo/preguntas_profesor.md) |
| Coordinar trabajo individual | [Guía de integrantes](equipo/guia_integrantes.md) |
| Ver alcance real del Sprint 1 | [Estado Sprint 1](equipo/ESTADO_SPRINT1.md) |
| Revisar Git, secretos y publicación | [Revisión del repositorio](equipo/revision_repositorio.md) |
| Consultar auditoría final antes de publicar | [Auditoría de publicación de Fase 6](equipo/auditoria_publicacion_fase6.md) |

## Cómo interpretar el estado

- **Ejecutado:** resultado acotado con archivo de evidencia, no cumplimiento automático del proyecto.
- **Preliminar:** contrato, DDL, colecciones y diagramas revisables.
- **Condicionado:** requiere cierre técnico o aceptación explícita de alcance.
- **Pendiente:** no existe ejecución, fuente o aprobación suficiente.

Los conteos y resultados históricos corresponden a enero de 2025 y al contrato `madrid-draft-v1`. El contrato provisional vigente para desarrollo es [`madrid-draft-v1-frozen`](../CONTRATO_PROVISIONAL_DATASET.md). No actualizar silenciosamente puntuaciones o resultados históricos con pruebas posteriores. Madrid continúa recomendado, pendiente de decisiones técnicas, del equipo y docentes.

Volver al [README principal](../README.md). La evidencia detallada sigue en [research/datasets](../research/datasets/); no se movieron ni eliminaron sus archivos.
