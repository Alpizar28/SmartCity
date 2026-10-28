# Código del Sprint 1 y núcleo de práctica

## Orden para estudiar

1. Leer una consulta SQL y señalar sus entradas, filtros, agrupación y resultado.
2. Repetir el recorrido en `basico/consultas_mongodb_estudio.js`: cada consulta
   tiene una función propia. Es una ayuda de lectura, no un reemplazo de evidencias.
3. Revisar `basico/crud_mongodb.js` para seguir una escritura paso a paso.
4. Entender cómo `basico/preparar_v2.py` transforma filas en documentos y cómo
   `basico/cargar_mongodb_v2.js` carga lotes, valida e incorpora índices.
5. Dejar `core/`, los ejecutores y la investigación para explicar validación y
   reproducción, después de entender las consultas.

Una estación es un sitio lógico; un canal es una serie de una magnitud; una
observación es su valor en un instante. Un sensor físico es otra entidad y su
relación con el canal no debe inventarse. En MongoDB, `$match` filtra documentos,
`$group` calcula por grupo y `$sort` ordena el resultado. Nunca promediar juntos
valores de magnitudes o unidades distintas.

## Qué versión mostrar

El modelo PostgreSQL de entrega utiliza `smartcity` con el
[DDL normalizado](postgres/schema_v2_3nf.sql) y las diez consultas de
[queries_v2_3nf.sql](postgres/queries_v2_3nf.sql). Su evidencia comprende 748.889
lecturas y la [verificación de 3FN](postgres/cierre_3nf.md).
MongoDB utiliza los [módulos v2](basico/consultas_mongodb_v2.js) y conserva su
[cierre nativo](mongodb/evidencia_final_mongodb.md).

La ruta SQL histórica usa `smartcity` y las diez consultas de
[`postgres/queries.sql`](postgres/queries.sql). La prueba de motor está en
`scripts/test_sprint1_sql.py`. La entrada común desde la raíz es
`bash scripts/validate_sprint1.sh --engines`.

El resto de esta guía describe el núcleo **complementario** `sprint1`, separado
del modelo normalizado. Su SQL está en `postgres/staging_queries.sql`.

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

## Límites del núcleo de práctica

La prueba de tres lecturas no acredita volumen, clientes psycopg/PyMongo con
autenticación real, recuperación ante caídas ni concurrencia o rendimiento de
producción. Este núcleo tampoco implementa la administración sintética ni los
eventos y alertas derivados de v2. Esas funcionalidades y sus resultados se
documentan por separado en los cierres de entrega; sus límites semánticos
permanecen explícitos. Véanse el [modelo de práctica](MODELOS.md), la
[evidencia de integración](INTEGRACION.md) y el
[alcance del avance](../docs/equipo/ALCANCE_CONFIRMADO_SPRINT1.md).
