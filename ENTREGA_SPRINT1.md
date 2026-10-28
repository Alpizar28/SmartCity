# Sprint 1 — PostgreSQL y MongoDB

## Acceso y reproducción

1. Clonar `main` y descargar de Drive **el ZIP completo y su `.sha256`**.
2. Verificar el checksum y extraer el ZIP **dentro de la raíz del repositorio**,
   donde está este archivo. No extraer dentro de `research/datasets` ni sobrescribir
   archivos propios. En Windows se puede usar «Extraer todo» eligiendo esa raíz;
   en Linux: `unzip -n /ruta/SmartCity_DATASET_COMPLETO_PRIVADO.zip`.
3. Si el ZIP trae documentación/código antiguo, conservar el código de la rama de entrega.
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

- **PostgreSQL de entrega:** `sprint1/postgres/schema_v2_3nf.sql`, `queries_v2_3nf.sql` y [análisis de impacto](sprint1/postgres/impacto_3nf.md). El DDL común y `contract_v2.sql` conservan la reproducción histórica.
- **MongoDB de entrega:** `sprint1/basico/consultas_mongodb_v2.js` y `cargar_mongodb_v2.js` conservan las consultas y cargas públicas. El [laboratorio académico](sprint1/mongodb/academico/README.md) aporta MG01 por sensor y MG07 por tipo con datos sintéticos, además de consultas narrativas.
- **Informe:** [PDF final de 9 páginas](docs/avance_1/SmartCity_Sprint1_Entrega.pdf),
  [LaTeX autocontenido](docs/avance_1/SmartCity_Sprint1_Entrega.tex) y la matriz de consultas.
- **Estado y distribución:** `docs/equipo/ESTADO_SPRINT1.md`. Los ZIP, `raw/`,
  `private_results/`, `.env` y las credenciales se mantienen fuera de Git; el acceso
  al paquete privado está restringido al equipo.

**Resultados masivos confirmados:** PostgreSQL normalizado PASS con 748.889 filas
en `sprint1/postgres/evidencias/3nf/20261028T071812-55791345.json`.
La ejecución PostgreSQL v2 anterior conserva también 748.889 filas
(`execution-0652c6cd8bbc.json`). MongoDB v2 alcanzó PASS con 748.889 lecturas
(`execution-d26e40706dcd.json`). Estos dos últimos informes se encuentran bajo
`research/datasets/results/expanded-v2-2025-01/`. MongoDB acredita MG01–MG10,
replay, CRUD aislado, índices/validadores y reconciliación actual contra la
referencia PostgreSQL; ver [cierre MongoDB](sprint1/mongodb/evidencia_final_mongodb.md).
Las bases de prueba se eliminan:
estos comandos no dejan un servidor persistente para presentar ni cargan el compartido.

## Alcance

La aclaración docente del 28/10/2026 comunicada al equipo fija la **«Sección de
PostgreSQL y MongoDB»**, sin rúbrica independiente. El
[alcance documentado](docs/equipo/ALCANCE_CONFIRMADO_SPRINT1.md) toma como referencia
principal «Uso de PostgreSQL» y «Uso de MongoDB» del enunciado (pp. 8–12): modelos,
justificación, 3FN, tablas/relaciones/llaves, índices, SQL básico/relacional/analítico
y avanzado, diez consultas por motor, documentos, siete operaciones CRUD y
Aggregation Framework. Incluye información dinámica no estructurada, cuya
cobertura se demuestra con textos sintéticos separados; no basta usar BSON.
El almacenamiento distribuido mencionado expresamente en MongoDB sigue sin
demostración y no se excluye automáticamente del Sprint 1.

Los mínimos de **100.000 registros PostgreSQL y 500.000 documentos MongoDB** se
consideran objetivos del avance y están acreditados por las cargas v2. La corrección normalizada separa las dependencias de fuente, reloj y contrato;
la prueba formal y las nuevas ejecuciones se registran separadamente de los PASS
históricos. Se conservan las limitaciones semánticas de dispositivos físicos. Los aspectos ambiguos se marcan como
**transversales o pendientes de confirmación**.

Hadoop/HDFS, Spark, el dashboard completo, los análisis distribuidos y la
comparación final entre cuatro motores corresponden a la continuación de noviembre.

La ruta siguiente prueba las diez consultas SQL con fixtures controladas y añade
una demostración complementaria SQL/Mongo de tres ejemplos. No sustituye todos
los requisitos. El [estado](docs/equipo/ESTADO_SPRINT1.md) y la
[matriz de consultas](docs/equipo/MATRIZ_CONSULTAS_SPRINT1.md) indican lo pendiente.

## PostgreSQL normalizado de entrega

El [E-R completo](docs/arquitectura/diagrama_3nf.md) incluye catorce tablas,
con tipos de dispositivo independientes de magnitudes y asignaciones sensor–canal
separadas. La [matriz histórica de atributos](https://github.com/Alpizar28/SmartCity/blob/5eb3db7/docs/avance_1/secciones/06-equivalencias.tex)
representa los 17 atributos mínimos. La instancia nativa es temporal, propia,
sin TCP ni conexión a bases compartidas:

```bash
python scripts/validar_postgresql_3nf.py --sample 1000
python scripts/validar_postgresql_3nf.py
```

Requiere los binarios ya instalados de PostgreSQL 16 y el entorno Python de
investigación. [Evidencias nuevas](sprint1/postgres/evidencias/3nf/): cada informe
lleva su SHA-256. Las siguientes entradas conservan la reproducción anterior;
`--datos` no sustituye esta validación normalizada.

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

**Suite offline vigente:** 65 pruebas Python y dos archivos de pruebas Node.
Las diez consultas SQL y la integración de práctica cuentan con evidencia nativa
anterior de consultas, índices, replay, cuarentena, CRUD, respaldo/restauración y
concurrencia PostgreSQL acotada. La suite offline no vuelve a ejecutar esos motores
ni acredita clientes Python con autenticación real.

## Archivos para explicar en clase

- PostgreSQL de entrega: `sprint1/postgres/schema_v2_3nf.sql` y `queries_v2_3nf.sql`.
- PostgreSQL histórico: `research/datasets/scripts/phase5_postgresql.sql`,
  `sprint1/postgres/queries.sql` y `contract_v2.sql`, conservados para reproducibilidad.
- SQL de práctica: `schema_proposal.sql`, `staging_queries.sql` y `staging.sql`
  dentro de `sprint1/postgres/`; solo para el esquema `sprint1`.
- MongoDB de entrega: `sprint1/basico/cargar_mongodb_v2.js`,
  `consultas_mongodb_v2.js` y `crud_mongodb.js`.
- MongoDB de práctica: `sprint1/mongodb/validator.js`, `indexes.js`, `queries.js` y `staging.js`.
- Ejemplos comentados y CRUD: [sprint1/basico](sprint1/basico/README.md).

PG07 evalúa enero de 2025 en Madrid y excluye sensores sin vínculo a un canal:
una relación desconocida no significa falta de actividad. La prueba incluye un
sensor con lectura en el inicio incluido y otro solo en el final excluido.
Su PASS con fixtures no acredita inventario físico ni cierra el bloqueo de datos anuales.

Para consultar el modelo normalizado en una base **local ya preparada**:

```bash
PGOPTIONS='-c default_transaction_read_only=on' \
psql -X --set=ON_ERROR_STOP=1 --single-transaction \
  --host=127.0.0.1 --port=5433 --username=smartcity \
  --dbname=smartcity --file=sprint1/postgres/queries_v2_3nf.sql
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

El [cierre anual histórico](https://github.com/Alpizar28/SmartCity/blob/5eb3db7/docs/equipo/CIERRE_VALIDACION_SPRINT1.md) registra 1.076.813
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
el [intérprete oficial de históricos de tráfico](https://datos.madrid.es/dataset/208627-0-transporte-ptomedida-historico/resource/208627-81-transporte-ptomedida-historico/download/208627-81-transporte-ptomedida-historico.pdf), pp. 4–5, documenta su semántica.
La revisión implementada se identifica mediante `sprint1/postgres/contract_v2.sql`,
`sprint1/basico/preparar_v2.py` y las evidencias v2; la propuesta previa se conserva
como antecedente, no como especificación definitiva.

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
