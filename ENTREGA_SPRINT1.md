# Sprint 1 — PostgreSQL y MongoDB

## Cómo empezar — compañeros

1. Clonar `main` y descargar de Drive **el ZIP completo y su `.sha256`**.
2. Verificar el checksum y extraer el ZIP **dentro de la raíz del repositorio**,
   donde está este archivo. No extraer dentro de `research/datasets` ni sobrescribir
   archivos propios. En Windows se puede usar «Extraer todo» eligiendo esa raíz;
   en Linux: `unzip -n /ruta/SmartCity_DATASET_COMPLETO_PRIVADO.zip`.
3. Si el ZIP trae documentación/código antiguo, conservar el código de `main`.
   En Windows: copiar únicamente `research/datasets/raw/` y
   `research/datasets/private_results/` desde la extracción a esas mismas rutas
   del clon. Los resultados nuevos se consultan en GitHub, no en el respaldo antiguo.
4. Con Python 3.10+ y Node.js 18+, desde la raíz:

```bash
git clone --branch main https://github.com/Alpizar28/SmartCity.git
cd SmartCity
bash scripts/validate_sprint1.sh
```

La prueba rápida no necesita Docker ni instalar paquetes Python. Para cargar el
dataset en motores locales hacen falta Docker, las imágenes y las dependencias
descritas abajo. En Windows, ejecutar los comandos Bash en WSL o Git Bash;
las pruebas de motores requieren el socket Docker local indicado por el harness
(preferir Linux/WSL con Docker configurado, no una conexión remota).

- **Daniel:** `sprint1/postgres/queries.sql`, DDL común y `contract_v2.sql`.
- **Kembly:** `sprint1/basico/consultas_mongodb_v2.js` y `cargar_mongodb_v2.js`.
- **Fernanda:** `docs/avance_1/main.tex` en Overleaf y la matriz de consultas.
- **Todos:** leer `docs/equipo/ESTADO_SPRINT1.md`; no subir ZIP, `raw/`,
  `private_results/`, `.env` ni credenciales al repo. Drive restringido al equipo.

**Último resultado masivo confirmado:** PostgreSQL v2 PASS con 748.889 lecturas,
replay, metadatos y diez consultas. Informe
`research/datasets/results/expanded-v2-2025-01/execution-0652c6cd8bbc.json`.
MongoDB masivo aún no está confirmado como PASS. Las bases de prueba se eliminan:
estos comandos no dejan un servidor persistente para presentar ni cargan el compartido.

## Alcance

Primer avance del 28/10/2026: modelos, datos, índices, **10 consultas SQL y
10 MongoDB**, CRUD Mongo, vistas/funciones SQL, resultados y documentación.
El plan del equipo incluye dos fuentes y mínimos de 100.000 registros PostgreSQL
y 500.000 documentos MongoDB. Spark, Hadoop e interfaz quedan para noviembre.

La ruta siguiente prueba las diez consultas SQL con fixtures controladas y añade
una demostración complementaria SQL/Mongo de tres ejemplos. No sustituye todos
los requisitos. El [estado](docs/equipo/ESTADO_SPRINT1.md) y la
[matriz de consultas](docs/equipo/MATRIZ_CONSULTAS_SPRINT1.md) indican lo pendiente.

## Una entrada de ejecución

Desde la raíz, con Python 3.10+ y Node.js 18+:

```bash
bash scripts/validate_sprint1.sh
```

Para probar ambos motores se necesita Docker local y las imágenes
`postgres:16.6-alpine` y `mongo:7.0.16` ya descargadas:

```bash
bash scripts/validate_sprint1.sh --engines
```

El comando ejecuta, en orden: pruebas offline, diez consultas SQL canónicas
(`scripts/test_sprint1_sql.py`) e integración complementaria SQL/Mongo
(`scripts/test_sprint1_engines.py`). Deben aparecer `Sprint 1 canonical SQL: PASS`
y `Sprint 1 disposable engines: PASS`.

Solo crea y elimina contenedores propios, sin puertos ni bases persistentes.
Los informes nuevos quedan en `/tmp/opencode/smartcity-s1-sql-*.json` y
`/tmp/opencode/smartcity-s1-integration-*.json`; incluyen resultados, hashes y limpieza.

**Verificado localmente:** 51 pruebas Python, 13 Node y las diez consultas SQL
con resultados esperados e integración SQL/Mongo PASS.
Se comprobaron consultas, índices, replay, cuarentena, CRUD, respaldo/restauración
y concurrencia PostgreSQL acotada. No prueba los clientes Python con autenticación real.

## Archivos para explicar en clase

- PostgreSQL canónico: DDL `research/datasets/scripts/phase5_postgresql.sql`
  y consultas `sprint1/postgres/queries.sql`, ambos para el esquema `smartcity`.
- SQL de práctica: `schema_proposal.sql`, `staging_queries.sql` y `staging.sql`
  dentro de `sprint1/postgres/`; solo para el esquema `sprint1`.
- MongoDB: `sprint1/mongodb/validator.js`, `indexes.js`, `queries.js` y `staging.js`.
- Ejemplos comentados y CRUD: [sprint1/basico](sprint1/basico/README.md).

PG07 evalúa enero de 2025 en Madrid y excluye sensores sin vínculo a un canal:
una relación desconocida no significa falta de actividad. La prueba incluye un
sensor con lectura en el inicio incluido y otro solo en el final excluido.
Su PASS con fixtures no acredita inventario físico ni cierra el bloqueo de datos anuales.

Para ejecutar el archivo completo manualmente en una base **local ya preparada**:

```bash
PGOPTIONS='-c default_transaction_read_only=on' \
psql -X --set=ON_ERROR_STOP=1 --single-transaction \
  --host=127.0.0.1 --port=5433 --username=smartcity \
  --dbname=smartcity --file=sprint1/postgres/queries.sql
```

El comando impone una transacción de solo lectura. El usuario, puerto y nombre de base deben corresponder
a tu configuración local; no pasar contraseñas en el comando. El DDL no se instala
automáticamente y no debe aplicarse a una base poblada.

Detalles de pruebas y respaldos: [integración](sprint1/INTEGRACION.md) y
[restauración](sprint1/RESPALDOS.md).

## Validación documental

Para la suite pública del repositorio, crear el entorno **en la raíz**:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r research/datasets/scripts/requirements.lock
./scripts/validate_repo.sh
```

La instalación requiere acceso al repositorio de paquetes. Esta suite no reproduce
las cargas anuales ni recupera snapshots privados. Para usar otro intérprete,
definir `PYTHON=/ruta/al/python` al ejecutar el validador.

## Evidencia anual, separada de la demostración

El [cierre anual](docs/equipo/CIERRE_VALIDACION_SPRINT1.md) registra 1.076.813
lecturas reales de aire por motor en contenedores locales desechables.
Su contrato es [madrid-draft-v1](docs/equipo/CONTRATO_UNIFICADO.md).
No acredita una segunda fuente aceptada, 20 consultas completas ni carga compartida.

## Dos fuentes y consultas Mongo con datos reales (v2 local)

```bash
bash scripts/validate_sprint1.sh --datos
```

Añade la preparación y la carga de la generación `expanded-v2-2025-01`:
**748.889 lecturas reales de enero** (91.959 aire + 656.930 tráfico).
No modifica ni suma registros a la generación anual v1. Los snapshots originales,
inventarios Parquet y PDF oficial deben estar disponibles y pasar sus hashes.
Los resultados de carga quedan en
`research/datasets/results/expanded-v2-2025-01/execution-*.json`;
consultar su `status` y los resultados de cada motor, no inferir PASS de la preparación.

Para verificar informes ya terminados, sin volver a cargar:

```bash
research/datasets/.venv/bin/python scripts/verificar_v2.py
```

Exige resultados de ambas cargas, igualdad de IDs/payloads, código sin cambios,
replay y limpieza. Si falta un motor o solo hay ejecuciones fallidas, rechaza PASS.

Antes de la carga masiva, `--datos` ejecuta `scripts/test_mongo_v2_sample.py`:
prueba las diez consultas y eventos/alertas con tres lecturas reales en MongoDB.
Este control detectó y corrigió el uso de cursores asíncronos desde módulos
`require`; no equivale a validar el volumen completo.

El intérprete por defecto es `research/datasets/.venv/bin/python` (con las
dependencias de `requirements.lock`); se puede elegir otro mediante `PYTHON_DATOS`.
El PDF requerido es `research/datasets/raw/sprint1-v2/traffic_dictionary.pdf`,
SHA-256 `17562978ce1b7930c6c720db37f055cb3459e30b8cec50d2a671682b215b9de9`;
su URL oficial está en la [especificación v2](docs/decisiones/PROPUESTA_MADRID_DRAFT_V2.md).

Código para estudiar:

- `sprint1/basico/preparar_v2.py`: lectura, limpieza, cuarentena y accidentes anonimizados.
- `sprint1/postgres/contract_v2.sql`: adaptación explícita solo sobre base nueva vacía.
- `sprint1/basico/consultas_mongodb_v2.js`: las diez consultas comentadas.
- `sprint1/basico/cargar_mongodb_v2.js`: carga y generación local de eventos/alertas.
- `scripts/validar_v2.py`: ejecución, comparación con Python y limpieza de contenedores.

MG04/MG05 son **eventos derivados y alertas demo** de intensidad >2.000 veh/h,
no umbrales legales ni avisos oficiales. La emisión es actual, local y marcada
como replay. MG08 consulta accidentes reales de **2026**, separados de 2025.
Las zonas corresponden al inventario actual, sin vigencia histórica confirmada.
Los canales siguen sin sensor físico acreditado; PG07 no se cierra inventando esa relación.

## Compartir el dataset

Abrir la [muestra CSV](docs/datasets/muestra_v2.csv). Para transferir **todos los
datos locales**, generar el paquete privado completo y compartirlo por Drive
con acceso restringido; no subirlo a un release público:

```bash
research/datasets/.venv/bin/python scripts/empaquetar_dataset.py --completo
```

Se genera `data/releases/SmartCity_DATASET_COMPLETO_PRIVADO.zip` con todos los
originales y derivados disponibles de `research/datasets`, incluyendo otras
ciudades investigadas. Contiene algunos originales con datos de personas;
no está anonimizado ni cifrado. Excluye entornos Python, cachés, locks y secretos.
Incluye instrucciones, inventario por archivo y checksum SHA-256. No recupera
artefactos históricos que ya estaban ausentes.

Para generar **solo el paquete v2 preparado y anonimizado**, separado del completo:

```bash
research/datasets/.venv/bin/python scripts/empaquetar_dataset.py
```

Se escribe en `data/releases/` (ignorado por Git) y comprueba el CRC.
No sobreescribe un ZIP existente. Los manifiestos de los paquetes antiguos
quedan en `data/releases/historico/`; los archivos de datos únicos se conservan.
