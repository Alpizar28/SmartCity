# Demostración académica MongoDB

Este laboratorio utiliza una base standalone temporal y exclusiva. No carga,
actualiza ni atribuye a sensores las lecturas públicas Madrid v2. Su versión
documental es `smartcity-academic-v1`, independiente de `madrid-draft-v2`.

## Conjunto y procedencia

`fixtures.json` contiene dos tipos, cuatro sensores, nueve lecturas y tres textos
narrativos. Todos los documentos tienen origen `synthetic`. Las identidades y
nombres de los sensores son una proyección del paquete administrativo sintético;
sus tipos reproducen la regla `demo-type:` + categoría del modelo PostgreSQL,
sin acceder al motor ni modificarlo. Se comprueban los hashes del paquete y los
catálogos. No se copian asignaciones geográficas ni se identifican equipos físicos.

Las lecturas son valores de prueba, no copias ni ampliaciones de mediciones
municipales. Las fechas son simuladas y se almacenan como BSON Date. El mínimo
de 500.000 documentos se respalda exclusivamente con la evidencia pública previa.

## Consultas y resultados

- **MG01:** `lecturasPorSensor(base, sensorId)` exige un identificador explícito.
  El sensor A1 tiene dos lecturas, de valores 10 y 14. Un sensor inexistente
  devuelve cero; la ausencia del parámetro se rechaza.
- **MG07:** `promediosPorTipo(base)` relaciona lectura, sensor y tipo mediante
  dos `$lookup`. Agrupa por tipo de dispositivo, magnitud y unidad. Tipo A:
  temperatura, cuatro lecturas, promedio 17 °C. Tipo B: temperatura, tres lecturas,
  promedio 100/3 °C; humedad relativa, dos lecturas, promedio 50 %.
- **Información dinámica:** `informacionDinamica` recupera dos textos con
  «vibración», un documento con el atributo adicional de mantenimiento y dos
  revisiones del relato de A1. El cuerpo es texto libre; el sobre y los atributos
  constituyen información estructurada y semiestructurada. No se afirma que BSON
  por sí solo demuestre contenido no estructurado.

Las consultas públicas por canal y por magnitud permanecen intactas en
`sprint1/basico/consultas_mongodb_v2.js`, con su alcance y evidencia históricos.
La matriz de entrega identifica por separado las demostraciones por sensor y tipo.

## Reproducción

Se requieren Python 3.10+, el binario local `mongod` 7.0.16 y `mongosh`.
Desde la raíz del repositorio:

```bash
node --test tests/sprint1/test_mongodb.js
python3 scripts/validar_mongodb_academico.py
```

Los binarios deben estar disponibles en PATH; `--mongod` y `--mongosh` permiten
indicar sus rutas locales explícitas. El ejecutor necesita permiso para crear sockets locales. No acepta URI, host,
base existente ni directorio externo de datos. Crea un directorio exclusivo,
conecta por su socket Unix y verifica el PID del servidor. Solo enlaza TCP a
loopback, con puerto asignado temporalmente. No inicia replica set ni sharding.
No utiliza contenedores, volúmenes previos ni servidores compartidos.

Cada ejecución crea un directorio nuevo bajo `sprint1/mongodb/evidencias/academico/`
con salida nativa, comparación independiente, metadatos, resultados y SHA-256.
No sobrescribe intentos anteriores. La instancia se detiene y sus datos temporales
se eliminan al finalizar. Los binarios no forman parte de la entrega Git.

## Validación e integridad

El contraste Python verifica los 18 documentos completos, el filtro de identidad,
las sumas y cantidades por grupo y la selección narrativa. Los 13 controles
negativos comprueban referencias inexistentes, unidades incompatibles, conflicto
de replay, procedencia incorrecta, fecha no BSON, duplicados, parámetro ausente,
destinos oficiales y reutilización de la base. Las referencias y unidades se
verifican en la aplicación; no se presentan como FK MongoDB. Los rechazos nativos
por validación e índice conservan los códigos 121 y 11000.

La ejecución válida es
[`20261028T161057-eff98453`](../evidencias/academico/20261028T161057-eff98453/execution.json).
Los intentos anteriores registran fallos de permisos, comparación del PID,
serialización y manejo asíncrono. No acreditan resultados aprobados ni sustituyen
la ejecución válida; sus registros se conservan.

## Alcance pendiente

El almacenamiento distribuido aparece expresamente en la sección MongoDB del
enunciado y sigue **sin demostración**. Este laboratorio standalone resuelve
consultas y contenido, no distribución. La modalidad suficiente debe aclararse
con el docente antes de implementar replicación o particionamiento horizontal.
