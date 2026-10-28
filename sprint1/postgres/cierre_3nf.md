# Cierre del modelo PostgreSQL normalizado — Sprint 1

## Dictamen

El modelo de entrega satisface 3FN respecto de las dependencias funcionales
documentadas y los dominios SQL tipados. Representa las cinco entidades mínimas
y los 17 atributos exigidos, mediante columnas directas o relaciones. Conserva
la identidad y el contenido de las 748.889 lecturas Madrid v2.

Las doce entidades del núcleo se mantienen y se añaden dos relaciones necesarias:
`sensor_types` y `channel_sensors`. El modelo definitivo tiene **catorce tablas**;
el [E-R completo](../../docs/arquitectura/diagrama_3nf.md) refleja esas tablas,
todos sus atributos y sus diecisiete FK. El esquema de práctica con `readings`
y `storage_id` no representa este modelo.

La prueba formal trata JSONB como un dominio SQL tipado, sin afirmar una
normalización escalar recursiva de sus propiedades. No se deducen DF a partir
de coincidencias del lote. Las claves opcionales con NULL no se consideran
claves candidatas. Los límites de acreditación de dispositivos físicos son
independientes de la normalización.

## Cambios y compatibilidad

- Fuente eliminada de `channels` y `observations`; se reconstruye mediante joins.
- Hora local, constantes de contrato, rol, calidad y duración por fuente se
  calculan en vistas, sin repetir dependencias no clave en los hechos.
- Referencia original reconstruida desde localizador y SHA de versión.
- Tipo de dispositivo y categoría separados; las magnitudes medidas no tienen
  FK a categorías de dispositivo. Tipos y categorías demo son sintéticos.
- Asignación sensor–canal separada y comprobada contra la estación, sin inventar
  asignaciones en el lote observado.
- Jerarquía ubicación → zona → distrito explícita; los 21 nombres de distrito
  publicados se documentan con su snapshot. Se conservan 55 vínculos ausentes,
  22 nombres de sitio ausentes y las limitaciones del CRS/vigencia.
- `observation_contract` conserva la interfaz `madrid-draft-v2`. No cambia MongoDB,
  sus índices, validadores, documentos o transformación.

La [auditoría de impacto y prueba formal](impacto_3nf.md) identifica cada DF y
las repercusiones en claves, índices, cargadores y consultas. La
[matriz académica](../../docs/avance_1/secciones/06-equivalencias.tex) detalla la
representación, nulabilidad y origen de cada atributo.

## Evidencia nueva de ejecución

| Prueba | Resultado | Evidencia |
|---|---|---|
| Muestra nativa histórica ampliada | PASS, 1.000 lecturas; versión anterior del validador | [20261028T071356-04a8cc67.json](evidencias/3nf/20261028T071356-04a8cc67.json) |
| Carga completa normalizada | PASS, 748.889 lecturas: 91.959 aire y 656.930 tráfico | [20261028T071812-55791345.json](evidencias/3nf/20261028T071812-55791345.json) |
| Reconstrucción contractual | Cero diferencias, todas las lecturas | Informe completo |
| Replay completo | PASS, mismo conteo | Informe completo |
| PG01–PG10 | PASS, comparación de todas las filas contra Python | Informe completo: `queries` |
| PG07 controlada | Tres sensores esperados, límites y varios canales; rollback | Informe completo: `pg07_controlled` y fixture `postgres_3nf.sql` |
| Relaciones y restricciones | Catálogo de 14 PK, 17 FK, 5 UNIQUE, 22 CHECK y 25 índices; ocho operaciones rechazadas, sin aislamiento individual de CHECK/FK | Informe completo: catálogo y pruebas negativas |
| Jerarquía territorial y asignación compatible | PASS con rollback | Informe completo: `positive_tests` |
| DF y claves candidatas | Cierres exhaustivos de determinantes; 14 relaciones en 3FN | Informe completo: `fd_check` y `dependencias_3nf.json` |
| SQL avanzado | PASS: 11 grupos de aire, cinco canales y DISTINCT, comparados con Python | [advanced-20261028T073507-abef9831.json](evidencias/3nf/advanced-20261028T073507-abef9831.json) |
| Compatibilidad MongoDB | Misma huella de identidad/payload que ambos informes nativos anteriores | Informe completo: `mongodb_v2_reconciliation` |
| Limpieza | PostgreSQL detenido y directorio de la instancia eliminado | Informe completo |
| Automatización offline | 65 pruebas Python y dos archivos Node aprobados | Suites `tests/sprint1/` |

Filas de PG01–PG10: **12, 5.133, 2, 1, 5.133, 5, 0, 21, 360 y 5.133**.
PG01 clasifica tipos administrativos explícitos; PG08 usa nombres de distrito.
Las demás consultas conservan los resultados anteriores. En PG08 se conservan
identidades, cantidades y ranking; no se presenta un cambio de etiqueta como
alteración de mediciones.

SHA-256 del informe masivo:
`111881d7b699a00ff0a890157e8e5cbadea8c1e715ac270c30b93f137994614a`.
Cada informe tiene además su archivo `.sha256`. Se conserva la tentativa inicial
FAIL por bloqueo del socket en el sandbox y las muestras previas; no sustituyen
la ejecución completa. Los reportes nuevos no sobrescriben pruebas anteriores.

Las ejecuciones `20261028T071042-3f9f038f`, `20261028T071112-8aeb341f` y
`20261028T071356-04a8cc67` registran hashes de versiones anteriores de
`validar_postgresql_3nf.py`. El informe completo `20261028T071812-55791345`
registra el hash del validador actual y de sus siete archivos asociados, incluida
la fixture SQL. Las muestras son antecedentes; no se las reetiqueta como pruebas
del script actual. Los manifiestos históricos conservan las huellas documentales
de su fecha, aunque posteriormente se hayan corregido esos documentos.

## Cobertura de operaciones negativas

El ejecutor captura cualquier excepción mediante `WHEN OTHERS` y solo registra
`rejected`, sin SQLSTATE ni nombre de restricción. `channel_source`,
`sensor_station` y `zone_parent` están dirigidas a triggers de integridad.
`parent_source_update` y `payload_conflict` están dirigidas a la inmutabilidad.
`raw_locator_sha` y `observation_version` también quedan bloqueadas por
inmutabilidad antes de alcanzar el CHECK del localizador o la FK de versión.
`duplicate_natural` está dirigida a la UNIQUE canal/UTC, pero tampoco identifica
el error capturado. **Ninguna de estas pruebas aísla específicamente un CHECK o
una FK.** El catálogo demuestra su definición; los ocho rechazos no equivalen a
ocho restricciones declarativas verificadas individualmente. La clasificación
y los límites se detallan en la [auditoría interna](https://github.com/Alpizar28/SmartCity/blob/9d84a34e529a72b316c540bff549080c906b0126/docs/equipo/AUDITORIA_DOCUMENTAL_SPRINT1.md).

Huella ordenada identidad/payload reconciliada:
`9e8a6b6b7e1aa527693aa9c71ca8dc44123e2d4602f8b94f2ba2afa4b54c69a0`.

## Alcance académico

La conformidad estructural y de normalización queda demostrada con el alcance
formal indicado. Los datos administrativos mantienen su identificación sintética:
5.133 sensores, 5.133 usuarios y un organismo. Los tipos ficticios no acreditan
aparatos instalados. PG07 se ejecuta y su lógica se prueba, pero la actividad
física del lote público no es evaluable sin asignaciones acreditadas.

MongoDB mantiene las limitaciones documentadas de consultas por canal/variable,
eventos por regla demo, alertas de replay e incidentes de 2026. Esta corrección
no constituye aprobación docente de esas adaptaciones ni comprobación del
servidor compartido. No se implementan componentes de noviembre.

## Archivos de entrega

- `schema_v2_3nf.sql`, `queries_v2_3nf.sql`, `dependencias_3nf.json` y
  `distritos_madrid.json`.
- `scripts/validar_postgresql_3nf.py` y el [capturador histórico de SQL avanzado](https://github.com/Alpizar28/SmartCity/blob/9d84a34e529a72b316c540bff549080c906b0126/scripts/capturar_sql_avanzado_3nf.py).
- `tests/integration/postgres_3nf.sql` y `tests/sprint1/test_modelo_3nf.py`.
- E-R completo, informe LaTeX con equivalencias y evidencias nuevas con SHA-256.
- Código e informes anteriores conservados para reproducir su contexto histórico.

La validación utiliza PostgreSQL 16.15 nativo, una instancia propia con socket
Unix privado y TCP deshabilitado. No modifica configuración del sistema,
permisos Docker, datos privados originales ni bases compartidas.
