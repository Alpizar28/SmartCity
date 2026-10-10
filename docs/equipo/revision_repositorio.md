# Revisión del repositorio y publicación segura — Fase 6

## Protección y alcance

Al iniciar: rama `main`, HEAD `6ad86ce` (`chore: bootstrap data infrastructure`), remoto configurado `https://github.com/Alpizar28/SmartCity`, único cambio visible `?? research/`. La rama solicitada no existía; se creó **`docs/dataset-research`** desde ese HEAD, sin commits. Los archivos de investigación no rastreados se trataron como trabajo existente y se conservaron.

Antes de editar se registraron hashes de archivos existentes y referencias Git en una baseline local externa, `/tmp/opencode/smartcity-phase6/baseline.json`. No se leyó ni modificó ningún archivo `.env` privado. La revisión final compara esa baseline, especialmente todo `research/datasets/`, Compose y configuración existente; solo README principal, `docs/README.md` y `.gitignore` tienen cambios previstos sobre archivos anteriores.

## Infraestructura vinculada al despliegue

[compose.yaml](../../compose.yaml) define los servicios, pins, puertos por variables, red y volúmenes `postgres_data`/`mongodb_data`; [.env.example](../../.env.example) es la plantilla pública. La configuración efectiva del panel Coolify, rama monitorizada, webhooks y Tailscale no está presente en el árbol versionado revisado ni fue consultada remotamente. La existencia del entorno compartido procede del usuario/P, no de una comprobación de conectividad en esta fase.

Se conservaron `postgres/`, `mongodb/`, `data/`, `docs/` y `research/datasets/`; no se creó `postgresql/`, no se añadieron inicializadores y no se tocaron credenciales/volúmenes. La mera edición local no publica cambios, pero **no se puede garantizar que un futuro push/merge no dispare redeploy** sin revisar el panel con José. No ejecutar Compose, Coolify ni comandos Tailscale para validar docs.

## Artefactos y duplicaciones encontrados

- `raw/` contiene descargas y miembros ZIP grandes; `private_results/` contiene Parquet/CSV, cache y ledgers SQLite de cardinalidad. Se mantienen locales, sin borrar ni reubicar.
- `.venv/`, `.pytest_cache/`, `__pycache__/` y temporales son regenerables y no versionables.
- `results/phase3/academic_original.txt` y `results/phase4/E_original.txt` son transcripciones idénticas del mismo PDF. Se preservan ambas localmente; no se redistribuyen sus textos completos hasta confirmar autorización. Igual política para P/I completos.
- `results/phase3/postgres_execution.json` coincide con una salida `smartcity-phase3-proof-0c7789d6bb.json`, y sus logs también coinciden. No se eliminan: las rutas son evidencia referenciada en manifiestos.
- Los resultados supersedidos de Fase 5 y los intentos fallidos de motores no son poblaciones adicionales ni basura borrable sin revisión.
- No se movieron datasets a `docs/`: se añadieron síntesis y enlaces para evitar duplicar datos y logs.

## Política de versionado y licencias

[.gitignore](../../.gitignore) conserva excepciones para `.env.example` y `data/.gitkeep`, excluye descargas, derivados grandes, dumps, caches, temporales, claves y nuevos logs, y permite **solo los logs históricos expresamente revisados**. Diccionarios y matrices `.csv`, scripts SQL/JS/Python, locks, resultados acotados JSON/JUnit y docs permanecen candidatos. No se aplica una exclusión indiscriminada de CSV/SQL/JSON.

No se añaden nuevos datasets, PDF completos o datos LAQN/311 individuales. Madrid tiene CC BY 4.0 documentada, con atribución y cambios; no permite omitir privacidad ni confundir licencia de datos con licencia del código. LAQN tiene restricciones y NYC/EPA condiciones específicas: sus tablas originales siguen privadas. No se impone una licencia de código/documentación en nombre de todos los autores. Referencias: [fuentes y permisos](../datasets/fuentes_y_procedencia.md).

Las transcripciones ignoradas siguen referenciadas en manifiestos históricos, por lo que un clon necesita insumos autorizados para verificación completa. La investigación se puede leer sin ellos; no se promete que todas las pruebas de datos funcionen en un clon vacío.

## Validación reproducible y límites del examen de secretos

[phase6_validate_docs.py](../../research/datasets/scripts/phase6_validate_docs.py) examina enlaces Markdown internos de archivos candidatos, referencias de scripts, conteos, matriz exacta, relaciones E-R, exclusiones, candidatos grandes y patrones de secretos. Genera resultados nuevos en `research/datasets/results/phase6/`, sin regenerar fases anteriores. La comparación de baseline de este entorno también está disponible como opción.

La revisión de secretos es **estática y acotada al árbol candidato**, no auditoría de seguridad ni certificado de ausencia absoluta. Detecta patrones de claves, tokens, PEM, URIs con credenciales y asignaciones sospechosas; valores de ejemplo/variables se revisan como falsos positivos. No inspecciona secretos privados para publicarlos ni verifica todo el historial remoto. No se requiere conectividad de red.

La suite heredada se ejecuta con un JUnit nuevo, sin iniciar motores; los resultados nativos de Fase 5 se verifican como evidencia guardada, no como una nueva corrida. El informe final y hashes quedan en [validation.json](../../research/datasets/results/phase6/validation.json) y [tests.xml](../../research/datasets/results/phase6/tests.xml). Validación Mermaid: parser local si está disponible; si solo se comprueba estructura/relaciones, no se declarará renderizado visual probado.

## Preparación de publicación — posterior y manual

1. Los cuatro revisan texto, diagramas, atribución de trabajo y [ADR](../decisiones/ADR-001-madrid.md); Fernanda confirma norma IA y permiso de extractos/citas.
2. José verifica rama monitorizada y política de redeploy con el administrador antes de cualquier push o merge. No asumir que una rama documental es excluida de los webhooks.
3. Revisar `git status --short`, `git diff --check`, diff de archivos rastreados y **cada candidato no rastreado**. Revisar [inventario candidato](../../research/datasets/results/phase6/candidate_inventory.csv) y reporte de secretos/tamaños; no usar `git add .` sin esa auditoría.
4. Asegurar que las reglas `.gitignore` de raíz y de investigación se publiquen junto con la investigación: la raíz proporciona exclusiones adicionales.
5. Solo después de autorización, seleccionar rutas explícitas para staging, revisar `git diff --cached` y preparar commit/PR. **No realizados en Fase 6.**

La documentación queda para revisión; no sustituye aceptación del dataset, revisión humana de integrantes ni autorización de cargas/despliegues.
