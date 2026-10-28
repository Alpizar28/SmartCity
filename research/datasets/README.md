# Investigación y evidencia de datasets

**Archivo de referencia.** Para trabajar en la entrega actual, empezar por
[ENTREGA_SPRINT1.md](../../ENTREGA_SPRINT1.md), no por las fases de investigación.

## Contenido

- `00_*`–`05_*`: requisitos, candidatos, auditorías, selección y diseños de cada
  checkpoint histórico. Sus estados y reglas no son todos vigentes.
- `scripts/` y `tests/`: preparación, validación y pruebas de esos procesos.
- `results/phase*/`: resultados históricos; no reescribirlos para actualizar estados.
- `results/unified-v1/`: evidencia de la primera unificación.
- `results/expanded-2025/`: evidencia anual de 1.076.813 lecturas aceptadas de aire.
- `raw/` y `private_results/`: insumos locales ignorados por Git; no vienen en un clon.

## Referencias vigentes de la carga anual

- [Contrato `madrid-draft-v1`](../../docs/equipo/CONTRATO_UNIFICADO.md).
- [Resultados y límites históricos](https://github.com/Alpizar28/SmartCity/blob/5eb3db7/docs/equipo/CIERRE_VALIDACION_SPRINT1.md).
- [Propuesta de tráfico v2](../../docs/decisiones/PROPUESTA_MADRID_DRAFT_V2.md).

La interpretación histórica de `periodo_integracion` como minutos fue corregida:
cuenta muestras; tráfico sigue sin aceptarse bajo v1. Los 832.668 elegibles
estructurales históricos no equivalen al lote anual aceptado ni se suman a él.
La demostración de tres ejemplos en `sprint1/` usa otro esquema y contrato.

Para reproducir una fase se necesitan sus snapshots exactos y su versión de código.
La [recuperación histórica](https://github.com/Alpizar28/SmartCity/blob/5eb3db7/docs/equipo/RECUPERACION_INSUMOS_HISTORICOS.md)
documenta lo que falta; instalar dependencias no recupera esos archivos.
