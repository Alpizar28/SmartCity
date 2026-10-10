# Fuentes, versiones y procedencia

## Núcleo propuesto: Madrid, enero de 2025

Publicador: **Ayuntamiento de Madrid**. La condición municipal CC BY 4.0 fue documentada y comprobada en la investigación; exige atribución, enlace a licencia e indicación de cambios. Publicador no equivale automáticamente a propietario, operador o responsable de cada dispositivo. No se ha acreditado identidad física individual.

| Dominio y recurso oficial | Formato original / período real del snapshot | Variables y unidad | Selección propuesta |
|---|---|---|---|
| [Aire horario](https://datos.madrid.es/dataset/201200-0-calidad-aire-horario) | CSV UTF-8 con separador `;`; filas diarias, H01–H24/V01–V24; archivo auditado enero 2025–agosto 2026 | Magnitudes por estación/técnica: entre otras NO₂, PM2.5, PM10, O₃ y SO₂ en µg/m³; CO en mg/m³. La lista exacta por código está en el diccionario | `ANO=2025`, `MES=1`, todos los canales publicados; 91.959 horas elegibles |
| [Meteorología horaria](https://datos.madrid.es/dataset/300352-0-meteorologicos-horarios) | CSV UTF-8 `;`, H/V horarios; archivo auditado enero 2025–agosto 2026 | 81 viento, 82 dirección, 83 temperatura, 86 humedad, 87 presión, 88 radiación, 89 precipitación. **Unidades analíticas NULL**, candidatas pendientes de diccionario técnico | Enero de 2025; 66.005 horas elegibles |
| [Tráfico histórico](https://datos.madrid.es/dataset/208627-0-transporte-ptomedida-historico) | ZIP íntegro con miembro CSV `01-2025.csv`; intervalo publicado, no siempre de 15 min | `intensidad` veh/h; `ocupacion` y `carga` porcentuales; `vmed` km/h según tipo; `periodo_integracion` 1–30 min; `error`, `tipo_elem`, `id`, `fecha` | Estrato `int(id)%20=0` durante enero; 674.704 intervalos elegibles, multivariables |

Los conteos, filtros y períodos están en [05_dataset_manifest.md](../../research/datasets/05_dataset_manifest.md), [preparation.json](../../research/datasets/results/phase5/preparation.json) y [02_audit_report.md](../../research/datasets/02_audit_report.md). La selección no representa todo el tráfico de Madrid ni todas las variables en todas las estaciones.

### Inventarios auxiliares

- [Estaciones de aire](https://datos.madrid.es/dataset/212629-0-estaciones-control-aire).
- [Estaciones meteorológicas](https://datos.madrid.es/dataset/300360-0-meteorologicos-estaciones).
- [Puntos de tráfico](https://datos.madrid.es/dataset/202468-0-intensidad-trafico).

Son catálogos independientes de sitios, **no inventarios completos de sensores físicos o canales históricos**. Conservan códigos, nombres y coordenadas originales; su vigencia para enero de 2025 no está acreditada. Aire/meteo no reciben un distrito inventado. El distrito de tráfico procede del inventario publicado, con vigencia histórica pendiente.

## Versiones exactas reutilizadas

Cada SHA-256 identifica bytes del snapshot, no una garantía de permanencia de la URL. El [manifiesto de descarga](../../research/datasets/02_download_manifest.csv) conserva URL solicitada/final, fecha UTC, HTTP, tamaño, ETag, recurso y ruta local. `source_snapshots` en [preparation.json](../../research/datasets/results/phase5/preparation.json) reúne los seis inputs del núcleo y catálogos. No se redistribuyen aquí los archivos completos.

| Recurso de manifiesto | SHA-256 completo |
|---|---|
| MAD-AIR-file | `9122af41d3e73e71f5a0e0a22b99a0cefbd4c7f8abe9e2fae344207482398471` |
| MAD-METEO-file | `ada9304d302ead850e45c404d279762b774cd6671391febfc531f6c3033f3852` |
| MAD-TRAFFIC-Jan2025 | `4c3aac6c95939995ca6afd3b90c96ac72e59beb8770c34c6da5c92c20d8d167c` |
| 212629-0-estaciones-control-aire-inventory | `2c84ca974088a6d5de13509489196ddefeee83fcae4999798b00603aa951cd1b` |
| 300360-0-meteorologicos-estaciones-inventory | `a95a5d26d27912751589526dc13e6cf729cf49fd8222dc990d3030660acdb7c6` |
| MAD-TRAFFIC-META-file | `2cd3a4e97a4e25589068616148cd84841dfa1db71844247f5bb874648e961286` |
| MAD-ENERGY-file, complemento | `3346b8bf8f5b46fe77180e993c255f530f2a9d4056b42dfac245b69a9a755578` |
| MAD-CRASH-file, complemento | `25a84e6af0b213d6194df7c378490ef9c68e0156c165e0761a0a6c7b7ae4e321` |

Los dos últimos hashes y URLs exactas constan en [snapshots seleccionados de Fase 4](../../research/datasets/results/phase4/selected_source_snapshots.csv). El campo histórico `period=2025` de aire/meteo no limita su cobertura real: manda el contenido auditado, no una etiqueta de descarga.

## Complementos separados

| Fuente | Naturaleza / período | Restricción de uso analítico |
|---|---|---|
| [Accidentes con detalle](https://datos.madrid.es/dataset/300228-0-accidentes-trafico-detalle) | CSV municipal de **2026**; 33.322 filas de detalle y 14.388 expedientes distintos; dos expedientes con categoría desconocida | Una fila de persona/vehículo no es un accidente. Colección propuesta `incidents_2026`, fuera de la muestra nativa de enero de 2025. No mover fechas ni relacionarlos como hechos contemporáneos |
| [Consumo municipal](https://datos.madrid.es/dataset/300430-0-consumo-energia-edificios) | CSV de reportes **mensuales**; cobertura publicada desde marzo de 2020; rango efectivo del snapshot descrito en las métricas de esquema | Edificio/medidor/mes y niveles jerárquicos. kWh, kvarh y m³ no se suman; no dividir consumo mensual para fabricar energía horaria. Propuesta `energy_reports_monthly` |

Evidencia de incidentes: [incident_checks.json](../../research/datasets/results/phase3/incident_checks.json). Perfil energético, nulos y rango original: [MAD-ENERGY-schema_quality.json](../../research/datasets/results/MAD-ENERGY-schema_quality.json). La jerarquía de medidores y claves requiere revisión antes de totales. No se acreditó fuente de concentración ambiental de CO₂ ni de tiempos de recorrido.

## Identificación y linaje por atributo

El [contrato histórico `madrid-draft-v1`](../../research/datasets/05_data_contract.md) y [diccionario de 75 entradas](../../research/datasets/05_data_dictionary.csv) son borradores de Fase 5 para revisión. El contrato provisional vigente es [`madrid-draft-v1-frozen`](../../CONTRATO_PROVISIONAL_DATASET.md); conserva los límites de la evidencia sin reescribir resultados históricos. Distinguen `station_id`, `sensor_id`, `channel_id`, `measurement_type`, `location_id` y `measurement_id`.

- Estación/sitio: namespace de fuente y código original; una co-localización no fusiona redes.
- Dispositivo físico: `sensor_id=NULL` sin evidencia verificable. No sustituirlo por el código de estación.
- Canal ambiental: fuente, estación, magnitud y punto/técnica; meteo conserva punto vacío como NULL.
- Canal de tráfico: fuente, ID y tipo; cada intervalo contiene conjuntamente las variables disponibles.
- Observación: ID SHA-256 de tupla JSON canónica `sca-id-v1`, canal, UTC y papel temporal; no usa valor ni número de fila para disimular conflictos.
- `source_version`: hash del snapshot. `raw_reference`: archivo, miembro y fila/columna según fuente; `inventory_reference`: snapshot auxiliar.
- `data_origin=observed` para mediciones; IDs y normalización temporal son derivados por atributo. `synthetic` se reserva a fixtures CRUD no métricos aislados, no a completar ausencias.

El UTC de meteo/tráfico está calculado bajo hipótesis local pendiente. Cambiar el reloj puede cambiar IDs: requiere migración revisada y correspondencia con la clave original, no sumar dos versiones como nuevas mediciones.

## Licencias, atribución y publicación

Referencias oficiales verificadas durante las fases previas:

1. Ayuntamiento de Madrid. [Condiciones de uso](https://datos.madrid.es/pages/condiciones-de-uso); [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Evidencia HTTP M25 y registros posteriores en los manifiestos.
2. NYC DOT. [Automated Traffic Volume Counts](https://data.cityofnewyork.us/d/7ym2-wayt) y [311](https://data.cityofnewyork.us/d/erm2-nwe9). Términos municipales y privacidad por revisar antes de redistribuir; Socrata no implica CC BY.
3. EPA. [AQS AirData](https://aqs.epa.gov/aqsweb/airdata/download_files.html), PM2.5 horario 2023; condiciones públicas y excepciones de proveedores, no una licencia SPDX universal inferida.
4. LAQN. [API](https://www.londonair.org.uk/Londonair/API) y [copyright](https://www.londonair.org.uk/london/asp/copyright.asp): finalidad informativa/educativa, no operativa/comercial; sin permiso general de redistribución acreditado.
5. UK Power Networks. [Low Carbon London](https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d): CC BY 4.0 documentada. No concede derechos sobre LAQN.
6. DfT. [Road traffic downloads](https://roadtraffic.dft.gov.uk/downloads): OGL v3 enlazada. TfL requiere sus propias condiciones.

No se reconsultaron estas condiciones en Fase 6. Publicar documentación original, código y métricas agregadas no implica permiso para distribuir datasets o PDFs íntegros. Los tres PDF académicos originales y sus transcripciones completas quedan locales hasta confirmar autorización; sus hashes y referencias sí se conservan. No se añade una licencia general al repositorio en nombre del equipo.

Modelo de atribución para una futura exportación permitida: «Fuente: Ayuntamiento de Madrid, [nombre y URL del recurso], snapshot obtenido el [UTC del manifiesto], CC BY 4.0. Transformaciones: filtro temporal/QA, normalización e IDs según contrato [versión]; no producto oficial del Ayuntamiento». La redistribución de accidentes requiere además minimización de información personal; la muestra publicada mínima corresponde solo al núcleo no personal. Véase [control de publicación](../equipo/revision_repositorio.md).
