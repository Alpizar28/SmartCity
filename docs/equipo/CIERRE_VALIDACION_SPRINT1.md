# Cierre de validación local — contrato `madrid-draft-v1`

Fecha de ejecución: 15/10/2026. Rama `feat/unified-data-contract`. **Resultados locales verificados; contrato pendiente de aprobación del equipo.** No hubo reinicio de las cargas activas, push, merge ni cambios remotos.

## 1. Resultado completo, no muestra

| Control | PostgreSQL 16.15 | MongoDB 7.0.16 |
|---|---:|---:|
| Observaciones/documentos cargados | **1.076.813** | **1.076.813** |
| Registros con valores y metadatos comparados | 1.076.813 | 1.076.813 |
| Segunda importación del lote completo | Sin aumento | Sin aumento |
| Conflictos de payload | Rechazados por inmutabilidad | Rechazados y registrados |
| Unicidad ID y clave lógica | Comprobada | Comprobada |
| Referencias de catálogo | FK y comparación del DTO | Validación previa y comparación completa |
| Fecha | `timestamptz` y UTC validado | BSON Date, rechazo de fecha string |
| Mediciones sintéticas | 0 | 0 |
| Contenedor y volúmenes propios eliminados | Sí | Sí |

La prueba completa usa **todos** los aceptados anuales, no solo las primeras 5.000 lecturas. Los datos cargados corresponden a una única fuente de mediciones, `MAD-AIR`, año 2025. Los contenedores eran desechables y ya no están activos; los archivos reproducibles y la evidencia permanecen. No son bases de desarrollo persistentes del equipo ni una carga compartida.

Verificación final ejecutada:

```bash
.venv/bin/python research/datasets/scripts/unified_full_verify.py
```

Salida conservada: `research/datasets/results/expanded-2025/verification.json`, `verified=true`. Exige misma generación, hashes del código ejecutado, lote completo, metadatos, replay, conflictos, limpieza y cero mediciones sintéticas. Los IDs/payloads también se contrastaron contra el ledger del ETL, no solo entre motores.

Huella SHA-256 común de las líneas ordenadas `[measurement_id,payload_hash]`:

```text
7ee034a1f3be3f4ef533d43c571047f6860fbf62e925759c6387e600eb11f398
```

SHA-256 del JSONL aceptado:

```text
1fba6d1e8e65f31a92a88d0e837da0d5fcf375d686eb85dcb179410ac40f36b8
```

## 2. Tiempos y recursos medidos

| Operación | PostgreSQL | MongoDB |
|---|---:|---:|
| Copia SQL a staging | 15,01 s | No aplica |
| Importación inicial | 458,09 s | 70,47 s |
| Reimportación completa | 575,56 s | 299,94 s |
| Comparación completa de metadatos | 33,14 s | 237,84 s |
| Validación total, con otros controles y limpieza | **1.105,65 s** | **644,91 s** |
| Pico de memoria del cgroup | 2.147.483.648 bytes, **2 GiB** | 1.719.492.608 bytes, **1,60 GiB** |
| Límite por contenedor | 2 GiB / 2 CPU | 2 GiB / 2 CPU |

PostgreSQL alcanzó el límite de memoria del contenedor, pero completó sin error ni reinicio. No se infiere de ello holgura de memoria. La base local ocupó 4.195.351.575 bytes, **incluido staging**; `observations` con sus índices ocupó 2.416.459.776 bytes. MongoDB registró `totalSize=525.905.920` bytes, suma de almacenamiento e índices comprimidos; no es comparable directamente con tamaño lógico JSON o tamaño PostgreSQL. Los archivos nativos conservan detalle y `EXPLAIN`/`executionStats`.

Son mediciones de esta máquina, imágenes locales y configuración acotada; **no** benchmark del servidor, promesa de rendimiento de producción ni prueba de mejora de un índice. Se mantuvo el harness tal como se ejecutó para conservar hashes reproducibles; no se cambió el código durante las cargas.

## 3. Dataset y calidad

- Aire: 1.103.232 slots seleccionados; **1.076.813 aceptados**; 26.419 en cuarentena.
- Rechazos de aire: 26.167 por flag, 126 por hora local inexistente y 126 por hora ambigua sin fold acreditado.
- Duplicados y conflictos del lote original: **0 y 0**. Los conflictos inyectados de prueba fueron rechazados y no incrementan el dataset.
- Meteo enero: 69.408 en cuarentena; tráfico enero: 677.724 en cuarentena. No se cargaron como aceptados.
- Cuarentena combinada sin repetir enero de aire: **773.551**.
- Enero mantiene exactamente sus 91.959 IDs y payloads; ampliación adicional: 984.854, no una copia de enero.
- Mediciones sintéticas: **0**. La carga completa incluye **1 organización, 5.133 usuarios y 5.133 sensores administrativos sintéticos** con `data_origin=synthetic`, semilla/versionado y procedencia; sus correos usan `example.invalid`. No se enlazan a canales ni observaciones reales, que conservan `sensor_id=NULL`, y no acreditan inventario físico.
- No se descargaron nuevas mediciones: el CSV oficial ya contenía todo 2025. Se adquirieron siete recursos documentales oficiales, 2.606.497 bytes, con hashes y procedencia.
- JSONL aceptado: **1.567,85 MB / 1,568 GB**; derivados anuales, incluido ledger y muestra: **2,175 GB**. No sumar archivos derivados como registros adicionales.

## 4. Cumplimiento verificable

| Objetivo global | Estado | Evidencia y límite |
|---|---|---|
| PostgreSQL ≥100.000 registros | **Cumplido en validación local** | Carga/replay de 1.076.813 y comparación completa; no servidor compartido |
| MongoDB ≥500.000 documentos | **Cumplido en validación local** | Carga/replay de 1.076.813, BSON Date, unicidad y comparación completa |
| Spark ≥1.000.000 procesados | **Pendiente** | Hay input suficiente, pero Spark/Hadoop no se ejecutaron ni implementaron |
| Integración de ≥2 fuentes de mediciones | **Parcial / pendiente** | Solo aire aceptado; inventarios auxiliares no se presentan como segunda fuente de lecturas |
| PG01–PG10 funcionales sobre sensores físicos | **Parcial** | Ejecución SQL sin error no acredita inventario físico; sigue vacío |
| Contrato aprobado por todo el equipo | **Pendiente** | Esta rama y la propuesta v2 requieren revisión |

No se rellenan mínimos con cuarentena, duplicados, entidades administrativas o mediciones ficticias. El volumen ya no bloquea las pruebas de bases; la segunda fuente y los requisitos físicos/funcionales sí requieren decisiones.

## 5. Pruebas y errores

- **134 pruebas Python aprobadas**, cero fallos/errores/omisiones en la ejecución registrada en `tests.xml`.
- Validación del repositorio aprobada: enlaces, modelo, escaneo estático acotado de secretos, hashes históricos del código desde Git y diff sin errores.
- PostgreSQL: FK, ID duplicado, clave lógica duplicada y payload modificado rechazados; PG01–PG10 ejecutadas, sin convertir resultados vacíos en cumplimiento.
- MongoDB: fecha string, identidad inconsistente, hash de fuente inválido, valor no finito, fuente desconocida y duplicados rechazados. Payload alterado conservando hash antiguo fue rechazado y registrado.
- Los fallos esperados de integridad pertenecen a pruebas negativas; **no son errores del lote real**.
- Las incidencias de certificados, bibliotecas de `pdftotext`, alcance de enero, conteo provisional y validación histórica se describen en [el informe anual](AMPLIACION_REAL_SPRINT1.md). No se alteraron originales para resolverlas.

## 6. Equipo, revisión y Git

Instrucciones completas: [ENTREGA_TECNICA_SPRINT1.md](ENTREGA_TECNICA_SPRINT1.md).

- **Daniel:** adaptar sus consultas y pruebas al DDL `smartcity`, `measurement_id`, relación de ubicaciones y vistas/funciones documentadas. Puede medir consultas sobre más de un millón de lecturas reales; no se modificaron arbitrariamente sus archivos.
- **Kembly:** usar catálogos y JSONL EJSON del mismo lote, conservar IDs y BSON Date, aplicar política idempotente y conflictos en su implementación. El harness no sustituye su trabajo.
- **Fernanda:** actualizar diccionario, diagramas, versión vigente, conteos y límites de evidencia. No presentar muestras ni prototipos como cargas completas ni datos simulados como observaciones.

Cambios agrupados: contrato/DDL/ETL, compatibilidad de evidencia histórica, exportador multi-mes y validación completa local, pruebas, manifiestos compactos y documentos de integración. Los datasets privados, HTML/PDF completos, credenciales y resultados voluminosos quedan fuera de Git.

Se prepara un **commit local** en `feat/unified-data-contract`. No se hace push, no se crea PR remoto y no se hace merge. El hash definitivo del commit se informa al cerrar la tarea, sin insertar referencias circulares dentro de ese mismo commit.

## 7. Segunda fuente: propuesta, no implementación

[PROPUESTA_MADRID_DRAFT_V2.md](../decisiones/PROPUESTA_MADRID_DRAFT_V2.md) especifica semántica, fechas/DST, esquema/ETL, migración, pruebas e impacto en ambos motores. El dimensionamiento de solo lectura identifica **656.930 candidatas URB/M30** de enero, con 656.930 claves distintas, sin convertirlas todavía en aceptadas.

La revisión separa duración de 15 minutos de `integration_sample_count`; mantiene `publisher_label` sin inventar inicio/fin, cuarentena de DST ambiguo/inexistente y de C30 no acreditado. Aprobarla y ejecutar sus pruebas podría llevar el total estimado a 1.733.743 lecturas reales de dos fuentes, pero **esa cifra no está cargada ni aceptada hoy**.

## 8. Garantía de alcance

No se modificaron PostgreSQL/MongoDB compartidos, Coolify, Tailscale ni infraestructura remota. No se iniciaron componentes de Sprint 2. Los únicos servicios ejecutados fueron contenedores propios locales, aislados de red, sin puertos publicados y posteriormente eliminados con sus volúmenes anónimos.
