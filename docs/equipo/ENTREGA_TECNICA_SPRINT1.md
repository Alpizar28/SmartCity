# Entrega técnica de integración — Sprint 1

**Contrato:** `madrid-draft-v1`. **Rama:** `feat/unified-data-contract`. Pendiente de revisión por el equipo. Sin despliegue compartido, push ni merge autorizados.

## Paquete común disponible

| Elemento | Ruta desde la raíz |
|---|---|
| Contrato y reglas de identidad | `docs/equipo/CONTRATO_UNIFICADO.md` |
| Diccionario de intercambio | `docs/equipo/unified_fields.csv` |
| DDL único PostgreSQL | `research/datasets/scripts/phase5_postgresql.sql` |
| Informe anual y adaptaciones PG01–PG10 | `docs/equipo/AMPLIACION_REAL_SPRINT1.md` |
| Catálogos versionados compartidos | `research/datasets/private_results/expanded-2025/catalogs.json` |
| Muestra reproducible | `research/datasets/private_results/expanded-2025/sample.extjson` |
| **Lote completo aceptado** | `research/datasets/private_results/expanded-2025/accepted.extjsonl` |
| Rechazos de aire, no cargar | `research/datasets/private_results/expanded-2025/quarantine.extjsonl` |
| Configuración, conteos y hashes | `research/datasets/results/expanded-2025/preparation.json` |
| Informe de identidad de enero y tamaños | `research/datasets/results/expanded-2025/audit.json` |
| Pruebas completas de motores | `research/datasets/results/expanded-2025/postgresql_full.json` y `mongodb_full.json` |
| Verificador de ambos motores | `research/datasets/scripts/unified_full_verify.py` |
| Propuesta pendiente de segunda fuente | `docs/decisiones/PROPUESTA_MADRID_DRAFT_V2.md` |

Los archivos privados **no están en Git**. Transferirlos por un medio acordado por el equipo o regenerarlos con los snapshots autorizados. Verificar sus SHA-256 con el manifiesto antes de importar. No subir el JSONL de 1,568 GB ni el ledger de 577,55 MB al repositorio. No enviar `.env` o credenciales junto al paquete.

## Daniel — empezar sin esperar tráfico

1. Revisar el DDL común y ejecutarlo solo en una base local propia vacía. No ejecutar sobre esquemas poblados ni servidor compartido.
2. Usar la muestra para adaptar sintaxis y el lote completo para volumen/rendimiento; ambos tienen el mismo contrato.
3. Adaptar prefijo `sprint1` → `smartcity`, clave compartida `measurement_id` y JOIN de ubicación mediante `stations.location_id`. No seguir evolucionando otra definición de tablas.
4. Respetar la semántica de vistas/funciones: `channel_activity.readings`, tiempos UTC `first_observed_at/last_observed_at`; `channels_at_station()` **no cuenta sensores**. La lista detallada de diferencias está en el informe anual.
5. Mantener PG01–PG10 y sus pruebas bajo su autoría. No copiar automáticamente los ejemplos de Jose sobre sus archivos. Para la actividad sin lecturas, fijar ventana y no inferir avería.
6. Medir con `EXPLAIN ANALYZE`; no recrear índices redundantes con PK/UNIQUE ni índices sobre la relación antigua de ubicación.

Puede trabajar ya con **1.076.813 lecturas reales de aire**, catálogos, integridad y consultas analíticas. `sensor_id` permanece NULL en las observaciones y canales reales sin evidencia física. La carga de entrega completa además incluye entidades administrativas sintéticas deterministas, con `data_origin=synthetic`, semilla y procedencia visibles: sirven para poblar `organizations`, `users` y `sensors`, pero no acreditan instalación, estado administrativo, organismo ni usuarios reales.

## Kembly — importar sin recalcular identidades

1. Mantener su implementación; los scripts `unified_full_mongo.js` y `unified_full_load.py` son harnesses de validación local, no sustitutos de su importador.
2. Usar `readings` estándar y `_id = measurement_id` proporcionado por el ETL.
3. Leer cada línea con soporte **Extended JSON**: `observed_at.$date` debe convertirse en BSON Date, no conservarse como objeto o texto.
4. Verificar referencias contra los catálogos y versiones del mismo paquete antes de escribir. Preservar valores, campos originales, versiones de transformación, `raw_reference` y `payload_hash`.
5. Crear unicidad `_id` y canal/fecha/rol, índices fuente/tipo/fecha y zona/tipo/fecha. El índice único ya cubre canal/fecha; no necesita otro igual por prefijo salvo evidencia de utilidad. Sin TTL ni `2dsphere` con CRS pendiente.
6. Reimportar todo el lote sin aumento. Si mismo ID/clave tiene otro payload, abortar y registrar conflicto, no aplicar `$set` silencioso. Comprobar contenido además de hash para detectar un valor cambiado conservando el hash antiguo.
7. Comparar conteos, metadatos y huella de IDs/payloads con PostgreSQL; no usar solo un conteo o las primeras 5.000 lecturas como prueba de igualdad.

Puede probar ya búsquedas, rangos, agregaciones y rendimiento con más de un millón de documentos reales. Alertas/eventos, accidentes, energía, metadata dinámica y `crud_demo` quedan separados. No presentar eventos derivados como observaciones ni contar fixtures en el volumen.

## Fernanda — actualizar la entrega oficial

1. Sustituir como interfaz vigente las referencias incompatibles `madrid-draft-v1-frozen`, `draft5` y `sprint1`, preservando el contexto histórico donde corresponda.
2. Incorporar nombres canónicos, tipo SQL/BSON, unidad acreditada, nulabilidad, transformación y evidencia de `unified_fields.csv`.
3. Distinguir **1.076.813 aceptadas anuales** de 26.419 rechazos de aire, 69.408 meteo y 677.724 tráfico en cuarentena. No sumar enero y la muestra otra vez.
4. Citar los manifiestos de carga completa y sus resultados, no convertir una prueba de 5.000 en una carga de 500.000. Spark sigue pendiente aunque el input supere un millón.
5. Registrar CC BY 4.0, atribución al Ayuntamiento de Madrid, snapshot/hash y evidencia documental.
6. Etiquetar la propuesta v2 como pendiente: `periodo_integracion` cuenta muestras; duración documentada 15 minutos. No editar diccionario o estado para aparentar tráfico aceptado antes de aprobación y pruebas.
7. Dejar explícito que la autorización docente de datos administrativos aleatorios no acredita sensores físicos, relojes, unidades ni mediciones inventadas.

## Verificación que pueden repetir

```bash
.venv/bin/python research/datasets/scripts/unified_expand.py --dry-run
.venv/bin/python research/datasets/scripts/unified_expand.py
.venv/bin/python research/datasets/scripts/unified_audit.py
.venv/bin/python -m pytest research/datasets/tests -q
.venv/bin/python research/datasets/scripts/unified_full_verify.py
```

El verificador final exige ambos manifiestos completos, mismos hashes de código y lote, comparaciones completas, replay, conflictos rechazados y limpieza de contenedores. Si faltan evidencias o cambiaron archivos debe fallar, no inferir éxito.

Para ejecutar **nuevas** validaciones propias, primero confirmar que no hay otra prueba equivalente activa y usar los comandos de carga del informe anual. No reiniciar un proceso sano ni ejecutar sobre servicios compartidos. Las pruebas completas tardan minutos y tienen límite de recursos; no es necesario repetirlas para leer sus resultados ya sellados.

## Decisiones que no resuelve este paquete

- Aprobación del contrato común y de la propuesta `madrid-draft-v2` por el equipo.
- Segunda fuente aceptada: 656.930 candidatas conservadoras de tráfico, todavía no aceptadas/cargadas.
- Identidad física de sensores, alcance académico de las consultas de inventario y reglas de alertas.
- Reloj meteorológico, CRS y vigencia histórica de las ubicaciones.
- Autorización independiente para publicación de la rama, PR o servidor compartido. Este paquete no la concede.
