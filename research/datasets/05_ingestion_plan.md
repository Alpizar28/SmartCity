# Fase 5 — Pipeline reproducible y limitado

## Arquitectura propuesta

Originales inmutables + manifiesto02/SHA → filtro de enero/estrato existente → validación de campos/QA → tiempo local explícito/UTC condicionado → IDs deterministas → catálogos compartidos + ledger de identidad → muestra/exportaciones → PostgreSQL estructurado y MongoDB documental locales → CSV/Parquet futuros para HDFS/Spark. Derivados/eventos/alertas son otra rama después de aprobar reglas. Sin flujo ni servidor definitivo.

## Comandos desde research/datasets

```bash
.venv/bin/python scripts/phase5_verify.py
.venv/bin/python scripts/phase5_prepare.py --dry-run
.venv/bin/python scripts/phase5_prepare.py --sample-size 5000
.venv/bin/python scripts/phase5_postgres_sample.py
.venv/bin/python scripts/phase5_native.py --engine mongodb
.venv/bin/python scripts/phase5_reports.py
.venv/bin/python -m pytest tests -q --basetemp=/tmp/opencode/smartcity-phase5-tests --junitxml=results/phase5/tests.xml
.venv/bin/python scripts/phase5_verify.py --final
```

Dry-run verifica seis hashes y muestra el plan, sin escribir, extraer ni conectar motores. Preparación no tiene DSN ni carga masiva: exporta1000..10000 documentos como máximo. Docker ejecuta sobre unix:///var/run/docker.sock explícito; --network none, sin puertos publicados ni credenciales remotas. Scripts nativos requieren imagen local (--pull=never), DB/nombre aleatorio y mount inputs readonly. Imágenes usadas: postgres16-alpine y mongo7.0; digest/versión registrados. Imágenes Docker descargadas en esta fase son infraestructura de prueba, no nuevos datasets ni presupuesto de adquisición02. Nunca usar Compose raíz, .env privado o URI compartida.

## Controles implementados

- Fuente/versión: hashing completo y localizadores de fila/columna/miembro. Cache de tráfico conserva nueve columnas; solo se reutiliza si fingerprint y hash coinciden. Escritura temporal + os.replace; originales nunca sobrescritos.
- Lotes: extracción CSV100k, commits ledger10k y Mongo insertMany500. Prueba SQL limitada5k. Preparación writer con flock; no procesos concurrentes sobre mismo directorio.
- Unicidad: ledger SQLite local en disco, PK determinista y payload_hash; conserva conflicto de misma clave hasta excluirla. No SQL/Mongo voluminosos. Ceros válidos, NULL≠0, flags sin convertir a estado, extremos sin borrado automático.
- Reanudación: cache publicado solo al completar CRC; archivo parcial no cuenta. Ledger incompleto se reconstruye determinísticamente desde inputs/cache, no salta filas sin verificar. Output de éxito se publica al terminar; sin preparation.json válido no se importa. Commit parcial se reevalúa, no se acepta como conjunto final. Coste: replay de la validación, no checkpoint por offset arbitrario.
- Idempotencia: run completo con mismos scripts/configuración/hashes se reutiliza y vuelve a verificar hashes de outputs. Configuración nueva o output alterado aborta: nueva versión/directorio y revisión explícita. En motores: IDs/UNIQUE + comparación de payload antes del upsert; replay igual no añade datos. No usar ON CONFLICT DO UPDATE para mediciones sin política de correcciones.
- Error: fallo de hash/clock/catálogo fatal; flags/campos inválidos contados y retenidos en original/ledger con valid=false; conflictos excluidos. Logs prepare.log, ledger y JSON de conteos. Excepciones nativas guardan salida/error y ejecutan finally de cleanup de recursos propios.
- Integridad: source/type/channel/station/zone con catálogo hash; trigger SQL y validator BSON complementan validación previa. PostgreSQL y MongoDB no comparten transacción: futuro outbox/manifest de lote con estados pending/SQL_committed/Mongo_committed/reconciled y replays idempotentes, **especificación, no implementado remoto**.

## Ingestión futura, después de revisión/autorización

José prepara exportación completa en ruta privada con misma regla; Daniel valida staging y carga por transacción (catálogos primero), Kembly valida BSON y upserts por lote; comparar IDs/payload/counts de cada lote y aprobar errores. Extensión necesaria: exportador completo actualmente limitado, ledger de lotes/errores durable por motor, reconciliación de escrituras parciales, backup/restore, recursos/benchmark e inventarios/relojes/unidades. No ejecutar esos pasos masivos aquí.

Exportaciones sample.csv/sample.parquet generadas con source_id/versión/IDs/UTC/tipo/unidad/origen; son solo5k. Partición futura source/year/month por calendario y manifest; HDFS -put/batch/Spark no ejecutados. schema_arrow/timestamp UTC explícito y diccionario NULL deben validarse al ampliar; no llamar procesamiento distribuido a Parquet local.
