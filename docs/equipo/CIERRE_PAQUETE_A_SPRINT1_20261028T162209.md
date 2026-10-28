# Cierre del paquete A — Sprint 1

La ejecución corresponde exclusivamente a las correcciones académicas autorizadas de MongoDB. No constituye aprobación integral del Sprint 1: el almacenamiento distribuido continúa sin demostración.

## Resultados

- MG01: dos lecturas sintéticas del sensor explícito A1, valores 10 y 14; sensor inexistente: cero.
- MG07: tipo A/temperatura, cuatro lecturas y promedio 17; tipo B/temperatura, tres y 100/3; tipo B/humedad, dos y 50. Las unidades no se mezclan.
- Tres textos narrativos con atributos heterogéneos y revisiones. Selección textual: dos; atributo de mantenimiento: uno; revisiones de A1: dos.
- Python cotejó 18 documentos completos y resultados. Replay sin cambios y 13 rechazos comprobados; referencias y unidades se validan en aplicación, no mediante FK.

## Ejecución y pruebas

La evidencia nativa válida es `sprint1/mongodb/evidencias/academico/20261028T161057-eff98453/execution.json`. MongoDB 7.0.16 standalone se inició en un directorio exclusivo, verificó su PID, se detuvo y sus datos temporales se eliminaron. No se reutilizaron instancias ni se accedió a servidores compartidos. Cuatro intentos anteriores conservan su estado FAIL; el primero no pudo crear un socket y los siguientes fallaron antes de completar las consultas. No certifican el código actual.

Aprobaron 65 pruebas Python, los dos archivos Node históricos, el archivo Node académico y seis pruebas documentales. Los logs se conservan junto al manifiesto del cierre.

## Integridad y documento

Se preservaron 427 archivos públicos del estado inicial y seis archivos privados de la generación v2. Los 29 archivos sellados MongoDB, 19 archivos oficiales y ocho sidecars PostgreSQL verificaron sus hashes. Los códigos SQL, contrato, cargadores y consultas públicas permanecen intactos. La conservación de datos públicos se demuestra por hashes y referencias a las ejecuciones previas; no se repitió su carga.

El informe nuevo es `docs/avance_1/SmartCity_Sprint1_PaqueteA_20261028T162209.pdf` (18 páginas revisadas visualmente), SHA-256 `13ab3d1ec859e3ab44762d76a484a22adf90ae596e9b9d2e0c2a485aa3b5c332`. Incluye un diagrama de las siete colecciones oficiales y otro separado para el laboratorio. No tiene comandos LaTeX sin procesar, referencias indefinidas ni cajas desbordadas. La precisión sobre 22 nombres vacíos se corrigió solo en el análisis de impacto.

Manifiesto: `sprint1/mongodb/evidencias/academico/cierre-20261028T162209/MANIFIESTO_PAQUETE_A.json`. Los PDF y manifiestos previos conservan sus bytes. Sus snapshots de documentos describen versiones históricas y no se reescriben para coincidir con las fuentes nuevas.

## Requisitos abiertos

- Demostración de almacenamiento distribuido MongoDB y aclaración de modalidad suficiente. No se ejecutaron replica set ni sharding.
- Alcance de materializadas, particionamiento y optimización general PostgreSQL, pendiente de aclaración docente.
- Persisten límites de sensores físicos, CRS, vigencia territorial, períodos y reglas demo. El laboratorio no los convierte en evidencia municipal.
- Negativos individuales CHECK/FK, unificación de la ruta antigua y optimización MG10 son mejoras separadas.

## Archivos modificados por este paquete

- `ENTREGA_SPRINT1.md`.
- `README.md`.
- `docs/README.md`.
- `docs/avance_1/main.tex`.
- `docs/avance_1/secciones/01-alcance-datos.tex`.
- `docs/avance_1/secciones/02-modelos.tex`.
- `docs/avance_1/secciones/03-consultas.tex`.
- `docs/avance_1/secciones/04-validacion.tex`.
- `docs/avance_1/secciones/05-cierre.tex`.
- `docs/equipo/ALCANCE_CONFIRMADO_SPRINT1.md`.
- `docs/equipo/CHECKLIST_CIERRE_SPRINT1.md`.
- `docs/equipo/ESTADO_SPRINT1.md`.
- `docs/equipo/MATRIZ_CONSULTAS_SPRINT1.md`.
- `sprint1/basico/README.md`.
- `sprint1/mongodb/README.md`.
- `sprint1/postgres/impacto_3nf.md`.

Los archivos nuevos y sus hashes se enumeran individualmente en el manifiesto, incluidas las evidencias nativas válidas y fallidas. No se realizaron commit, push, merge ni cambios en main.
