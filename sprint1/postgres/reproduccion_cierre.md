# Reproducción segura del cierre PostgreSQL

## Versión, requisitos y seguridad

Base comprobada: rama `main`, commit
`b77e5497fa28f8c2b483b06e2e593d96b7bd0a5d`, más los cambios locales de este cierre.
Comparar `source_hashes` de cada JSON antes de citarlo. Cambiar código invalida
la identidad de una ejecución, no autoriza editar sus hashes o convertir FAIL en PASS.

Comandos desde la raíz del repositorio. Python 3.10+ para herramientas de cierre,
stdlib/zoneinfo disponibles; **no requieren pandas, pyarrow, psycopg ni instalación**.
Docker local para SQL; imagen existente. Las suites completas también requieren
Node.js >=18, MongoDB y los pins que se indican más abajo. No usar sudo ni un DSN.

Los harnesses de cierre usan explícitamente `unix:///var/run/docker.sock`,
contenedores propios con nombre aleatorio, red none, sin puertos, recursos
limitados, autenticación de prueba aislada y datos PostgreSQL en tmpfs. No leen
credenciales de `.env`. Nunca apuntar estas fixtures a un servidor compartido.

En esta máquina existe `postgres:16-alpine` (PostgreSQL **16.15**); no existe
el pin `postgres:16.6-alpine`. Se eligió explícitamente la imagen existente con
`SMARTCITY_PG_IMAGE`, sin retag ni descarga; el ID de imagen se registra.
No hay Node.js/LaTeX disponibles y no se instalaron. Las dependencias de datos
de los reproductores masivos tampoco están disponibles en el entorno del proyecto.

Preflight de solo lectura:

```bash
git status --short --branch
git rev-parse HEAD origin/main
df -h . /tmp/opencode
command -v python3 docker node pdflatex latexmk
docker --host unix:///var/run/docker.sock info --format '{{.ServerVersion}}'
docker --host unix:///var/run/docker.sock image inspect postgres:16-alpine
```

## 1. Offline sin archivos privados

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/sprint1 -p 'test_*.py' -v
```

Incluye los verificadores nuevos de archivos seguros, rutas SQL y correspondencia
entre evidencia persistida y código actual. Debe acabar en `OK`; cualquier
`FAILED`/excepción es fallo. No conecta a bases. Las pruebas estáticas LaTeX no
sustituyen compilar.

Entrada general existente (Python + Node):

```bash
bash scripts/validate_sprint1.sh
```

En esta sesión se ejecutó y se detuvo después de aprobar Python por falta de
Node.js: **no** se declara PASS de esa entrada completa. No requiere Docker ni
el paquete grande en su modalidad offline.

## 2. SQL exacto PG01–PG10 y PG07 controlada, sin paquete privado

```bash
SMARTCITY_PG_IMAGE=postgres:16-alpine PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_sprint1_sql.py
```

Sin la variable usa el pin original 16.6, que debe existir localmente; siempre
`--pull never`. Ejecuta DDL v1, 9 controles de esquema, 14 controles SQL existentes,
fixture canónica y diez resultados esperados. Luego otra transacción amplía solo
PG07 y ejecuta el mismo SELECT parseado. Ambas fixtures terminan en ROLLBACK,
con conteo cero de remanentes. Se elimina el contenedor.

Salida: `/tmp/opencode/smartcity-s1-sql-*.json`; último mensaje
`Sprint 1 canonical SQL: PASS`, exit code 0, `status=PASS`,
`container_removed=true`, `fixtures_rolled_back=true`, `pg07_extended.rollback=true`.
Las filas fabricadas no son evidencia de mediciones reales.

## 3. Auditoría completa del ZIP v2, sin base de datos

No extraer el paquete completo ni ejecutar sus scripts. El ZIP contiene además
originales restringidos de personas ajenos a PostgreSQL: no versionarlo ni mostrar
sus filas. El auditor publica solo metadatos/hashes/conteos y cabeceras pertinentes.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/auditar_cierre_postgresql.py \
  --paquete /home/dburger/Descargas/SmartCity_DATASET_COMPLETO_PRIVADO.zip \
  --salida /tmp/opencode/auditoria-pg-nueva.json
```

El nombre de salida debe ser nuevo; el script rechaza reemplazar evidencia.
`--paquete` es configurable: no presupone una copia dentro del repositorio.
Necesita leer 1,47 GB de JSONL y otros derivados desde el ZIP, memoria para los
IDs y unos 408 MB de disco temporal para el ledger, más margen. La lectura completa
tardó aproximadamente tres minutos en esta máquina. CRC y SHA se verifican al leer.
No descarga ni carga observaciones. Valida código/manifiestos/archivos y ledger;
compara independientemente totales/muestras del PASS masivo PostgreSQL v2 vigente.
El temporal propio se elimina automáticamente.

PASS: exit code 0, `status=PASS`, `accepted=748889`, by_source 91959/656930,
`duplicates=0`, diez `historical_total_and_sample_match=true`. No usar FAIL como
evidencia aprobada ni confundirlo con validación masiva de ambos motores.

## 4. SQL v2 con datos reales seleccionados, no carga masiva

```bash
SMARTCITY_PG_IMAGE=postgres:16-alpine PYTHONDONTWRITEBYTECODE=1 \
  python3 scripts/probar_cierre_postgresql.py \
  --paquete /home/dburger/Descargas/SmartCity_DATASET_COMPLETO_PRIVADO.zip \
  --salida /tmp/opencode/subconjunto-pg-nuevo.json
```

Lee catálogos/demo sellados y selecciona **todas** las lecturas de aire aceptadas
con original_time el 1 de enero más los primeros 64 intervalos de tráfico. Resultado
seleccionado: 2.907 filas (2.843 aire, 64 tráfico). Ejecutar primero auditoría completa
para acreditar el paquete; el harness pequeño verifica hashes de catálogos/demo,
no pretende sustituir la auditoría de todo el JSONL. Tampoco usa esquema v1 para
recibir datos v2: aplica `contract_v2.sql` en la base nueva antes de los catálogos.

Ejecuta diez consultas exactas con comparación completa Python, resumen de aire
canónico, complemento CTE/DENSE_RANK, catálogo de restricciones/NOT NULL/triggers
e índices, dos EXPLAIN ANALYZE en READ ONLY y reproducción reversible de tres
limitaciones DDL. El SELECT de evidencia no cambia las lecturas y el contenedor
temporal completo se destruye al terminar.

PASS: exit 0, `status=PASS`, `container_removed=true`, diez `python_match=true`.
**PG09 del subconjunto=126**, mientras H completo=360. Los contadores administrativos
son de los mismos catálogos/demo completos. Los marcadores de limitaciones aceptadas
documentan defectos actuales del DDL; no son una certificación de integridad completa.

## 5. Reproducción completa existente (no ejecutada en este cierre)

Se inspeccionaron los scripts antes de decidir no repetir cargas innecesarias.
En un entorno que **ya** tenga los prerrequisitos:

```bash
bash scripts/validate_sprint1.sh --engines
bash scripts/validate_sprint1.sh --datos
```

`--engines` ejecuta unidades, canónico y práctica complementaria SQL/Mongo,
incluidos respaldo/restauración. Requiere `postgres:16.6-alpine` y `mongo:7.0.16`
locales, además de Node. `--datos` añade preparación, muestra Mongo, carga y replay
masivos v2 y verificación conjunta. Necesita snapshots en
`research/datasets/raw/`, derivados y catálogos de inventario en
`research/datasets/private_results/`, y Python de datos en
`research/datasets/.venv/bin/python` (o `PYTHON_DATOS` apuntando a entorno existente
con las dependencias fijadas). La preparación puede producir archivos grandes:
no se ejecuta solo porque el ZIP esté disponible.

Los comandos reales para una generación ya preparada son:

```bash
research/datasets/.venv/bin/python scripts/validar_v2.py --generacion expanded-v2-2025-01 --motor postgresql
research/datasets/.venv/bin/python scripts/verificar_v2.py --generacion expanded-v2-2025-01
```

El primero genera un **nuevo** `execution-*.json` bajo results/expanded-v2-2025-01,
sin sobrescribir anteriores. El segundo exige PASS vigente de **ambos** motores,
igualdad de huellas y limpieza: no puede aprobarse en main solo con el PASS SQL.
Estos scripts esperan la estructura privada preparada, no leen directamente ZIP;
no se ofrecen comandos de extracción indiscriminada. Si se necesita reproducir
la carga completa, preparar una ubicación privada revisada y verificar capacidad
antes de copiar/montar archivos. No instalar dependencias sin autorización.

Benchmark histórico v1 (otro alcance, costoso; tampoco ejecutado ahora):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B tests/sprint1/validate_real_postgres.py --benchmark
```

Necesita `private_results/expanded-2025`, resultados/manifiesto v1 y su imagen
local. No combinarlo con v2 ni presentar sus tiempos como rendimiento v2.

## 6. LaTeX y limpieza

El `Makefile` existente en docs/avance_1 usa latexmk. Si el entorno ya lo tiene,
compilar desde esa carpeta con salida externa (sin instalar distribuciones):

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=/tmp/opencode/smartcity-latex-nuevo main.tex
```

El comando se documenta como reproducción, **no** como ejecutado en esta sesión.
Aquí no había herramientas LaTeX; solo controles estáticos de llaves, entornos,
inputs y citas. Revisar visualmente tablas, referencias y portada al compilar.

Limpieza de solo lectura:

```bash
docker --host unix:///var/run/docker.sock ps -a --filter label=smartcity.scope=sprint1-canonical-sql
docker --host unix:///var/run/docker.sock ps -a --filter label=smartcity.scope=postgres-close
git diff --check
git status --short
git ls-files --others --exclude-standard
git check-ignore research/datasets/private_results/expanded-v2-2025-01/accepted.extjsonl
```

Los dos filtros deben quedar sin contenedores de estas pruebas. Los harnesses
usan `--rm` y tmpfs, no persistencia del usuario. No ejecutar prune, no eliminar
contenedores/volúmenes ajenos ni reemplazar manifiestos históricos para limpiar.
Los originales permanecen en Descargas, y los directorios privados siguen ignorados.
