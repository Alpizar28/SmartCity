# Investigación de datasets — Fases 0 y 1

Fecha: 2026-10-09; verificaciones fase 1 fechadas 2026-10-10 UTC por el reloj del entorno. **Fases 0 y 1 terminadas; fase 2 no iniciada. Dataset definitivo no seleccionado.**

## Entregables

- [00_requirements.md](00_requirements.md): requisitos oficiales, planificación del equipo, evaluación preliminar y preparación local.
- [00_query_matrix.csv](00_query_matrix.csv): 20 consultas obligatorias del sprint 1, 10 de Spark y 5 preguntas orientativas de Hadoop; atributos, posibles fuentes y verificación pendiente.
- [00_risks.md](00_risks.md): contradicciones, vacíos de cobertura y condiciones de aceptación para una futura fase 1.

### Fase 1

- [01_sources_catalog.csv](01_sources_catalog.csv): 30 fuentes concretas, URLs, campos, licencias, cobertura y estado de verificación.
- [01_research.md](01_research.md): investigación comparativa y evidencia documentada/comprobada/estimada/pendiente.
- [01_candidate_architectures.md](01_candidate_architectures.md): tres propuestas de integración, roles tecnológicos y cobertura condicionada de las 20 consultas.
- [01_download_methods.md](01_download_methods.md): mecanismos reales, comprobaciones limitadas, bloqueos y métodos futuros no ejecutados.
- [01_source_risks.md](01_source_risks.md): vacíos exactos, derivaciones frente a sintéticos y condiciones de rechazo.
- [01_shortlist.md](01_shortlist.md): Madrid, NYC y Londres para auditoría, sin elección definitiva.
- [01_http_evidence.csv](01_http_evidence.csv): bitácora adicional de probes HTTP con URLs, fecha UTC, tamaños leídos, código/error y hashes de prefijos.

La matriz `00_query_matrix.csv` conserva el snapshot de fase 0: no se reescribe como si aquellas pruebas hubieran ocurrido entonces. La actualización analítica de cobertura está en `01_candidate_architectures.md`; no son consultas implementadas/ejecutadas.

## Documentación leída

Los tres originales están en `/home/jp/Descargas/`. Se extrajo y leyó el texto completo de todas sus páginas con `pdftotext -layout`; se revisaron además imágenes del enunciado que contienen ejemplos, arquitectura y la rúbrica (incluida la página 3, sin texto extraíble). Las referencias E/P/I usan **páginas físicas del PDF**, numeradas desde 1.

| Clave | Archivo | Páginas | Autoridad |
|---|---|---:|---|
| E | `Proyectos_CE3101_Enunciado_Proyecto_II_Semestre_2026.pdf` | 28 | Enunciado y rúbrica oficiales suministrados |
| P | `Plan_de_trabajo.pdf` | 6 | Organización propuesta por el equipo; no reemplaza E |
| I | `Informe_Datasets_SmartCity_Jose.pdf` | 5 | Evaluación preliminar; puntuaciones no medidas |

SHA-256 de los originales:

```text
E 362210fab6ae08f8d4f333293edb7037371d2dcdd904d3a3fcafbe7cce3e45a3
P e72a2b2135d2892cb46e40c6929a43bb51e60f1bcc1c50a335c80df18b421107
I 5e7f90c7f40738b85704ae94816428119ab030b816ded1f806c6df898759af78
```

## Cómo interpretar la matriz

CSV UTF-8 separado por comas, con encabezado y campos entre comillas. `consulta` conserva las listas oficiales; `atributos_necesarios` es análisis técnico, no un esquema aprobado. `fuente_posible` es una hipótesis de búsqueda, **no cobertura confirmada**. `estado_verificacion` se refiere a los datos de origen, no a la existencia del requisito.

- `PENDIENTE_MUESTRA`: falta comprobar campos, significado y cobertura con datos reales.
- `SIN_FUENTE_COMPROBADA`: hay un vacío documental explícito; una fuente candidata no demuestra el atributo.
- `PENDIENTE_IMPLEMENTACION_Y_MUESTRA`: además depende de construir una vista, función o pipeline.
- Todas las filas tienen `evidencia_datos = Ninguna muestra inspeccionada en fase 0`.
- `naturaleza_requisito` distingue obligación de preguntas orientativas. No hay una lista oficial numerada de diez consultas Hadoop.

Los códigos de fuentes se resuelven en `00_requirements.md`, sección 6. No confundir `CO` con `CO₂`, una estación con cada dispositivo, ni una solicitud 311 con una alerta automática.

## Límites históricos de fase 0

Solo se crearon estos cuatro archivos de investigación. No se instalaron paquetes ni infraestructura, no se descargaron datasets, no se generaron datos sintéticos y no se conectó a PostgreSQL/MongoDB remotos. Las únicas solicitudes externas fueron HEAD a páginas públicas para probar acceso a Internet; no verifican datasets. No se ejecutaron instrucciones de instalación del README existente.

La fase 1 fue autorizada por el usuario posteriormente y amplió la búsqueda a ocho escenarios/repositorios. Se consultaron metadatos, muestras/prefijos pequeños y diccionarios; no se descargaron datasets grandes ni se generaron sintéticos, no se accedió a bases privadas ni se modificó infraestructura. Los límites de fase 0 de arriba son históricos, no describen las solicitudes adicionales de fase 1.

## Estado actual y siguiente autorización

Tres paquetes candidatos para **auditoría**, no datasets aceptados. Ninguno acredita todavía todos los atributos/KPIs con fuentes reales; faltantes y bloqueos son explícitos. No hubo commit, push ni merge. **Fase 2 pendiente de autorización expresa**, con alcance y presupuesto de muestras/descargas; no concede acceso remoto a PostgreSQL/MongoDB/Coolify/Tailscale por defecto.
