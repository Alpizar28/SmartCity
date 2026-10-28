# Cierre técnico MongoDB — Sprint 1

## Observaciones públicas y ejecución v2

La ejecución nativa Madrid v2 `execution-20261028T055755-3fea400d` alcanzó PASS
con 748.889 lecturas, MG01–MG10, replay, siete operaciones CRUD y reconciliación.
El código de esa ejecución corresponde al commit
`804d6a551dc84e22d901b64554c30a712b951f77` de `main`; no identifica por sí solo
el estado posterior de toda la rama de entrega.

- Código público: `sprint1/basico/cargar_mongodb_v2.js`,
  `sprint1/basico/consultas_mongodb_v2.js` y `sprint1/basico/crud_mongodb.js`.
- [Evidencias selladas y verificación de hashes](evidencias/20261028T055755-3fea400d/README.md).
- [Comprobación de consultas, CRUD y reconciliación](evidencias/20261028T055755-3fea400d/comprobacion_cierre.json).
- [Inventario de código y versión de la ejecución](evidencias/20261028T055755-3fea400d/CODIGO_OFICIAL.json).

Las lecturas son observaciones reales de aire y tráfico de enero de 2025.
MG04/MG05 utilizan una regla demo y alertas de replay local, sin umbrales legales
ni avisos oficiales históricos. MG08 consulta incidentes anonimizados de 2026,
separados del período de las lecturas. MG01 por canal y MG07 por magnitud son
funcionalidades públicas que no identifican dispositivos físicos.

## Complemento académico del paquete A

El [laboratorio académico aislado](academico/README.md) demuestra MG01 por sensor
explícito, MG07 mediante lectura–sensor–tipo y recuperación de texto narrativo
con atributos heterogéneos y revisiones. Sus datos son enteramente sintéticos;
las nueve lecturas no se suman a las 748.889 observaciones públicas.

La ejecución [20261028T161057-eff98453](evidencias/academico/20261028T161057-eff98453/execution.json)
registró PASS en MongoDB 7.0.16 standalone. Python cotejó 18 documentos completos,
los resultados de las consultas, el replay y 13 rechazos. Las referencias y las
unidades se validan en aplicación; no son FK entre colecciones. Código:
`sprint1/mongodb/academico/modelo_demo.js`, `consultas_demo.js` y `ejecutar_demo.js`.
Los intentos fallidos anteriores conservan sus informes y no se contabilizan como
pruebas satisfactorias. El laboratorio no equivale a inventario municipal ni a
reportes ciudadanos reales.

## Alcance y limitaciones

El [alcance del avance](../../docs/equipo/ALCANCE_CONFIRMADO_SPRINT1.md) comprende
la sección Uso de MongoDB completa. El laboratorio aporta la demostración
narrativa y las consultas por sensor/tipo; el PASS público aislado no acredita
por sí solo esas demostraciones ni aceptación académica global.

El almacenamiento distribuido sigue sin demostración. Las pruebas locales no
certifican la base compartida, autenticación real, alta disponibilidad ni
restauración de producción. Capturar validadores no demuestra todos sus rechazos;
la ruta pública conserva tres colecciones administrativas sin validador. Los
13 rechazos del laboratorio tienen su propio alcance y no sustituyen pruebas
negativas de la ruta pública. Persisten los límites sobre sensores físicos,
CRS, vigencia geográfica, reglas demo y períodos distintos.

## Antecedentes conservados

El resumen dirigido a una integrante y los informes originales de la ejecución
pública son registros históricos sellados. Sus instrucciones de coordinación y
referencias a una sesión no constituyen especificaciones vigentes. Se conservan
íntegros para trazabilidad; este cierre y las evidencias identificadas arriba
constituyen la entrada técnica de la entrega actual.
