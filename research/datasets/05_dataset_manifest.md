# Fase 5 — Manifiesto del núcleo inicial propuesto

**Madrid sigue condicionado (63,665/100 de Fase4).** Esta fase autoriza preparación y pruebas locales, no ratifica la decisión académica ni una carga definitiva. Contrato `madrid-draft-v1` para revisión de los cuatro integrantes.

## Archivos originales y versiones

| Recurso | Archivo | Versión SHA256 | URL oficial |
|---|---|---|---|
| MAD-AIR-file | `raw/MAD-AIR-file.attempt1.bin` | `9122af41d3e73e71f5a0e0a22b99a0cefbd4c7f8abe9e2fae344207482398471` | https://datos.madrid.es/dataset/201200-0-calidad-aire-horario/resource/201200-1-calidad-aire-horario-csv/download/201200-1-calidad-aire-horario-csv.csv |
| MAD-METEO-file | `raw/MAD-METEO-file.attempt1.bin` | `ada9304d302ead850e45c404d279762b774cd6671391febfc531f6c3033f3852` | https://datos.madrid.es/dataset/300352-0-meteorologicos-horarios/resource/300352-180-meteorologicos-horarios-csv/download/300352-180-meteorologicos-horarios-csv.csv |
| MAD-TRAFFIC-Jan2025 | `raw/MAD-TRAFFIC-Jan2025.record89.bin` | `4c3aac6c95939995ca6afd3b90c96ac72e59beb8770c34c6da5c92c20d8d167c` | https://datos.madrid.es/dataset/208627-0-transporte-ptomedida-historico/resource/208627-73-transporte-ptomedida-historico-zip/download/208627-73-transporte-ptomedida-historico-zip.zip |
| 212629-0-estaciones-control-aire-inventory | `raw/212629-0-estaciones-control-aire-inventory.record39.bin` | `2c84ca974088a6d5de13509489196ddefeee83fcae4999798b00603aa951cd1b` | https://datos.madrid.es/dataset/212629-0-estaciones-control-aire/resource/212629-0-estaciones-control-aire-csv/download/212629-0-estaciones-control-aire-csv.csv |
| 300360-0-meteorologicos-estaciones-inventory | `raw/300360-0-meteorologicos-estaciones-inventory.record41.bin` | `a95a5d26d27912751589526dc13e6cf729cf49fd8222dc990d3030660acdb7c6` | https://datos.madrid.es/dataset/300360-0-meteorologicos-estaciones/resource/300360-1-meteorologicos-estaciones-csv/download/300360-1-meteorologicos-estaciones-csv.csv |
| MAD-TRAFFIC-META-file | `raw/MAD-TRAFFIC-META-file.attempt1.bin` | `2cd3a4e97a4e25589068616148cd84841dfa1db71844247f5bb874648e961286` | https://datos.madrid.es/dataset/202468-0-intensidad-trafico/resource/202468-306-intensidad-trafico/download/202468-306-intensidad-trafico.csv |

Origen: Ayuntamiento de Madrid; CC BY4.0 documentada en Fase1, atribución obligatoria. Los seis snapshots fueron verificados por SHA completo. No se descargó ningún dataset de nuevo. E/P/I originales conservan los hashes de Fase4, y las 48 pruebas de continuidad pasaron otra vez; evidencia `results/phase5/preflight.json` y `baseline_tests.xml`.

## Selección exacta de registros

- Aire y meteo: filas originales con `ANO=2025` y `MES=1`, todos los sitios, magnitudes y puntos/técnicas publicados; H01..H24 se expanden a **horas realmente publicadas**, no mediciones artificiales. Aire:3905 filas diarias/93720 slots; meteo:2892/69408. Conservar H24 del31 de enero (endpoint local1 de febrero, UTC31 de enero23:00). No incluir julio ni seleccionar por mes UTC.
- Tráfico: miembro `01-2025.csv` del ZIP auditado; estrato determinista `int(id)%20=0` durante enero completo. Conserva los nueve campos originales y número de fila, no solo intensidad. Se recuperaron los campos faltantes mediante una extracción dirigida del ZIP local; no se repitió una auditoría general ni se extrapoló unicidad a los13.218.804 registros del ZIP completo.
- Elegibilidad: flag V ambiental o N tráfico, valor principal finito; intensidad no negativa, tipo URB/M30/C30, duración entera1..30min, fecha de enero, unicidad y referencias de catálogo. Unidades meteo siguen **NULL/candidatas**; elegibilidad estructural no valida automáticamente interpretación científica, reloj o geografía histórica.
- Inventarios completos de sitios/puntos se conservan como catálogo independiente de sitios; canales observados no equivalen a un inventario independiente de dispositivos. Sitios sin datos no se califican como averiados.

| Fuente enero2025 | Registros/slots seleccionados | Elegibles estructurales únicos | Rechazados | Duplicados/conflictos |
|---|---|---|---|---|
| MAD-AIR | 93720 | 91959 | 1761 | 0/0 |
| MAD-METEO | 69408 | 66005 | 3403 | 0/0 |
| MAD-TRAFFIC | 677724 | 674704 | 3020 | 0/0 |

Total estructural único: **832668**, distinto de los993374 hechos enero+julio de Fase3. Identidades exactas en `private_results/phase5/identity_ledger.sqlite`; SHA de ledger, cache y muestra en `preparation.json`. No versionar ese ledger ni datos voluminosos.

## Separaciones obligatorias

MAD-CRASH2026: mismo archivo/hash de Fase4,14388 expedientes, no33322 accidentes; dos categorías desconocidas. Solo complemento separado2026, no presente en la muestra nativa de enero2025 ni relacionado causalmente con sensores. MAD-ENERGY: recurso mensual municipal separado (snapshot y período publicado en manifiesto02), unidades/niveles distintos; nunca consumo horario por división del mensual. Accidente2025 requeriría recurso real y validación futura autorizada. No se atribuyen CO2 ni tiempos de recorrido a CO, NO2, velocidad o intensidad.

Las condiciones académicas, unidades, clocks provisionales, CRS y vigencias quedan abiertas. Núcleo propuesto, **no fuentes definitivamente aprobadas**.
