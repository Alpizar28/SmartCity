# Respaldo, restauración y concurrencia — pruebas acotadas

Estas pruebas pertenecen al harness `scripts/test_sprint1_engines.py`. No son un
procedimiento autorizado para producción ni una política de respaldo del equipo.
No usan bases compartidas ni secretos. Ambos motores se mantienen sin red y sin
puertos publicados. Los archivos de respaldo solo viven dentro del contenedor y
se eliminan con él; no se suben a Git ni se confunden con backups históricos.

## PostgreSQL

1. Crear un snapshot lógico ordenado del esquema `sprint1`: todas las tablas,
   cuarentena, secuencias, índices, vista, funciones y restricciones.
2. Ejecutar `pg_dump --format=custom` sobre `sprint1_test`.
3. Crear **otra base vacía**, `sprint1_restore`, dentro del contenedor desechable.
4. Restaurar con `pg_restore --exit-on-error`, sin borrar la base original.
5. Comparar los snapshots lógicos completos, excluyendo OIDs físicos, estadísticas
   y nombre de base, que no representan igualdad del contenido lógico.
6. Ejecutar la vista, función y replay en el destino. Probar la secuencia de
   cuarentena con una inserción explícitamente marcada como sondeo de restauración.
7. Confirmar que el snapshot de la base origen no cambió.

Después de comprobar la restauración, se reutiliza **solo el destino desechable**
para una carrera de ocho conexiones independientes a PostgreSQL: cuatro intentan
el ejemplo de aire y cuatro una mutación contradictoria de prueba, todos para la
misma clave original. Las lecturas/cuarentena del destino se truncan para este
sondeo; jamás las de origen.

Resultado comprobado en READ COMMITTED:

- 1 `accepted` y una sola lectura persistida.
- 3 `duplicate`, sin duplicar la lectura ganadora.
- 4 `quarantined`, todos con la huella del payload opuesto al ganador.
- La huella aceptada coincide con uno de los dos candidatos y nunca se sobrescribe.

Esto verifica la contención de **una clave y ocho conexiones**, no un benchmark,
estrés sostenido, todas las intercalaciones posibles ni otros aislamientos.
La prueba no exige un ganador concreto: el orden de llegada es concurrente.

## MongoDB

1. Ejecutar `mongodump --gzip --archive` para `sprint1_test`.
2. Restaurar hacia el namespace nuevo `sprint1_restore.*`, usando `--nsFrom`,
   `--nsTo`, `--nsInclude` y `--stopOnError`; sin `--drop`.
3. Comparar todas las colecciones: documentos y tipos BSON, índices y opciones
   (incluidos validadores). Se excluye namespace físico/UUID al cambiar de base.
4. Comprobar BSON Date, agregación, replay y rechazo de una identidad física
   inventada con el validador restaurado.
5. Confirmar que origen y destino conservan su contenido lógico tras las pruebas.

Se recuperan tres lecturas, una cuarentena y seis índices de lecturas, incluido
`_id`. La mutación rechazada no se conserva como dato real. No se ha demostrado
concurrencia MongoDB entre procesos ni operación durante caída del servidor.

## Evidencia y reproducción

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_sprint1_engines.py
```

El informe nuevo en `/tmp/opencode/smartcity-s1-integration-*.json` incluye:

- Versiones e IDs de imágenes, hashes de código y ejemplos históricos.
- Resultado de integración, respaldo/restauración y concurrencia PostgreSQL.
- SHA-256 de archivos de respaldo y fingerprint lógico cuando corresponde.
- Verificación de ejemplos históricos sin cambios y limpieza de contenedores.

El hash del archivo de respaldo puede cambiar entre ejecuciones por metadatos:
la prueba exige igualdad **lógica del contenido restaurado**, no identidad binaria
entre backups distintos. Eso no modifica el requisito de identidad binaria de
los SQLite históricos pendientes: son controles diferentes.

## Pendiente para un respaldo real

Volumen representativo, almacenamiento externo cifrado, accesos y retención,
respaldo de roles/configuración, procedimiento de recuperación independiente,
RPO/RTO acordados, monitoreo y recuperación ante corrupción o caída. Restaurar
dentro del mismo contenedor demuestra un round-trip lógico, no recuperación
ante pérdida total de la máquina ni durabilidad de tmpfs.
