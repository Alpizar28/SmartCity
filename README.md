# SmartCity Analytics

Proyecto académico SmartCity Analytics: investigación, preparación y análisis de datos urbanos para justificar el uso de PostgreSQL, MongoDB, Hadoop/HDFS y Apache Spark en CE-3191 Base de Datos. La identificación administrativa del curso debe confirmarse: el nombre del enunciado PDF dice CE3101.

**Estado real:** fases 0–5 de investigación y preparación documentadas; Fase 6 organiza la documentación. Madrid es una **recomendación condicionada**, pendiente de ratificación del equipo y decisiones docentes. Hay diseños preliminares y pruebas nativas locales desechables, no modelos definitivos ni cargas en las bases compartidas. Hadoop, Spark y Streamlit/dashboard **no están implementados**.

## Navegación

- [Documentación por temática](docs/README.md) y [texto listo para el informe](docs/academico/texto_para_informe.md).
- [Selección de Madrid](docs/datasets/seleccion_dataset.md), [fuentes y licencias](docs/datasets/fuentes_y_procedencia.md), [calidad y límites](docs/datasets/calidad_y_limitaciones.md).
- [Modelos preliminares](docs/arquitectura/modelos.md), [diagramas Mermaid](docs/arquitectura/diagramas.md) y [pipeline/reproducción](docs/arquitectura/pipeline.md).
- [Guía del equipo](docs/equipo/guia_integrantes.md), [preguntas al profesor](docs/equipo/preguntas_profesor.md) y [ADR condicionado](docs/decisiones/ADR-001-madrid.md).
- [Índice de evidencias de fases 0–5](docs/datasets/indice_evidencias.md). El [README de investigación](research/datasets/README.md) conserva su estado histórico de fases 0–1, no el estado actual.

## Arquitectura y organización

Originales inmutables → validación → normalización temporal → IDs deterministas → catálogos compartidos → PostgreSQL y MongoDB → exportaciones posteriores CSV/Parquet. El esquema relacional separa sitio, dispositivo físico, canal y observación; MongoDB mantiene un documento por intervalo multivariable de tráfico. No hay FK ni transacción automática entre motores.

El núcleo propuesto es enero de 2025: **832.668 observaciones estructuralmente elegibles**, no una carga definitiva. Véanse los [conteos y su evidencia](docs/datasets/calidad_y_limitaciones.md). Accidentes de 2026 y energía mensual permanecen separados.

| Ruta | Uso actual |
|---|---|
| `postgres/init/` | Reservada y sin scripts de inicialización; conservar estructura |
| `mongodb/init/` | Reservada y sin scripts de inicialización; conservar estructura |
| `data/` | Datos locales ignorados salvo marcador `.gitkeep` |
| `research/datasets/` | Investigación histórica, scripts, pruebas y evidencia técnica |
| `docs/` | Documentación académica, arquitectura, decisiones y handoff |

Los scripts preliminares están en [DDL PostgreSQL](research/datasets/scripts/phase5_postgresql.sql), [consultas SQL](research/datasets/scripts/phase5_postgresql_queries.sql) y [prueba MongoDB/CRUD/agregaciones](research/datasets/scripts/phase5_mongo_test.js). **No copiarlos a `init/` ni ejecutarlos sobre bases compartidas sin revisión y autorización.** No crear una carpeta duplicada `postgresql/`.

## Infraestructura local existente

Las instrucciones originales se conservan abajo. Ejecutarlas solo en un equipo de desarrollo autorizado, nunca en el servidor compartido desde esta fase. Compose inicia únicamente PostgreSQL y MongoDB; no aplica los diseños de investigación. `compose.yaml` no monta actualmente las carpetas `init/`.

## Arquitectura

```text
Integrante (Docker local)                 Entorno compartido
┌─────────────────────────┐              ┌─────────────────────────────┐
│ PostgreSQL + MongoDB    │              │ Coolify / Docker Compose    │
│ datos locales aislados  │              │ PostgreSQL + MongoDB        │
└─────────────────────────┘              │ acceso privado por Tailscale│
                                         └──────────────┬──────────────┘
                                                        │
                                             Tailnet privada del equipo
                                                        │
                                    PostgreSQL 100.75.216.1:5434
                                    MongoDB    100.75.216.1:27018
```

GitHub y la rama `main` son la fuente de verdad de la infraestructura. La configuración del recurso Coolify, las credenciales y las reglas de acceso de Tailscale se administran fuera del repositorio.

## Tecnologías y versiones

| Tecnología | Uso | Versión / estado |
| --- | --- | --- |
| PostgreSQL | Base relacional | `postgres:16.6-alpine` |
| MongoDB | Base documental | `mongo:7.0.16` |
| Docker Compose | Orquestación local y del recurso | Compose v2 compatible |
| Coolify | Despliegue del entorno compartido | Configuración externa al repositorio |
| Tailscale | Acceso privado al entorno compartido | Configuración y ACL externas al repositorio |
| Hadoop/HDFS, Spark/PySpark, Streamlit | Fases posteriores | Aún no implementados |

Las imágenes de PostgreSQL y MongoDB están fijadas en `compose.yaml` y son compatibles con `amd64` y `arm64`.

## Estructura actual

```text
SmartCity/
├── compose.yaml
├── .env.example
├── .gitignore
├── README.md
├── data/
│   └── .gitkeep
├── docs/
│   ├── .gitkeep
│   └── README.md
├── mongodb/
│   └── init/
│       └── .gitkeep
└── postgres/
    └── init/
        └── .gitkeep
```

Los directorios `postgres/init/` y `mongodb/init/` están reservados para fases posteriores; actualmente no contienen scripts de inicialización ni modelos de datos. `data/` está reservado para datos locales y se ignora en Git, salvo su marcador `.gitkeep`.

## Desarrollo local

### Requisitos

- Git
- Docker Desktop con Docker Compose v2 (Windows), o Docker Engine con Docker Compose v2 (Linux)

### Inicio rápido

```bash
<<<<<<< HEAD
git clone https://github.com/Alpizar28/SmartCity.git
cd SmartCity
cp .env.example .env
# Edita .env y sustituye los valores de contraseña de ejemplo.
docker compose config
=======
if [ ! -e .env ]; then cp .env.example .env; fi
# Edit .env and replace all passwords before running the stack.
>>>>>>> origin/docs/dataset-research
docker compose up -d
docker compose ps
```

En PowerShell:

```powershell
<<<<<<< HEAD
git clone https://github.com/Alpizar28/SmartCity.git
Set-Location SmartCity
Copy-Item .env.example .env
# Edita .env y sustituye los valores de contraseña de ejemplo.
docker compose config
=======
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Edit .env and replace all passwords before running the stack.
>>>>>>> origin/docs/dataset-research
docker compose up -d
docker compose ps
```

El archivo `.env` no se versiona. Los valores de ejemplo son solo para desarrollo local y no deben usarse en el entorno compartido.

### Servicios locales

| Servicio Compose | Puerto interno | Acceso local por defecto |
| --- | ---: | --- |
| `postgres` | `5432` | `127.0.0.1:5433` |
| `mongodb` | `27017` | `127.0.0.1:27017` |

Los puertos se configuran mediante `.env`:

```env
POSTGRES_BIND_ADDRESS=127.0.0.1
POSTGRES_PORT=5433
MONGODB_BIND_ADDRESS=127.0.0.1
MONGODB_PORT=27017
```

El bind por defecto a `127.0.0.1` permite conectar herramientas del equipo anfitrión —por ejemplo DBeaver, `psql` o MongoDB Compass— sin publicar las bases en la red local.

Para detener los servicios y conservar los datos:

```bash
docker compose down
```

Para borrar **deliberadamente** los datos locales de ambas bases:

```bash
docker compose down -v
```

> `docker compose down -v` elimina los volúmenes locales del proyecto. No usarlo si se desea conservar información de desarrollo.

## Qué configura Docker Compose

`compose.yaml` declara exclusivamente los servicios `postgres` y `mongodb`.

| Aspecto | PostgreSQL | MongoDB |
| --- | --- | --- |
| Imagen | `postgres:16.6-alpine` | `mongo:7.0.16` |
| Volumen persistente | `postgres_data` en `/var/lib/postgresql/data` | `mongodb_data` en `/data/db` |
| Límite de memoria | 512 MiB | 512 MiB |
| Límite de CPU | 0.25 CPU | 0.25 CPU |
| Healthcheck | `pg_isready` | `mongosh` con `ping` autenticado |

Ambos servicios comparten la red Docker `smartcity-network`. Docker Compose aplica un prefijo de proyecto a la red y a los volúmenes, evitando nombres globales fijos y colisiones entre entornos.

Variables requeridas por Compose:

```env
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_BIND_ADDRESS=
POSTGRES_PORT=

MONGO_INITDB_ROOT_USERNAME=
MONGO_INITDB_ROOT_PASSWORD=
MONGODB_BIND_ADDRESS=
MONGODB_PORT=
```

No se deben agregar contraseñas, tokens ni archivos `.env` a Git.

## Entorno compartido: Coolify

El recurso compartido se despliega desde el repositorio mediante Coolify. La configuración del recurso, las variables con secretos, los volúmenes gestionados y los redeploys pertenecen a Coolify; no se reproducen desde el README ni deben copiarse a `.env` local.

Para un recurso Docker Compose en Coolify:

- **Base Directory:** `/`
- **Docker Compose File Location:** `compose.yaml`
- No configurar dominios ni rutas de proxy para las bases de datos.
- Mantener las contraseñas únicamente como variables/secretos del recurso.

Los valores específicos del entorno compartido son:

```env
POSTGRES_BIND_ADDRESS=100.75.216.1
POSTGRES_PORT=5434
MONGODB_BIND_ADDRESS=100.75.216.1
MONGODB_PORT=27018
```

Estos valores son del servidor compartido. No deben reemplazar los valores locales de `.env` de cada integrante.

## Acceso privado por Tailscale

El servidor compartido tiene esta identidad en la tailnet:

```text
Hostname: jokemvnic
Tailscale IP: 100.75.216.1
```

Las bases del recurso compartido están enlazadas a la interfaz Tailscale, no a `0.0.0.0`:

| Servicio | Host | Puerto |
| --- | --- | ---: |
| PostgreSQL | `100.75.216.1` | `5434` |
| MongoDB | `100.75.216.1` | `27018` |

La política de Tailscale del proyecto debe permitir a los miembros únicamente TCP `5434` y TCP `27018` hacia este servidor. SSH por Tailscale (`22`), Coolify y el resto de puertos del servidor deben permanecer bloqueados por las ACL de la tailnet.

### Conectar un equipo a la tailnet

Un administrador debe invitar al integrante como miembro de la tailnet. Tras instalar Tailscale en el equipo local, asociarlo con:

```bash
sudo tailscale up
tailscale status
```

La autenticación se completa mediante la URL que muestra el comando. No guardar enlaces de invitación ni claves de autenticación en el repositorio.

### Verificar conectividad privada

Desde un equipo ya conectado a la tailnet:

```bash
nc -vz 100.75.216.1 5434
nc -vz 100.75.216.1 27018
```

En PowerShell:

```powershell
Test-NetConnection 100.75.216.1 -Port 5434
Test-NetConnection 100.75.216.1 -Port 27018
```

No se debe intentar acceder a SSH por la IP Tailscale; debe estar bloqueado por la política de la tailnet.

## Conexiones a las bases compartidas

Solicita las contraseñas al administrador por un medio privado. No las copies en este documento, en issues, en pull requests ni en commits.

### PostgreSQL

```text
Host:     100.75.216.1
Port:     5434
Database: smartcity
Username: smartcity
```

Con `psql`:

```bash
psql -h 100.75.216.1 -p 5434 -U smartcity -d smartcity
```

### MongoDB

```text
Host:                    100.75.216.1
Port:                    27018
Username:                smartcity_admin
Authentication Database: admin
```

En MongoDB Compass, configurar los campos anteriores y proporcionar la contraseña recibida por canal privado.

## Troubleshooting

### Docker Compose no inicia localmente

```bash
docker compose config
docker compose ps
docker compose logs postgres mongodb
```

Confirma que `5433` y `27017` estén disponibles o cambia `POSTGRES_PORT` y `MONGODB_PORT` en tu `.env` local.

### Una base no está healthy

```bash
docker compose ps
docker compose logs postgres mongodb
```

Comprueba que las variables requeridas estén presentes en `.env`. Si se modificaron las credenciales después de inicializar un volumen local, crea un entorno local nuevo solo si no necesitas sus datos:

**Destructivo: únicamente para datos locales propios y con autorización explícita. Nunca usar sobre volúmenes compartidos.**

```bash
docker compose down -v
docker compose up -d
```

### No hay acceso al entorno compartido

1. Verifica que Tailscale esté conectado: `tailscale status`.
2. Prueba los puertos `5434` y `27018` con los comandos anteriores.
3. Si fallan, solicita al administrador que revise las ACL de Tailscale y el estado del recurso en Coolify.
4. Si los puertos responden pero el cliente rechaza la conexión, revisa usuario, contraseña, base de datos y —para MongoDB— la base de autenticación `admin`.

## Flujo de trabajo

```text
git pull
  ↓
trabajar en una rama
  ↓
probar localmente con Docker Compose
  ↓
commit y push
  ↓
pull request
  ↓
merge aprobado a main
  ↓
redeploy controlado en Coolify
```

El entorno compartido es de integración. Cada integrante debe poder desarrollar y probar localmente sin depender de él.

<<<<<<< HEAD
## Seguridad

No subir al repositorio:

- `.env` ni contraseñas.
- Tokens, claves de autenticación o enlaces de Tailscale.
- Llaves privadas SSH (`.pem`, `.key`).
- Credenciales de Oracle, Coolify u otros proveedores.
- Dumps de bases de datos con datos sensibles.
- Volúmenes Docker o datasets locales grandes, salvo acuerdo explícito del equipo.

Antes de un commit, revisar:

```bash
git status
git diff --cached
```

## Próximas fases

1. Modelado relacional en PostgreSQL.
2. Modelado documental en MongoDB.
3. Carga y generación de datasets.
4. Hadoop/HDFS.
5. Spark/PySpark.
6. Streamlit.

Ninguno de estos componentes está implementado todavía.
=======
Do not add models, schemas, seed data, or initialization scripts until the data-design phase.

## Reproducción de la investigación y pruebas

Desde la raíz, con el entorno aislado existente y los snapshots locales autorizados:

```bash
cd research/datasets
.venv/bin/python scripts/phase5_prepare.py --dry-run
.venv/bin/python -m pytest tests -q --junitxml=results/phase6/tests.xml
.venv/bin/python scripts/phase6_validate_docs.py
```

Las 82 pruebas de fases 0–5 incluyen validación de datos locales y resultados nativos guardados; **no lanzan motores ni reemplazan una nueva corrida nativa**. Un clon no incluye `raw/`, `private_results/`, PDFs originales ni sus transcripciones completas: las pruebas de evidencia necesitan esos insumos. La [guía de reproducción](docs/arquitectura/pipeline.md) explica dependencias, temporales exclusivos, limitaciones del clon y comandos nativos opcionales; no descarga automáticamente datasets ni imágenes.

## Entorno compartido y colaboración segura

El servidor compartido de Coolify y el acceso privado por Tailscale están descritos por el usuario y el plan del equipo, **no verificados remotamente en estas fases**. Solicitar credenciales al administrador por un canal privado; no publicarlas en Git, capturas ni logs. No se conocen aquí reglas de redeploy, rama monitorizada ni configuración efectiva del panel. Un futuro push o merge debe coordinarse con José antes de publicarse.

Para colaborar: revisar la [guía de integrantes](docs/equipo/guia_integrantes.md), trabajar en ramas propias, conservar las fases históricas y enlazar cada afirmación a su evidencia. Revisar `git status`, el diff, [.gitignore](.gitignore) y los [controles de publicación](docs/equipo/revision_repositorio.md) antes de seleccionar archivos; no usar `git add .` sin auditoría.

Pendientes: aprobación conjunta/docente, unidades y relojes de meteorología/tráfico, CRS y geografía histórica, identidad física/instalación/estado/responsables, usuarios consentidos, MG04/MG05/MG08, mínimos cargados en el contrato aceptado, respaldo/restauración, ejecución distribuida y dashboard. La documentación de esta fase no autoriza despliegues, síntesis masiva ni implementación definitiva.
>>>>>>> origin/docs/dataset-research
