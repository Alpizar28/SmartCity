# Estado del Sprint 1 — 28/10/2026

**Alcance:** secciones completas «Uso de PostgreSQL» y «Uso de MongoDB» del
enunciado, según la aclaración docente del 28/10/2026 comunicada al equipo,
sin rúbrica independiente. Incluye modelos, 3FN, tablas/relaciones/llaves, índices, SQL
avanzado, documentos, CRUD y Aggregation Framework, además de las veinte consultas.
Los mínimos de 100.000 registros PostgreSQL y 500.000 documentos MongoDB son
objetivos del avance. Véanse [alcance confirmado](ALCANCE_CONFIRMADO_SPRINT1.md),
[checklist](CHECKLIST_CIERRE_SPRINT1.md) e
[instrucciones](../../ENTREGA_SPRINT1.md). Los aspectos ambiguos son transversales
o pendientes de confirmación; su estado se distingue de la evidencia técnica.

## Comprobado

- **PostgreSQL normalizado: PASS nuevo.** [Cierre 3FN](../../sprint1/postgres/cierre_3nf.md):
  748.889 lecturas, cero diferencias del DTO, replay, PG01–PG10 comparadas
  completamente con Python, SQL avanzado, restricciones y reconciliación con
  MongoDB. Catorce tablas, tipos separados de magnitudes y jerarquía territorial.
  La instancia PostgreSQL 16.15 nativa fue detenida y eliminada.

- **PostgreSQL v2: PASS masivo.** 748.889 lecturas (91.959 aire + 656.930
  tráfico), metadatos comparados, replay sin duplicados y diez consultas ejecutadas.
  Contenedor y volúmenes eliminados. Evidencia:
  `research/datasets/results/expanded-v2-2025-01/execution-0652c6cd8bbc.json`.
  PG07 devuelve cero por ausencia de vínculos observados: no acredita actividad física.
- **MongoDB v2: PASS masivo actual.** 748.889 lecturas, MG01–MG10 contrastadas,
  replay, siete CRUD aislados, 13 índices, validadores y planes capturados;
  contenedor y volúmenes eliminados. Evidencia:
  `research/datasets/results/expanded-v2-2025-01/execution-d26e40706dcd.json` y
  [cierre MongoDB](../../sprint1/mongodb/evidencia_final_mongodb.md).
- **Reconciliación actual verificada:** ambas referencias contienen 748.889
  identidades/payloads con la misma huella. El informe MongoDB conservado se compara también con la nueva ejecución
  PostgreSQL normalizada, sin repetir ni modificar MongoDB.

- Suite offline actual: 65 pruebas Python y dos archivos Node aprobados; diez consultas SQL
  `smartcity` ejecutadas con resultados comprobados y fixtures revertidas.
  El parser anual vuelve a reconocer PG01–PG10. SQL de práctica separado en
  `staging_queries.sql`; PG07 excluye relaciones sensor–canal desconocidas.
- Núcleo complementario `sprint1`: integración local
  PostgreSQL 16.6/MongoDB 7.0.16 con tres ejemplos, replay, cuarentena,
  CRUD, respaldo/restauración y carrera PostgreSQL de ocho conexiones.
- Carga anual `smartcity`: los manifiestos registran 1.076.813 lecturas reales
  de aire por motor. Es evidencia local anterior, no una carga compartida verificada hoy.
- El paquete anual incluye 1 organización, **5.133 usuarios y 5.133 sensores**
  administrativos **sintéticos**, con procedencia. No acreditan inventario físico
  ni se vinculan a lecturas reales. La [autorización registrada](EVIDENCIA_AUTORIZACION_DATOS_SINTETICOS.md)
  permite esos atributos administrativos, no inventar mediciones.
- Preparación v2 local separada: **748.889 lecturas** de enero de 2025,
  91.959 de aire y 656.930 de tráfico. Las cargas nativas se comprueban con
  `scripts/validar_v2.py`; preparación y carga no son el mismo paso.
- Código Mongo v2: diez consultas reales, eventos derivados por regla demo,
  replay de alertas locales y accidentes de 2026 anonimizados (14.388 expedientes,
  deduplicados desde 33.322 filas de personas). No son avisos oficiales históricos.

## Pendientes de ambas secciones

La 3FN está técnicamente verificada en el modelo normalizado, con DF declaradas,
JSONB como dominio indivisible y las limitaciones indicadas en el cierre. La
auditoría del DDL histórico conserva su alcance original.

1. **Almacenamiento distribuido MongoDB:** requisito expreso de la p. 11 sin
   demostración. La modalidad suficiente requiere aclaración docente. Las pruebas fueron
   standalone; no se demostraron replica set, sharding ni almacenamiento distribuido.
   El requisito no se excluye automáticamente del avance.
2. **Límites de los datos:** sensores físicos desconocidos, PG07 sin asignación
   observada, geografía sin vigencia histórica, reglas demo y accidentes de 2026.
   El laboratorio sintético no transforma esos límites en evidencia municipal.
3. **Objetivos generales por aclarar:** vistas materializadas, particionamiento y
   alcance de optimización PostgreSQL pendientes de aclaración docente.
4. **Mejoras opcionales:** negativos individuales de CHECK/FK, plan MG10 y unificación
   de `--datos` con el ejecutor 3FN. La entrega distingue las rutas actuales.

El [laboratorio académico](../../sprint1/mongodb/academico/README.md) terminó en
PASS con dos lecturas para MG01, tres grupos para MG07 y tres textos con
revisiones y atributos heterogéneos. Python cotejó 18 documentos completos y
13 rechazos. La instancia temporal quedó detenida y eliminada. El diagrama
documental vigente representa las siete colecciones oficiales por separado.

Hadoop/HDFS, Apache Spark, dashboard completo, análisis distribuidos y comparación
final de cuatro motores corresponden a la continuación de noviembre. Su exigencia
para este avance no está acreditada por una rúbrica independiente.

## Reproducción histórica, separada de la validación actual

La [recuperación histórica](RECUPERACION_INSUMOS_HISTORICOS.md) conserva un
checkpoint de 83/85 pruebas y 15 artefactos pendientes. No se reejecutó hoy ni
se convierte en PASS con las pruebas nuevas. Enero y las muestras ya están
contenidos en sus generaciones: no sumarlos al volumen anual.
