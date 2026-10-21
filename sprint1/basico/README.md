# Código básico para estudiar el Sprint 1

Esta es la entrada recomendada para aprender: diccionarios, listas, `for`, `if`,
consultas directas y funciones cortas. No usa clases nuevas, decoradores,
programación asíncrona, frameworks, menús complicados ni SQL dinámico.

El núcleo `sprint1/core/` se conserva: contiene los controles delicados de IDs,
reloj, procedencia y calidad ya probados. Simplificar el código no significa
eliminar esos controles ni inventar los campos que faltan.

## Qué leer primero

1. `consultas_postgres.sql`: SELECT, WHERE, ORDER BY, DISTINCT, JOIN, GROUP BY,
   HAVING, COUNT, MIN, MAX, AVG y SUM, con comentarios en español.
2. `consultas_mongodb.js`: consultas, filtros, ordenamiento y agrupaciones.
3. `crud_mongodb.js`: insertOne/insertMany/find/findOne/updateOne/updateMany/
   deleteOne paso a paso, sobre una colección de práctica separada.
4. `archivos.py`: lectura de JSON y conversiones sencillas de fechas/documentos.
5. `cargar_postgres.py` y `cargar_mongodb.py`: validación, conexión local y carga
   una lectura a la vez. No contienen un importador masivo ni recuperan originales.

## Revisar un archivo sin instalar drivers ni conectar

Desde la raíz del repositorio:

```bash
python3 -m sprint1.basico.cargar_postgres data/lecturas.json data/catalogos.json
python3 -m sprint1.basico.cargar_mongodb data/lecturas.json data/catalogos.json
```

Esas rutas son los archivos reales que debe proporcionar el equipo, no archivos
de ejemplo incluidos ni instrucciones para generar datos ficticios. Se necesita
un array JSON de 1 a 5000 lecturas nuevas del contrato congelado y un objeto de
catálogos revisados (`sources`, `versions`, `stations`, `channels`, `zones`). Cada
archivo tiene un límite de 5 MiB. Es una carga acotada, no una estrategia de volumen.

Los catálogos tienen mapas por ID. Cada versión indica `source_id`; cada estación
indica `source_id`, `source_key` y `zone_id`; cada canal indica `source_id`,
`station_id`, `measurement_type`, `unit` y `unit_status`. Las referencias y unidades
deben venir de evidencia revisada, **no construirse desde cada lectura entrante**.
PostgreSQL debe tener además sus catálogos previamente instalados y consistentes.

No pasar el archivo histórico `examples.extjson` como si fuera un contrato nuevo:
se rechaza su versión. Tampoco se recalculan hashes o IDs para esconder errores.
Sin `--guardar`, estos programas validan todos los registros y terminan sin
abrir una conexión. Un archivo con errores produce un código de salida 1.

## Guardar: solo en una base local preparada y autorizada

Antes de guardar debe existir una base **exclusivamente local de práctica** llamada
`smartcity_sprint1_local`. No usar un túnel hacia un servidor compartido aunque
escuche en localhost. Los scripts fijan `127.0.0.1`, pero no pueden comprobar dónde
termina un túnel creado fuera del programa.

- PostgreSQL necesita `schema_proposal.sql`, `queries.sql`, `staging.sql` y
  catálogos independientes cargados/revisados. Los scripts no crean ni sustituyen
  el esquema ni sus catálogos automáticamente.
- MongoDB necesita `validator.js`, los índices de `indexes.js` y permisos para
  lecturas/cuarentena. Se comprueban modo estricto, rechazo de errores e índice
  único completo de `staging_key`. La revisión previa debe confirmar que es el
  validador correcto; esta comprobación no acredita por sí sola su contenido.
- Crear usuarios locales con permisos mínimos para la práctica, sin inventar
  usuarios personales del dataset ni copiar credenciales compartidas.

Instalar los drivers en un entorno propio, nunca en el Python global:

```bash
python3 -m venv .venv-basico
.venv-basico/bin/python -m pip install -r sprint1/basico/requirements.txt
```

Definir de forma privada `SMARTCITY_PG_USER`, `SMARTCITY_PG_PASSWORD`,
`SMARTCITY_MONGO_USER` y `SMARTCITY_MONGO_PASSWORD` en la terminal. No guardarlos
en el código, Git ni argumentos de línea de comandos. Los programas no muestran
contraseñas ni textos completos de errores de conexión.

Después de preparar y autorizar ese entorno:

```bash
.venv-basico/bin/python -m sprint1.basico.cargar_postgres data/lecturas.json data/catalogos.json --guardar
.venv-basico/bin/python -m sprint1.basico.cargar_mongodb data/lecturas.json data/catalogos.json --guardar
```

Puertos por defecto: PostgreSQL 5433 y MongoDB 27017; se cambian con `--puerto`.
`accepted` significa insertada, `duplicate` significa replay idéntico y
`quarantined` significa conflicto conservado sin sobrescribir la lectura previa.
PostgreSQL confirma todo el archivo en una transacción o lo revierte. MongoDB
guarda por documento: puede quedar una carga parcial ante un error. Repetir el
archivo permite reconocer duplicados; una cuarentena fallida nunca se anuncia
como exitosa. No hay reintentos automáticos ni carga concurrente en estos scripts.

## Ejecutar las consultas y el CRUD básico

Usar clientes autenticados en la base local preparada. Los parámetros de
conexión y las credenciales se configuran fuera de los archivos de consultas.

- PostgreSQL: abrir la base local con `psql` y ejecutar
  `\i sprint1/basico/consultas_postgres.sql` desde la raíz del repo.
- MongoDB: abrir la base local con `mongosh` y ejecutar
  `load('sprint1/basico/consultas_mongodb.js')`.
- CRUD MongoDB: `load('sprint1/basico/crud_mongodb.js')` solo explica el modo seguro.
  Para practicar explícitamente, en esa misma sesión local:

```javascript
var GUARDAR = true;
load('sprint1/basico/crud_mongodb.js');
GUARDAR = false;
```

El CRUD copia tres lecturas existentes, usa `practica_crud` y la elimina al
terminar. Si ya existe esa colección, aborta sin tocarla. Si falla la práctica,
puede quedar esa colección para inspección: no borres trabajo sin revisarlo.
No aplica cambios de práctica sobre `readings`, sensores ni alertas históricas.

## Qué se probó y qué no

`bash scripts/validate_sprint1.sh` incluye pruebas de archivos, conversiones,
modo sin conexión y lógica de carga con clientes simulados. El harness de motores
ejecuta las consultas y el CRUD básico en las bases desechables.

Las conexiones completas de estos nuevos CLI mediante psycopg/PyMongo **no se
han probado contra una base local autenticada**. No se instalaron esos drivers
ni se ejecutó `--guardar` en la máquina. El harness prueba por separado el SQL y
MongoDB reales, no sustituye esa validación del cliente. Tampoco resuelve los
requisitos académicos bloqueados o la 3FN definitiva.
