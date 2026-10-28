# SmartCity Analytics

Proyecto académico de Bases de Datos — II Semestre 2026.

## Leer solo esto para trabajar

1. [Sprint 1: alcance y ejecución](ENTREGA_SPRINT1.md).
2. [Estado y pendientes](docs/equipo/ESTADO_SPRINT1.md).
3. [Las 20 consultas y su evidencia](docs/equipo/MATRIZ_CONSULTAS_SPRINT1.md).

Para redactar la entrega: [informe en LaTeX](docs/avance_1/main.tex), con
[instrucciones para Overleaf y compilación local](docs/README.md#informe-del-avance-en-latex).

## Ver o descargar el dataset

- [Muestra CSV de 200 lecturas](docs/datasets/muestra_v2.csv): visible en GitHub
  o en LibreOffice/Excel; 100 de aire y 100 de tráfico, no el conjunto completo.
- **Dataset completo:** `data/releases/SmartCity_DATASET_COMPLETO_PRIVADO.zip`
  en la máquina de José; compartir por Drive con acceso restringido al equipo.
  Incluye todos los originales y derivados locales, no solo v2. Su manifiesto y
  checksum permiten verificar qué contiene. No se publica porque algunos originales
  contienen información de personas y fuentes con permisos distintos.

El paquete es una generación preparada. La validación masiva se acredita con
los informes PASS de ambos motores, no con el hecho de descargar el ZIP.
Los datos grandes no van al historial Git. Para reconstruir el ZIP privado:
`research/datasets/.venv/bin/python scripts/empaquetar_dataset.py --completo`.

**Primer avance, 28 de octubre:** PostgreSQL y MongoDB, modelos, datos,
10 consultas por motor y documentación. Hadoop, Spark e interfaz quedan para
la entrega final del 25 de noviembre. Referencia: `Plan_de_trabajo.pdf` del equipo.

## Ruta de ejecución

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

## Carpetas

- `sprint1/`: código local y consultas de práctica; `tests/`: sus pruebas.
- `research/datasets/scripts/`: ETL y validación de la carga anual e investigación.
- `research/datasets/results/`: evidencia de ejecuciones anteriores, no datos actuales del servidor.
- `docs/`: [documentación técnica y archivo histórico](docs/README.md).
- `compose.yaml`: infraestructura local; no instala automáticamente el esquema del dataset.

No subir credenciales, `.env`, claves, dumps ni datos privados. El acceso al servidor
se coordina con el administrador. No aplicar cargas o migraciones compartidas sin autorización.
