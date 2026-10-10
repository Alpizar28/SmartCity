# Auditoría lógica de los SQLite regenerados

**Integración documental autorizada:** este informe y los pendientes se incorporan a `main` por decisión explícita del usuario. El estado de validación descrito abajo sigue siendo FAIL; integrar documentación no acredita equivalencia con las bases históricas ni reproducción completa.

## Qué falla exactamente

1. `research/datasets/tests/test_phase3.py::test_prior_inputs_unchanged_after_phase3` compara **tamaño y SHA-256 binario** de todos los archivos de `results/phase3/inputs_manifest.csv`. Se detiene actualmente en `private_results/lcl_keys.sqlite`. No es una prueba exclusiva de SQLite: todavía faltan 13 respuestas históricas de catálogo/metadatos, enumeradas en [recuperación de insumos](RECUPERACION_INSUMOS_HISTORICOS.md).
2. `research/datasets/tests/test_phase5.py::test_dry_run_no_mutation_and_complete_run_idempotent` verifica que dry-run no conecte motores, que la preparación reutilice la ejecución completada y que la muestra conserve su hash. El rechazo del ledger **no está en el test**: ocurre en `phase5_prepare.py`, líneas 198–204, al comprobar todos los hashes binarios de `preparation.json.private_output_hashes`.

Además, `phase6_validate_docs.verify_private_evidence` verifica SHA binarios de los manifiestos y bloquea `validate_repo.sh` antes de pytest por el SQLite de LCL. Cambiar exclusivamente un assert de pytest no resolvería esos otros controles ni los 13 archivos faltantes.

## Evidencia disponible y su límite

Se dispone de fuentes originales recuperadas con SHA histórico exacto, scripts generadores cuyo SHA coincide con la evidencia histórica, esquema declarado por esos scripts, conteos históricos y muestra de Fase 5 con hash exacto.

**No se dispone de los SQLite históricos, dumps completos de sus tablas ni hashes lógicos calculados sobre ellos.** Un SHA binario no permite deducir el contenido ni el hash lógico de una tabla. La comparación fila a fila contra los originales recuperados permite acreditar la reconstrucción, pero no es una comparación directa entre el SQLite histórico y el regenerado. No se debe presentar el hash lógico actual como si se hubiese registrado en la ejecución histórica.

## Esquema e índices observados

Ambas bases se abrieron en modo solo lectura y pasan `PRAGMA integrity_check`.

| Base / tabla | Columnas | Claves e índices |
|---|---|---|
| LCL / `audit_lcl_keys` | `household TEXT`, `timestamp TEXT` | PK compuesta `(household,timestamp)`, colación BINARY, `WITHOUT ROWID`; sin tablas ni índices adicionales |
| Fase 5 / `identities` | `id TEXT`, `source TEXT`, `signature TEXT`, `valid INT`, `conflict INT DEFAULT 0` | PK sobre `id`, autoíndice único BINARY; tabla con rowid, sin tablas ni índices adicionales |

Estos esquemas corresponden al DDL de los scripts históricos verificados. Se inspeccionaron `sqlite_schema`, `table_info`, `index_list`, `index_xinfo` y los tipos almacenados por columna. No hay un dump histórico independiente que permita confirmar el catálogo efectivo de las bases antiguas.

## Hashes lógicos actuales

Algoritmo explícito para estas tablas (solo TEXT e INTEGER): SHA-256 de JSON UTF-8 compacto con `ensure_ascii=False` y `allow_nan=False`; primero una línea con nombres de columnas en orden del esquema, luego una línea por fila completa ordenada por todas las columnas. Cada línea termina en LF. No incluye páginas, rowids ocultos, freelist ni cabeceras SQLite. El esquema e índices se revisan por separado; estos hashes no sustituyen esa revisión.

| Tabla | Filas | SHA-256 lógico actual |
|---|---:|---|
| `audit_lcl_keys` | 3.997.252 | `76b0da5ea4a90df8448adbb6ea7d694b60cbf4b515e11ffc9967880c9dc352c6` |
| `identities` | 840.852 | `2ce58492d65526c5dde5051abb7e63daea369df716a451e3985152f18268ca27` |

Los hashes binarios históricos y regenerados continúan documentados en [recuperación](RECUPERACION_INSUMOS_HISTORICOS.md); no se alteraron ni se eliminaron requisitos de PASS.

## Comparación completa contra fuentes verificadas

**LCL:** se releen los cuatro CSV originales con SHA exacto y las mismas reglas de claves de `audit.py`, también con SHA histórico exacto. Una referencia temporal aislada deduplica los 4.000.000 registros. Se comparan todas las claves mediante `EXCEPT` en ambas direcciones: **0 faltantes y 0 extras**, 3.997.252 claves únicas. El hash lógico de esa referencia coincide con el de `audit_lcl_keys`. La referencia temporal se eliminó al terminar; no es una nueva fixture ni insumo de pytest.

**Ledger Fase 5:** se verifican los seis snapshots, el caché y los hashes de `phase5_prepare.py` y `phase5_contract.py` contra la configuración histórica. Se recorren los generadores de enero sin exportar ni cargar datos. Para cada ID se consulta el ledger en solo lectura y se compara la tupla `(source, signature, valid, conflict)` con el documento generado y su firma canónica: **840.852 filas comparadas, 0 discrepancias**, y el ledger contiene exactamente 840.852 filas. Los conteos seleccionados/válidos coinciden con la evidencia: aire 93.720/91.959, meteo 69.408/66.005, tráfico 677.724/674.704; conflictos cero.

Los informes completos de esta auditoría se conservan fuera de Git en `research/datasets/private_results/sqlite_logical_audit.json`, `lcl_row_comparison.json` y `phase5_row_comparison.json`. Son evidencia nueva de reconstrucción, no resultados históricos reescritos.

## Por qué el hash binario no demuestra una diferencia semántica

En general, el orden de inserción, asignación de páginas, freelist, reutilización tras DELETE, VACUUM y versión SQLite pueden producir archivos binarios distintos con las mismas filas. Por eso una validación lógica de esquema y contenido puede ser preferible para equivalencia. **Esto no identifica la causa concreta de las diferencias observadas aquí ni demuestra por sí solo que las bases históricas tenían idénticas filas.**

Para acreditar una sustitución de control histórico por equivalencia lógica haría falta una copia histórica cuyo SHA binario coincida, un dump histórico completo verificable o una decisión explícita que adopte una reconstrucción desde fuentes verificadas como nueva referencia. No se adopta esa decisión implícitamente ni se omiten los otros insumos ausentes.

## Decisión y validaciones

- **Tests modificados: ninguno.** Tampoco se modifican los controles binarios de los scripts: no está acreditada la condición de equivalencia con el contenido efectivo de las bases históricas.
- No se detectó diferencia semántica respecto de las fuentes verificadas y los generadores históricos. Respecto de los SQLite históricos efectivos, el resultado es **no determinable con la evidencia disponible**, no «diferencia exclusivamente binaria».
- `python -m pytest research/datasets/tests -q`: **FAIL — 83 PASS, 2 FAIL**, en las dos pruebas identificadas arriba.
- `./scripts/validate_repo.sh`: **FAIL**, por el hash histórico distinto de LCL en la etapa documental.
- **Listo para PR: NO.** Se requiere acreditar el contenido histórico o autorizar una nueva referencia reconstruida explícita; en cualquier caso, siguen pendientes las 13 respuestas históricas y no se altera su validación.
