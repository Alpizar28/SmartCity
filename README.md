# SmartCity Analytics

Proyecto académico de Bases de Datos — II Semestre 2026.

## Empezar por aquí

- **Para defender:** [guía corta y accesos al código](defensa/README.md).
- **PostgreSQL:** [tablas](sprint1/postgres/schema_v2_3nf.sql),
  [consultas](sprint1/postgres/queries_v2_3nf.sql) y
  [diagrama](docs/arquitectura/diagrama_3nf.md).
- **MongoDB:** [consultas oficiales](sprint1/basico/consultas_mongodb_v2.js).
  Para entenderlas una por una: [versión de estudio](sprint1/basico/consultas_mongodb_estudio.js).

## Documentación de la entrega

1. [Sprint 1: alcance y ejecución](ENTREGA_SPRINT1.md).
2. [Estado y pendientes](docs/equipo/ESTADO_SPRINT1.md).
3. [Las 20 consultas y su evidencia](docs/equipo/MATRIZ_CONSULTAS_SPRINT1.md).

El [informe en LaTeX](docs/avance_1/main.tex) se acompaña de
[instrucciones para Overleaf y compilación local](docs/README.md#informe-del-avance-en-latex).

## Ver o descargar el dataset

- [Muestra CSV de 200 lecturas](docs/datasets/muestra_v2.csv): visible en GitHub
  o en LibreOffice/Excel; 100 de aire y 100 de tráfico, no el conjunto completo.
- **Dataset completo:** `data/releases/SmartCity_DATASET_COMPLETO_PRIVADO.zip`
  distribuido por el canal privado del equipo, con acceso restringido.
  Incluye todos los originales y derivados locales, no solo v2. Su manifiesto y
  checksum permiten verificar qué contiene. No se publica porque algunos originales
  contienen información de personas y fuentes con permisos distintos.

El paquete es una generación preparada. La validación masiva se acredita con
los informes PASS de ambos motores, no con el hecho de descargar el ZIP.
Los datos grandes no van al historial Git. Para reconstruir el ZIP privado:
`research/datasets/.venv/bin/python scripts/empaquetar_dataset.py --completo`.

**Primer avance, 28 de octubre:** secciones completas «Uso de PostgreSQL» y
«Uso de MongoDB» del enunciado, según la aclaración docente del 28/10/2026 comunicada al
equipo, sin rúbrica independiente. Incluye modelos, 3FN, tablas/relaciones/llaves,
índices, SQL avanzado, documentos, siete CRUD y Aggregation Framework, además de
diez consultas por motor. Los mínimos son objetivos de 100.000 registros SQL y
500.000 documentos MongoDB. Ver [alcance y cobertura](docs/equipo/ALCANCE_CONFIRMADO_SPRINT1.md).
Hadoop/HDFS, Spark, dashboard completo, análisis distribuidos y comparación final
quedan para noviembre. El alcance de los aspectos transversales no confirmados
se distingue de los resultados técnicos acreditados. El almacenamiento
distribuido MongoDB sigue sin demostración dentro del avance. El
[laboratorio académico aislado](sprint1/mongodb/academico/README.md) aporta
MG01 por sensor, MG07 por tipo y contenido narrativo con datos sintéticos.

## Ruta de ejecución

**PostgreSQL de entrega normalizado:** [DDL v2](sprint1/postgres/schema_v2_3nf.sql),
[PG01–PG10](sprint1/postgres/queries_v2_3nf.sql), [prueba de DF e impacto](sprint1/postgres/impacto_3nf.md)
y [E-R completo](docs/arquitectura/diagrama_3nf.md). Son catorce tablas: doce del
núcleo y dos auxiliares. La interfaz documental mantiene `madrid-draft-v2`.

Con PostgreSQL 16 nativo y el paquete v2 preparado, en una instancia temporal
propia sin TCP:

```bash
python scripts/validar_postgresql_3nf.py --sample 1000
python scripts/validar_postgresql_3nf.py
```

Los informes y sus SHA-256 quedan en `sprint1/postgres/evidencias/3nf/`.
Las rutas siguientes reproducen el modelo histórico y la práctica; no aplican
el DDL normalizado ni constituyen migraciones para una base existente.

- **SQL canónico:** esquema `smartcity`, contrato `madrid-draft-v1`.
  Las diez consultas están en `sprint1/postgres/queries.sql`; se prueban con
  fixtures controladas. La evidencia anual previa registra 1.076.813 lecturas por motor.
- **Práctica complementaria:** esquema `sprint1`, contrato
  `madrid-draft-v1-frozen`. Prueba tres ejemplos; no acredita el volumen anual
  ni las 20 consultas completas. Su SQL está en `staging_queries.sql`, no en el archivo canónico.

No mezclar sus esquemas, identificadores o resultados. La segunda fuente aceptada
de tráfico está implementada en una generación v2 local separada, descrita abajo.
Su preparación no acredita por sí sola la carga en motores. No se ha comprobado
aquí el servidor compartido ni la identidad física de sensores.

## Comprobar el código

Con Python 3.10+ y Node.js 18+, desde la raíz:

```bash
bash scripts/validate_sprint1.sh
```

Para incluir las diez consultas canónicas en PostgreSQL y la integración de práctica
SQL/Mongo, con Docker e imágenes ya disponibles:

```bash
bash scripts/validate_sprint1.sh --engines
```

La preparación de imágenes, el alcance de cada prueba y la validación documental están en
[ENTREGA_SPRINT1.md](ENTREGA_SPRINT1.md).

Para incluir datos reales de **aire + tráfico**, eventos/alertas demo e incidentes
anonimizados, con los snapshots y dependencias de investigación disponibles:

```bash
bash scripts/validate_sprint1.sh --datos
```

El código sencillo de esa ruta está en `sprint1/basico/*v2*` y usa `smartcity`
en una base local nueva. Las veinte consultas no equivalen a aceptación docente:
canal no es sensor físico y las alertas son replay local, no avisos oficiales.

## Qué contiene cada carpeta

- `defensa/`: recorrido corto; sus accesos apuntan a los originales.
- `sprint1/postgres/`: modelo normalizado y consultas; los SQL históricos y de
  práctica están identificados en su README.
- `sprint1/basico/`: preparación/carga v2, consultas y ejemplos de práctica.
- `sprint1/mongodb/academico/`: laboratorio sintético, separado de Madrid v2.
- `sprint1/mongodb/`: también conserva validadores y consultas del núcleo de práctica.
- `sprint1/core/`: validación de ese núcleo; no es necesario empezar por aquí.
- `scripts/`: ejecutores; [cuál usar](scripts/README.md).
- `tests/sprint1/`: pruebas offline; `tests/integration/`: pruebas para bases temporales.
- `docs/`: informe, diagramas, requisitos y resultados, con sus antecedentes identificados.
- `data/`: [paquete privado e instrucciones](data/README.md), no datos publicados en Git.
- `research/datasets/`: investigación, ETL y evidencias. El código actual todavía
  importa utilidades de aquí; no es una carpeta descartable.
- `.github/`: comprobaciones automáticas. `compose.yaml` define motores locales,
  pero no instala el esquema ni carga datos por sí solo.

No subir credenciales, `.env`, claves, dumps ni datos privados. El acceso al servidor
se coordina con el administrador. No aplicar cargas o migraciones compartidas sin autorización.
