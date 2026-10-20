# Validación local de la unificación

Contrato `madrid-draft-v1`, implementación `unified-v1`, ejecutada el 14/10/2026. No reemplaza los resultados históricos de `../phase5/` ni acredita despliegue compartido.

## Resultados

| Control | Resultado |
|---|---|
| Originales | Seis snapshots verificados por SHA-256; sin nuevas descargas |
| Aire | 93.720 registros seleccionados; 91.959 aceptados; 1.761 en cuarentena por calidad |
| Meteorología | 69.408 en cuarentena por semántica temporal no confirmada |
| Tráfico | 677.724 en cuarentena por semántica temporal no confirmada; selección auditada `ID % 20 == 0` |
| Conflictos del lote original | Cero |
| Preparación repetida | `idempotent_reuse=true`; se verifican hashes sin duplicar ni regenerar |
| PostgreSQL | DDL `smartcity` desde cero; muestra de 5.000 observaciones; PG01–PG10 ejecutadas |
| MongoDB | 5.000 lecturas con BSON Date; unicidad lógica e índices sin TTL ni geoespacial |
| Reconciliación | Coinciden exactamente IDs y valores de las 5.000 observaciones |
| Reimportación | Sin incremento de lecturas en ambos motores |
| Payload discordante | Rechazado en PostgreSQL y MongoDB; conflicto registrado en la evidencia |
| Integridad SQL | Fuente, canal, estación de sensor, hash original, estados de tiempo, DST y valores no finitos rechazados |
| Demo administrativo | 14 entidades sintéticas en `smartcity_demo.entities`; cero mediciones sintéticas |
| Limpieza | Contenedores y volúmenes propios eliminados; sin puertos ni conexiones remotas |
| Pruebas Python | 111 aprobadas al cerrar la implementación |
| Validación de repositorio | Aprobada; documentos, diagrama, hashes históricos desde Git, enlaces y diff |

Huella compartida de la lista ordenada de IDs y valores:

```text
260ab18a77aaeb743b73867e95fad71ade04d18eccc313cdd9bbf1b8499ccdd7
```

## Archivos

- `preparation.json`: configuración, conteos, tiempos, referencias de snapshots y hashes de todas las salidas privadas.
- `sample_reference.json`: referencia de la muestra nueva (solo aire, no tres fuentes aceptadas).
- `postgresql_sample.json`: versión e imagen del motor, hashes del código ejecutado, integridad, replay, consultas y `EXPLAIN ANALYZE`.
- `mongodb_execution.json`: versión e imagen, hashes del código, BSON, replay, conflicto, índices, consultas y reconciliación.
- Datos y cuarentena: `research/datasets/private_results/unified-v1/`, ignorado por Git.

La validación histórica de fuentes modificadas usa los bytes originales del commit registrado en `docs/decisiones/unified-v1.json`; no modifica los manifiestos antiguos ni afirma que el código actual sea idéntico al histórico. Los resultados históricos siguen verificándose por sus bytes actuales.

## Lo que todavía no se acredita

- No se cargó el lote completo en motores ni se alcanzaron 100.000 mediciones válidas: el conjunto actualmente admitido tiene 91.959.
- No hay inventario físico acreditado: PG01–PG08 sobre sensores reales siguen vacías o incompletas. Ejecutar esas consultas sin error no es cumplimiento funcional.
- Falta evidencia temporal de meteorología y tráfico, además de unidades meteorológicas y CRS/vigencia de ubicaciones.
- Pendientes revisión de Daniel/Kembly/Fernanda e integración de sus entregables. No se editó la rama de Daniel.
- No se modificó el servidor compartido, no se hizo push ni se abrió PR.

Reproducción: [contrato común](../../../../docs/equipo/CONTRATO_UNIFICADO.md). Verificación de las evidencias y salidas privadas: `.venv/bin/python research/datasets/scripts/unified_verify.py` desde la raíz.
