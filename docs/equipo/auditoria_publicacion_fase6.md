# Auditoría final de publicación — Fase 6

## Dictamen

**APTO PARA PUBLICACIÓN documental, tras la corrección verificada del validador.** No significa aprobación del dataset ni autorización para publicar ahora. **Antes de cualquier push, José debe comprobar Coolify y el usuario debe autorizar la operación**: el riesgo de despliegue de una rama distinta de `main` continúa **NO VERIFICADO**.

La revisión no realizó staging, commit, push, merge, PR, despliegue ni conexiones a bases remotas. No inició PostgreSQL/MongoDB ni alteró infraestructura. La revisión fue local e independiente del sello anterior: releyó documentos/diffs, inspeccionó todos los candidatos, volvió a ejecutar pruebas y reprodujo un problema real en una copia de publicación sin datos privados.

## 1. Git y alcance revisado

- Rama: `docs/dataset-research`; `main` y HEAD siguen en `6ad86ce6ef43e200ed554f80100455ff04461d3c`. No hay commits nuevos ni archivos staged.
- Remoto configurado: `https://github.com/Alpizar28/SmartCity`; no se realizó fetch/push ni se verificó el estado remoto en vivo.
- Diff rastreado de Fase 6: `.gitignore`, `README.md`, `docs/README.md`. Documentos temáticos e investigación permanecen sin seguimiento porque las fases previas tampoco se habían publicado.
- `git diff main -- compose.yaml .env.example postgres mongodb` vacío; se contrastaron además hashes con la baseline de Fase 6. No se creó `postgresql/` ni se tocaron volúmenes, Tailscale o credenciales.
- Los resultados técnicos/archivos de fases 0–5 se preservaron: sus manifiestos verifican 396 entradas, con insumos locales completos. Un clon no contiene esos insumos privados y no se presenta como reproducción de datos completa.
- El diff de archivos nuevos se revisó como contenido completo, no solamente mediante `git diff`, que omite archivos no rastreados. El examen automático de secretos/tamaños incluyó también los reportes generados, no solo el subconjunto del validador original.

## 2. Archivos aprobados y exclusiones

La lista **exacta** de rutas propuestas para staging está en [approved_paths.txt](../../research/datasets/results/phase6_review/approved_paths.txt). No incluye archivos protegidos sin cambios. El [inventario de auditoría](../../research/datasets/results/phase6_review/review.json) registra conteos, tamaños, exclusiones, controles y resultados; el [inventario general](../../research/datasets/results/phase6/candidate_inventory.csv) añade SHA-256 de los inputs candidatos del validador.

| Grupo aprobado | Alcance |
|---|---|
| Documentación | README principal, índice `docs/README.md` y documentos de académico/datasets/arquitectura/equipo/decisiones, incluido este reporte |
| Exclusiones | `.gitignore` raíz y `research/datasets/.gitignore`; no añadir con `-f` archivos ignorados |
| Investigación previa necesaria | Entregables `00_*`–`05_*`, README histórico, matrices y diccionario CSV; conservados como snapshots |
| Reproducibilidad | Scripts Python/SQL/JS, requirements/lock y pruebas existentes; validador Fase 6 y tres regresiones nuevas |
| Evidencia acotada | JSON/CSV/JUnit, ejemplos mínimos del núcleo no personal y logs históricos explícitamente revisados; manifiestos y resultados nuevos de revisión |

Ningún candidato supera 1 MiB. No se encontraron credenciales reales, correos personales, IP privadas/Tailscale, filas individuales de solicitudes 311 o detalles personales de accidentes en los candidatos revisados. Los perfiles JSON de esas fuentes contienen estadísticas/esquemas; los ejemplos de lecturas publicados son mínimos del núcleo de Madrid, no personas ni usuarios. Los correos `example.invalid` son ilustrativos y no cuentas reales.

**Excluidos y conservados localmente:** `raw/`, `private_results/`, `.venv/`, caches de pytest/Python, SQLite/Parquet, dumps/backups/volúmenes, `.env*` salvo plantilla pública, claves y logs nuevos. También las transcripciones completas `results/phase3/academic_original.txt` y `results/phase4/{E,P,I}_original.txt`, por redistribución académica no confirmada. Las rutas ignoradas reales se registran en [excluded_paths.txt](../../research/datasets/results/phase6_review/excluded_paths.txt). No se eliminaron ni reubicaron artefactos.

Las excepciones `.gitignore` para logs son explícitas, no un permiso general para futuros logs. Los CSV de matrices/diccionario y scripts no quedan accidentalmente excluidos. La revisión estática no certifica ausencia absoluta de secretos ni permisos jurídicos; el historial local disponible tiene un único commit de infraestructura, también examinado. No se inspeccionaron archivos privados para copiar sus secretos ni se consultó historial remoto.

## 3. Revisión documental y académica

| Comprobación | Resultado |
|---|---|
| Estado de Madrid | Recomendación/selección condicionada, pendiente de equipo/docente; sin aprobación atribuida |
| Núcleo vigente | 91.959 aire + 66.005 meteo + 674.704 tráfico = **832.668** elegibles estructurales, enero de 2025 |
| Prueba previa | **993.374** hechos de Fase 3, aire/meteo enero+julio y tráfico enero; otro alcance/modelo, no suma adicional del núcleo |
| Puntuaciones | Madrid 63,665; Londres 49,345; NYC 46,345/100; matriz exacta y sumas contrastadas, no notas académicas |
| Modelos | Doce tablas/colecciones preliminares; prueba local no implementación definitiva; sensor, sitio y canal separados |
| Origen | Observado por medición, derivado por IDs/UTC/reglas; synthetic únicamente fixtures CRUD no métricos, no volumen |
| Límites | Metadatos físicos/administrativos, unidades/clocks/CRS, geografía, MG04/05/08 y KPIs faltantes permanecen abiertos |
| Períodos | Accidentes 2026 separados; energía mensual no horaria; no CO₂ o recorridos inventados |
| Tecnologías futuras | HDFS/Spark/dashboard no implementados; enero no acredita 1 millón Spark; muestras de 5.000 no cumplen mínimos finales |
| IA | Asistencia automatizada declarada; no análisis manual independiente ni firmas; registro consolidado Codex/modelos y norma institucional pendientes |
| Utilidad para Fernanda | Texto universitario con metodología, caracterización, calidad, límites, citas y referencias; requiere adaptación/formato y revisión humana, no reescribir logs |

Las referencias internas son accesibles en la selección publicable; los documentos históricos se identifican como snapshots. Las URLs oficiales se vinculan a manifiestos verificables, **sin volver a consultar disponibilidad o términos en vivo**. Las transcripciones académicas completas permanecen excluidas; Madrid CC BY 4.0 documentada no implica licencia universal del repositorio ni permiso para redistribuir LAQN/NYC/EPA sin revisar sus condiciones específicas.

## 4. Diagramas y pruebas

- **Cinco diagramas parseados y renderizados localmente** con Mermaid **11.12.1**, usando paquetes ya presentes, Webpack local y Chrome headless. No se instalaron paquetes ni se descargaron recursos. Los SVG resultantes quedaron en temporales, no se duplicaron como nuevos diagramas versionables.
- La primera prueba Node sin DOM no podía sanitizar flowcharts; fue un límite del entorno, no un error de sintaxis. El render en navegador resolvió esa limitación. Webpack del sistema se ejecutó con Node del sistema y una dependencia `uuid` ya instalada.
- Se contrastaron las doce entidades, **15 FK** y nulabilidad/cardinalidades contra `phase5_postgresql.sql`; coinciden. `users` sigue independiente, sin FK inventada ni enlace cruzado SQL–MongoDB.
- Render confirma sintaxis/generación de SVG, **no revisión perceptual humana de legibilidad ni equivalencia garantizada con cualquier versión de GitHub**.
- Suite inicial: **82/82 aprobadas**. Tras corregir el problema reproducido y añadir regresiones: **85/85**, cero fallos/errores/omisiones. Las tres nuevas prueban referencia local `main`, fallback a `origin/main` y rechazo si ambas faltan.
- Dry-run de preparación: seis hashes verificados, sin escritura ni motores.
- Enlaces relativos, existencia de scripts, conteos, puntajes, exclusiones, whitespace/conflictos y hashes verificados. Las cifras exactas finales de enlaces/candidatos están en [validation.json](../../research/datasets/results/phase6/validation.json) y [review.json](../../research/datasets/results/phase6_review/review.json).
- JUnit de revisión: [tests.xml](../../research/datasets/results/phase6_review/tests.xml). Evidencia de render: [mermaid_render.json](../../research/datasets/results/phase6_review/mermaid_render.json).

## 5. Problema concreto corregido

**Validador no portable en clon de la rama documental.** `phase6_validate_docs.py` consultaba directamente la rama local `main`; un clon que checkout `docs/dataset-research` normalmente solo tiene `origin/main`. Se reprodujo el fallo (`git rev-parse main`, exit 128) en una copia local aislada que contenía únicamente candidatos publicables, sin raw/derivados privados.

Corrección mínima: resolver primero `refs/heads/main` y, si falta, `refs/remotes/origin/main`; registrar la referencia utilizada y fallar claramente si ninguna existe. Se aplica también a la comparación de baseline. La misma copia pasó después sin descargar insumos y sin afirmar una reproducción de datos privados. No se modificaron contratos, datos o scripts de Fase 5. Los tres casos de regresión quedaron en `tests/test_phase6_docs.py`.

Los comandos de instalación/arranque/carga no se ejecutaron: son procedimientos posteriores con advertencias. Bash de copia de `.env` fue comprobado sintácticamente y en un directorio temporal con un `.env` existente; la protección evita sobrescritura. PowerShell fue revisado textualmente si su intérprete no está disponible, sin declararlo probado en ejecución.

## 6. Pendientes y riesgo Coolify

**NO VERIFICADO:** rama configurada en Coolify, autodeploy, integración GitHub/webhooks y despliegues preview de ramas/PR. La configuración disponible solo incluye `compose.yaml` y variables de plantilla; no contiene reglas suficientes para garantizar que publicar una rama distinta de `main` no active servicios.

Antes de autorizar push, José debe confirmar en el panel: repositorio/recurso afectado, rama monitorizada, autodeploy, alcance de webhooks, preview deployments y política de PR. No se inspeccionó el panel ni se invocó API/hook. Un diff de Compose vacío no garantiza ausencia de redeploy por un webhook.

Otros pendientes no bloquean compartir documentación honesta, pero sí impiden declarar el proyecto terminado: ratificación, respuestas docentes, unidades/clocks/CRS, mínimos/cargas definitivas, revisión humana individual, norma IA y permisos de redistribución adicionales. El dictamen es sobre los archivos auditados, no aprobación académica o garantía legal.

## 7. Comandos recomendados — solo después de autorización

Desde la raíz, validar **antes** de staging (el validador deliberadamente rechaza cambios staged):

```bash
git branch --show-current
git status --short
python3 research/datasets/scripts/phase6_validate_docs.py
git diff --check
git add --dry-run --pathspec-from-file=research/datasets/results/phase6_review/approved_paths.txt
```

Si las rutas/contenidos cambiaron desde el reporte, volver a auditar la lista; no añadir rutas ajenas ni ignoradas. Después de aprobación del usuario/equipo, seleccionar únicamente el allowlist:

```bash
git add --pathspec-from-file=research/datasets/results/phase6_review/approved_paths.txt
git diff --cached --name-status
git diff --cached --check
git diff --cached -- compose.yaml .env.example postgres mongodb
git diff --cached
```

La última comparación de infraestructura debe estar vacía. Si staging no corresponde a lo autorizado, detenerse; no ejecutar automáticamente reset/restore de trabajo ajeno. Solo tras revisar el staged diff y **confirmar Coolify/autorización**:

```bash
git commit -m "docs: document dataset research and review"
git push --set-upstream origin HEAD:refs/heads/docs/dataset-research
```

Estos últimos comandos **no se ejecutaron y no son inocuos frente a un Coolify no verificado**. El destino explícito evita publicar `main`, pero no neutraliza webhooks. No usar `--force`, hacer merge ni abrir PR automáticamente. Esperar autorización al finalizar esta revisión.
