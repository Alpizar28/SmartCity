# SmartCity Analytics

Proyecto académico de **Bases de Datos — II Semestre 2026**. El código administrativo del curso figura de forma inconsistente como `CE-3191` y `CE3101` en evidencia histórica; está pendiente de confirmación docente y no se adopta ninguno como definitivo aquí.

## Estado y contrato vigente

> **Entrega Sprint 1:** la guía concreta para la asignación «Sección de
> PostgreSQL y Mongo» está en [ENTREGA_SPRINT1.md](ENTREGA_SPRINT1.md). Es la
> ruta recomendada para revisión y demostración; Spark/Hadoop y el resto de
> fases no forman parte de esa demostración.

**Ampliación real de Sprint 1:** [entrega técnica anual](docs/equipo/AMPLIACION_REAL_SPRINT1.md). El CSV oficial ya disponible permite **1.076.813 observaciones aceptadas de aire de 2025**, con cuarentena separada y carga completa local reproducible. No sumar la muestra o enero otra vez. La segunda fuente de mediciones y Spark siguen pendientes; los manifiestos de los motores acreditan únicamente las pruebas efectivamente terminadas.

Inicio para el equipo: [instrucciones de Daniel, Kembly y Fernanda](docs/equipo/ENTREGA_TECNICA_SPRINT1.md). Segunda fuente: [propuesta `madrid-draft-v2`](docs/decisiones/PROPUESTA_MADRID_DRAFT_V2.md), pendiente de aprobación y sin implementación incompatible.

**Validación completa terminada:** [cierre y cumplimiento verificable](docs/equipo/CIERRE_VALIDACION_SPRINT1.md): 1.076.813 registros en cada motor local, replay completo sin duplicados e igualdad comprobada. Los mínimos de volumen de PostgreSQL y MongoDB se acreditan localmente; dos fuentes aceptadas, inventario físico y Spark siguen pendientes. Contenedores desechables eliminados; servidor compartido no modificado.

- **Contrato común implementado en esta rama:** [`madrid-draft-v1`](docs/equipo/CONTRATO_UNIFICADO.md), esquema SQL `smartcity`, generación `unified-v1`; pendiente de revisión del equipo y sin autorización de carga compartida.
- **Contrato anterior:** [`madrid-draft-v1-frozen`](CONTRATO_PROVISIONAL_DATASET.md), obsoleto por la especificación de integración del 14/10/2026. Los resultados de Fase 5 se preservan como evidencia histórica, no como prueba de la implementación nueva.
- Madrid para enero de 2025 tiene **832.668 observaciones estructuralmente elegibles** en evidencia local; esto **no** significa que estén cargadas en PostgreSQL ni MongoDB compartidos.
- Hadoop/HDFS, Spark y Streamlit no están implementados ni ejecutados. La recomendación de Madrid y las excepciones académicas siguen condicionadas a decisiones del equipo, evidencia técnica y validación docente.

El estado operativo del Sprint 1 está en [`docs/equipo/ESTADO_SPRINT1.md`](docs/equipo/ESTADO_SPRINT1.md). Las preguntas breves que se envían al profesor están en [`PREGUNTAS_PROFESOR.md`](PREGUNTAS_PROFESOR.md); el seguimiento detallado está en [`docs/equipo/preguntas_profesor.md`](docs/equipo/preguntas_profesor.md).

## Estructura

| Ruta | Propósito y estado |
|---|---|
| `compose.yaml`, `.env.example` | Infraestructura local de PostgreSQL y MongoDB; no aplica esquemas del dataset. |
| `postgres/init/`, `mongodb/init/` | Reservadas y vacías salvo `.gitkeep`. No añadir DDL/DML aún. |
| `CONTRATO_PROVISIONAL_DATASET.md` | Contrato provisional vigente y límites semánticos. |
| `research/datasets/` | Investigación, scripts, pruebas y evidencia histórica de fases 0–5. |
| `docs/` | Guías, decisiones, arquitectura preliminar y estado del equipo. |
| `scripts/validate_repo.sh` | Validación local mínima de integridad documental y Python. |
| `sprint1/` | Núcleo local nuevo, validadores y propuestas SQL/MongoDB con integración desechable acotada. |
| `sprint1/basico/` | Código sencillo de estudiante: consultas comentadas, CRUD de práctica y carga local opcional. |
| `tests/sprint1/`, `scripts/validate_sprint1.sh` | Pruebas offline nuevas e independientes de la reproducción histórica. |
| `tests/integration/`, `scripts/test_sprint1_engines.py` | Integración nueva en contenedores locales desechables, sin red ni cargas masivas. |

Los scripts `phase5_postgresql.sql`, `phase5_postgresql_queries.sql` y `phase5_mongo_test.js` ahora implementan la unificación para **pruebas locales desechables**. Sus resultados anteriores en `results/phase5/` son históricos; los nuevos van a `results/unified-v1/`. No se copian a inicializadores ni se ejecutan contra bases compartidas. Reproducción y límites: [contrato común](docs/equipo/CONTRATO_UNIFICADO.md).

## Desarrollo local

### Requisitos

- Git.
- Docker Engine y Docker Compose v2 en Linux, o Docker Desktop con Compose v2 en Windows.

### Linux

```bash
git clone https://github.com/Alpizar28/SmartCity.git
cd SmartCity
cp .env.example .env
# Edita .env: reemplaza las contraseñas de ejemplo y ajusta puertos si están ocupados.
docker compose --env-file .env config
docker compose --env-file .env up -d
docker compose --env-file .env ps
```

### PowerShell

```powershell
git clone https://github.com/Alpizar28/SmartCity.git
Set-Location SmartCity
Copy-Item .env.example .env
# Edita .env: reemplaza las contraseñas de ejemplo y ajusta puertos si están ocupados.
docker compose --env-file .env config
docker compose --env-file .env up -d
docker compose --env-file .env ps
```

Por defecto los servicios se enlazan solo en `127.0.0.1`: PostgreSQL en el puerto host `5433` y MongoDB en `27017`. Si hay colisión, cambia `POSTGRES_PORT` o `MONGODB_PORT` en `.env`. No uses las contraseñas de `.env.example` fuera de tu máquina local.

Para detener el entorno local conservando datos:

```bash
docker compose --env-file .env down
```

`docker compose down -v` borra volúmenes **locales**. Úsalo solo si los datos son propios y prescindibles; nunca como instrucción para un entorno compartido.

## Reproducción de la investigación

La investigación requiere los snapshots locales autorizados y archivos no versionados (`raw/`, `private_results/` y, en algunos casos, PDFs originales). Los siguientes comandos no descargan datasets, no inician Spark/Hadoop y no usan credenciales remotas. En una copia nueva, crea primero el entorno y sus dependencias (esta instalación sí requiere acceso al repositorio de paquetes):

```bash
python3 -m venv research/datasets/.venv
research/datasets/.venv/bin/python -m pip install -r research/datasets/scripts/requirements.txt
```

Crear el entorno **no recupera los insumos históricos ausentes** ni garantiza que la suite histórica pase. `scripts/validate_repo.sh` usa `python3` del PATH: activa ese entorno antes de ejecutarlo.

```bash
cd research/datasets
.venv/bin/python scripts/phase5_prepare.py --dry-run
.venv/bin/python -m pytest tests -q
.venv/bin/python scripts/phase6_validate_docs.py
```

Las salidas de Fase 5 son evidencia histórica: muestran muestras locales acotadas y pruebas nativas desechables, no una carga definitiva ni un benchmark del servidor. Consulta [`docs/arquitectura/pipeline.md`](docs/arquitectura/pipeline.md) para requisitos y límites de reproducción.

### Núcleo nuevo del Sprint 1

Con Python 3.10+ y Node.js 18+, desde la raíz, sin instalar dependencias Python:

```bash
bash scripts/validate_sprint1.sh
```

Véase [`sprint1/README.md`](sprint1/README.md). Este comando no conecta a bases ni altera resultados históricos. Su PASS solo cubre pruebas unitarias/builders y controles estáticos de propuestas; no certifica motores, volumen, aceptación docente ni reproducción histórica.

La integración nativa ya se comprobó aparte con tres ejemplos publicados en
PostgreSQL 16.6/MongoDB 7.0.16 desechables. Para requisitos, ejecución y límites,
consulta [`sprint1/INTEGRACION.md`](sprint1/INTEGRACION.md). No acredita los mínimos
de volumen ni cumplimiento completo del avance.

## Colaboración segura

- Trabaja en una rama propia; revisa `git status` y el diff antes de añadir archivos.
- No subas `.env`, contraseñas, tokens, llaves, dumps, volúmenes ni snapshots privados. `.gitignore` ayuda, pero no sustituye la revisión humana.
- Los parámetros para el entorno compartido (host privado, puertos y credenciales) se solicitan al administrador por un canal privado. No se versionan aquí. Coolify, Tailscale y las bases compartidas no se administran desde este repositorio.
- No infieras un sensor físico desde un canal, estación o variable. El permiso docente para datos administrativos aleatorios se aplica a fixtures explícitamente sintéticos y separados; consulta el contrato común.
- Antes de preparar un PR, ejecuta `scripts/validate_repo.sh` y revisa [`docs/equipo/revision_repositorio.md`](docs/equipo/revision_repositorio.md).

## Seguridad

No versionar secretos, enlaces privados, credenciales, llaves SSH, archivos `.pem`/`.key`, dumps ni datos personales. Las credenciales de servicios compartidos solo se intercambian por un medio privado. No ejecutar cargas, migraciones, scripts de Fase 5 ni comandos administrativos contra servidores compartidos sin autorización expresa del equipo.

## Próximas fases

1. Cerrar evidencia técnica pendiente: unidades meteorológicas, relojes, CRS y vigencia geográfica.
2. Resolver con el profesor el alcance físico de sensores/canales y alertas. El permiso del 10/10 para atributos administrativos aleatorios está registrado, pero no confirma inventario físico, usuarios reales ni relojes.
3. Revisar las propuestas de `sprint1/` y diseñar la implementación definitiva; solo entonces crear migraciones o colecciones versionadas y autorizar pruebas locales desechables.
4. Planificar cargas locales y compartidas autorizadas con respaldo, reconciliación y pruebas.
5. Abordar HDFS/Spark y la interfaz en fases posteriores, con fuentes reales y validación independiente.
