# Inicio local del Sprint 1

**Actualización:** el usuario autoriza integrar/publicar la consolidación documental en `main`, conservando explícitamente sus bloqueos históricos. Se mantiene `feat/sprint1-local-core` como rama activa; las menciones a no fusionar/publicar más abajo registran la preparación inicial. No se autorizan cargas ni cambios de infraestructura.

## Base y separación de evidencia

Referencia: [`madrid-draft-v1-frozen`](../../CONTRATO_PROVISIONAL_DATASET.md) y [estado del Sprint 1](ESTADO_SPRINT1.md). La interfaz provisional permite desarrollo; no autoriza DDL definitivo, carga ni despliegue. Los campos abiertos no se convierten en requisitos obligatorios del núcleo.

La recuperación histórica queda en `fix/repo-consolidation`: **83 PASS / 2 FAIL**, dos SQLite sin identidad binaria histórica acreditada y 13 respuestas históricas pendientes. No se modifican pruebas, manifiestos, hashes, resultados ni scripts de Fase 5. Ese bloqueo impide cerrar la reproducción histórica, pero no invalida el contrato provisional ni bloquea implementar código nuevo independiente. Ningún PASS nuevo significa que la suite histórica pasó.

Rama de continuación: **`feat/sprint1-local-core`**, creada desde `main` local, sin fetch, push ni merge. Directorio independiente: `../SmartCity-sprint1`. Solo se trasladan documentos de referencia, incluida la recuperación y auditoría para conservar los enlaces; no se arrastran commits de consolidación, entornos ni datos privados. Los documentos trasladados quedan como cambios locales revisables, no como un merge ni un nuevo resultado histórico.

## PostgreSQL — Daniel

1. Crear propuesta revisable del núcleo: fuentes, versiones de snapshot, estaciones, canales y lecturas de trabajo con procedencia, calidad y nulabilidad. Separar identidad de registro local de `measurement_id`: meteo/tráfico no tendrán PK definitiva dependiente del UTC hipotético. Conservar `source_key` y reloj original; no diseñar una identidad científica nueva ni usar fila/valor como ID.
2. Implementar validadores y adaptación al contrato, integridad de referencias, rechazo/cuarentena de payload contradictorio y distinción NULL/cero. Sin FK obligatoria hacia sensores, organismos o usuarios. No poblar esos dominios.
3. Preparar consultas por fuente/canal/tipo, conteos de calidad y trazabilidad, ranking acotado por canal, una vista y una función de consulta. PG01/02/05/07 solo como alternativas parciales; PG09/10 pueden implementarse de nuevo dentro de ese alcance. No declarar PG03/04/06 ni PG08 geográfico resueltos.
4. Pruebas nuevas de contrato y SQL, independientes de SQLite históricos. Una ejecución futura en PostgreSQL desechable requiere acordar el entorno local y autorizar una muestra acotada de originales verificados. No se ejecuta ahora.

Primeros archivos **propuestos, aún no creados**:

- `sprint1/postgres/README.md`: alcance y matriz de consultas.
- `sprint1/postgres/schema_proposal.sql`: DDL local revisable, no migración definitiva.
- `sprint1/postgres/queries.sql`: consultas, vista y función del núcleo.
- `sprint1/core/contract.py` y `sprint1/core/validation.py`: interfaz congelada y estados de evidencia, sin reutilizar el ledger histórico como dependencia.
- `tests/sprint1/test_contract.py`, `tests/sprint1/test_postgres.py`: validación nueva claramente identificada.

## MongoDB — Kembly

1. Proponer colección de lecturas de trabajo y catálogos con `schema_version='madrid-draft-v1-frozen'`, trazabilidad y payload multivariable de tráfico. No reetiquetar documentos históricos automáticamente ni exigir `_id` científico definitivo para meteo/tráfico. Un identificador interno de staging no representa identidad final y deberá tener correspondencia explícita futura.
2. Definir `$jsonSchema`, tratamiento explícito de campos opcionales/NULL y comprobación de referencias en aplicación. Índices candidatos sobre fuente/versión, canal, tipo y calidad; tiempo UTC solo para el subconjunto acreditado. No crear 2dsphere ni imponer unicidad basada en UTC hipotético.
3. Implementar find y agregaciones por fuente/canal/tipo/calidad y filtros combinados. MG01/07 parciales, MG09/10 dentro del núcleo; MG02 y extremos MG03 únicamente para aire con reloj/unidad acreditados. No agregación científica de meteo, joins de simultaneidad ni conclusiones espaciales. MG06 no se cierra con distritos publicados.
4. Pruebas nuevas de forma, BSON, nulabilidad y consultas. Prueba de motor desechable y muestra real quedan para una autorización local posterior; no depender de `phase5_prepare.py` ni de sus SQLite.

Primeros archivos **propuestos, aún no creados**:

- `sprint1/mongodb/README.md`: alcance y matriz.
- `sprint1/mongodb/validator.js`, `sprint1/mongodb/indexes.js`, `sprint1/mongodb/queries.js`: propuestas locales.
- `tests/sprint1/test_mongodb.py`: pruebas nuevas, sin conexión compartida.
- `scripts/validate_sprint1.sh`: futuro comando independiente; no sustituirá ni relajará `validate_repo.sh` ni la suite histórica.

## Bloqueos separados

**Profesor:** aceptar canal/sitio en lugar de sensor físico; tratamiento de instalación/estado ausentes; evidencia administrativa y usuarios consentidos; reglas de eventos/alertas y replay. Enviar la lista canónica [PREGUNTAS_PROFESOR.md](../../PREGUNTAS_PROFESOR.md). PG03/04/06 y MG04/05 no se presentan como cumplidas; las alternativas parciales siguen esperando aceptación académica.

**Publicador/evidencia técnica — José:** unidades meteorológicas, clocks meteo/tráfico, CRS y vigencia, inventario físico y relación administrativa. Una respuesta docente no certifica esas propiedades. Hasta resolverlas, unidades desconocidas y metadatos físicos quedan NULL; no GeoJSON, transformaciones, proximidad ni IDs temporales definitivos. MG08 exige además alcance y prueba separados de accidentes, fuera del núcleo enero 2025.

**Recuperación:** obtener las 15 copias exactas y repetir validaciones históricas; no es prerrequisito para redactar e implementar los módulos nuevos. Ninguna prueba histórica se omite para declarar reproducción completa.

## Primer checkpoint del equipo

Daniel y Kembly pueden comenzar propuestas y validadores sin esperar backups ni respuestas docentes. Fernanda mantiene separados aceptación académica, evidencia técnica y pruebas nuevas. Antes de ejecutar motores o cargar datos, acordar un entorno exclusivamente local desechable y autorizar explícitamente una muestra real acotada y verificada. No hacen falta sensores inventados, cuentas ficticias ni datos sintéticos.

Mantener `postgres/init/` y `mongodb/init/` con solo `.gitkeep`. No tocar Coolify, Tailscale, producción ni bases compartidas. No hay cargas, conexiones remotas, push ni merge en esta preparación.
