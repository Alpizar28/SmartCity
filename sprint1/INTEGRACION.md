# Integración local nueva — alcance y evidencia

Esta guía corresponde al núcleo complementario `sprint1`. Su SQL está en
`sprint1/postgres/staging_queries.sql`. La ruta canónica `smartcity` y sus diez
consultas se prueban aparte mediante `scripts/test_sprint1_sql.py`.
Ambos pasos se ejecutan desde la raíz con `bash scripts/validate_sprint1.sh --engines`.

Se ejecutó `scripts/test_sprint1_engines.py` con Docker local, imágenes existentes
**PostgreSQL 16.6** y **MongoDB 7.0.16**. El resultado es independiente de Fase 5.
Cada motor recibe **tres lecturas**, una por fuente, desde copias explícitas de
los ejemplos publicados. No se verificaron originales privados ni se generó una
carga de volumen. La mutación contradictoria es solo un caso negativo de prueba.

## Qué se comprobó

| Motor | Comprobación |
|---|---|
| PostgreSQL | DDL, índices, FK compuestas, unicidad de claves originales |
| PostgreSQL | Rechazo de NULL/NaN, proyecciones contradictorias, sensor inventado y unidad meteo promovida |
| PostgreSQL | Consulta por tipo/sitio, ranking, ausencia de lecturas en staging, vista de calidad y función de aire |
| PostgreSQL | Rango semiabierto, exclusión de meteo de estadísticas de aire |
| Ambos | Primer insert aceptado, replay sin duplicar, conflicto en cuarentena sin sobrescritura |
| MongoDB | Validación BSON y fecha nativa, ObjectId interno e índices reales |
| MongoDB | Find/proyección/orden, agregación de aire y conteos por calidad |
| MongoDB | Rechazo de sensor inventado, fecha string, hash de fuente contradictorio, unidad meteo y versión histórica |
| MongoDB | insertOne/insertMany/find/findOne/updateOne/updateMany/deleteOne en colección de CRUD aislada |
| Ambos | Respaldo nativo, restauración a otra base y comparación lógica de datos/esquema |
| PostgreSQL | Carrera de ocho conexiones con dos payloads: 1 accepted, 3 duplicate y 4 quarantined |
| Ambos | Consultas básicas de `sprint1/basico/` ejecutadas en los motores |
| MongoDB | CRUD básico paso a paso con copias reales en una colección nueva separada |

Se captura `EXPLAIN (FORMAT JSON)` de PostgreSQL: con tres filas no demuestra
mejora de rendimiento, uso óptimo del índice ni resultados de un benchmark.
Se verificó backup/restore lógico y una carrera PostgreSQL acotada; no estrés
sostenido ni recuperación tras caída. Véase [respaldos](RESPALDOS.md) para el
alcance exacto y los límites.

## Reproducir

```bash
bash scripts/validate_sprint1.sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_sprint1_engines.py
```

No usa Compose compartido. El harness fija `/var/run/docker.sock`, bloquea pulls,
deshabilita la red de contenedores y no publica puertos. Datos de motores en tmpfs,
sin volúmenes persistentes ni montajes de datos del host. Cleanup solo de sus
contenedores aleatorios. No modifica resultados/manifiestos/scripts históricos.

Cada ejecución escribe un informe nuevo en
`/tmp/opencode/smartcity-s1-integration-*.json`: hashes del código y ejemplos,
versiones, salida de motores, backup/restore, concurrencia PostgreSQL, status y
cleanup. Un fallo no se presenta como
PASS. El harness ya detectó y corrigió una carrera de readiness de PostgreSQL y
el uso de await de nivel superior incompatible con este modo de mongosh; las
ejecuciones fallidas quedaron separadas de la ejecución exitosa.

## Lo que no cierra

100.000 filas PostgreSQL / 500.000 documentos MongoDB; entidades de sensores,
organismos y usuarios; todas las consultas académicas; reglas/alertas/incidentes;
geografía; 3FN definitiva; reproducción histórica; aprobación docente. Los
catálogos de los tests se derivan de ejemplos y no se autorizan para una carga
real. Los CLI nuevos en `basico/` tienen pruebas unitarias con clientes simulados,
pero falta probar sus conexiones psycopg/PyMongo de extremo a extremo con catálogos
independientes, permisos y datos autorizados; faltan reintentos y pruebas de volumen.
