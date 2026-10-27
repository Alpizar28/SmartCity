# Código del Sprint 1 y núcleo de práctica

La ruta SQL canónica usa `smartcity` y las diez consultas de
[`postgres/queries.sql`](postgres/queries.sql). La prueba de motor está en
`scripts/test_sprint1_sql.py`. La entrada común desde la raíz es
`bash scripts/validate_sprint1.sh --engines`.

El resto de esta guía describe el núcleo **complementario** `sprint1`, no el DDL
anual. Su SQL está en `postgres/staging_queries.sql`.

Implementación nueva e independiente de la recuperación histórica. Sin paquetes
Python externos ni cargas automáticas. Importar los módulos no conecta a motores;
el harness de integración sí inicia exclusivamente contenedores desechables.

**Para estudiar el código desde lo sencillo:** empezar por
[`basico/README.md`](basico/README.md). Hay consultas comentadas, CRUD paso a paso
y scripts pequeños de carga local. El núcleo más estricto se conserva como soporte
de validación; no es necesario reescribir sus controles para aprender las consultas.

- `core/contract.py`: serialización e IDs compatibles con la interfaz congelada,
  fingerprint **nuevo** de staging y conversión temporal fail-closed.
- `core/validation.py`: referencias explícitas a catálogos, procedencia, claves,
  nulabilidad, reloj y QA; ledger de revisión en memoria con cuarentena.
- `core/adapters.py`: DTO inmutable validado y proyecciones puras para columnas
  PostgreSQL y valores BSON-ready; sin ejecutar escrituras.
- `postgres/schema_proposal.sql`, `postgres/staging_queries.sql`: propuesta
  DDL y consultas de práctica probadas en contenedores desechables;
  no migración aplicada a servicios persistentes o compartidos.
- `mongodb/`: esquema BSON, índices, builders y función explícita de staging.

## Validación independiente

Desde la raíz, con Python 3.10+ (base de zonas IANA instalada) y Node.js 18+:

```bash
bash scripts/validate_sprint1.sh
```

Las pruebas leen los tres ejemplos reales ya publicados en
`research/datasets/results/phase5/examples.extjson`. Solo dentro de los tests se
hacen copias explícitas con metadatos nuevos y se elimina la identidad histórica.
Las mutaciones negativas son entradas deliberadamente inválidas para comprobar
rechazos; no son un dataset sintético ni se guardan como evidencia real. No se
modifica ni reetiqueta el archivo histórico; no existe importador automático.

**Alcance del PASS:** unidades Python, construcción de filtros/agregaciones,
forma de propuestas y guardas estáticas SQL/BSON. No acredita ejecución SQL,
validación BSON por MongoDB, planes de índices, volumen cargado, concurrencia,
cumplimiento académico ni reproducción histórica. No sustituye `validate_repo.sh`.

## Integración en motores locales desechables

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_sprint1_engines.py
```

Requiere Docker local (`/var/run/docker.sock`) e imágenes ya disponibles
`postgres:16.6-alpine` y `mongo:7.0.16`; **no descarga imágenes**. Usa nombres
aleatorios, `--network none`, sin puertos, sin montajes del host y bases en tmpfs.
Solo detiene/elimina los contenedores que acaba de crear. PostgreSQL usa trust
únicamente en ese contenedor aislado, nunca como configuración compartida.
Reserva hasta 1,2 GiB de memoria entre ambos motores. Escribe un informe nuevo
con resultado, versiones, hashes de código y cleanup en `/tmp/opencode/`.

La integración prueba tres lecturas publicadas, SQL/BSON nativos, índices,
consultas, vista, función, replay, cuarentena y CRUD Mongo en colección separada.
Las funciones `stage_reading`/`stageReading` persisten el staging sin sobrescribir
conflictos; no sustituyen validación Python/catálogos ni son un importador masivo.
La unicidad se apoya en el motor. Se comprobó respaldo/restauración lógico en
ambos y una carrera PostgreSQL de ocho conexiones; no se declara estrés sostenido,
concurrencia MongoDB entre procesos, durabilidad tras reinicio ni rendimiento
representativo con tres filas. Detalles en [respaldos](RESPALDOS.md).

## Pendientes para la entrega

Revisión del modelo y aceptación docente; catálogos independientes completos;
carga masiva autorizada desde originales verificados; probar de extremo a extremo
los clientes básicos psycopg/PyMongo en un entorno local autenticado, resolver
errores/reintentos; volumen, política de respaldos reales, recuperación ante
caídas, concurrencia de mayor alcance y rendimiento.
No hay sensores, usuarios, alertas ni geografía inventados. PG03/04/06, MG04/05/08
y alcance espacial siguen pendientes. Véanse [modelo](MODELOS.md) y
[evidencia de integración](INTEGRACION.md).
