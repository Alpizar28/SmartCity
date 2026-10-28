# Calidad, limpieza y limitaciones del núcleo propuesto

## Población y conteos verificables

Autoridad: [preparation.json](../../research/datasets/results/phase5/preparation.json), `counts.*`; reglas y selección en [05_dataset_manifest.md](../../research/datasets/05_dataset_manifest.md). Son **observaciones estructuralmente elegibles**, no sensores físicos, ni datos científicamente ratificados, ni cargas definitivas.

| Enero de 2025 | Slots/intervalos seleccionados | Elegibles únicos | Excluidos | Extras duplicados / claves conflictivas |
|---|---:|---:|---:|---:|
| Aire | 93.720 | 91.959 | 1.761 | 0 / 0 |
| Meteorología | 69.408 | 66.005 | 3.403 | 0 / 0 |
| Tráfico, estrato ID | 677.724 | 674.704 | 3.020 | 0 / 0 |
| **Total** | **840.852** | **832.668** | **8.184** | **0 / 0** |

El total suma observaciones ambientales horarias y documentos de intervalos de tráfico; no implica idéntica frecuencia entre redes. Los **993.374 hechos** de Fase 3 incluían enero y julio, con un modelo de prueba anterior: [postgres_execution.json](../../research/datasets/results/phase3/postgres_execution.json). No son una segunda población del núcleo actual ni se suman a ella.

## Reglas aplicadas y reproducibilidad

1. **Originales:** snapshots inmutables; SHA-256 antes de usar y CRC del miembro ZIP completo. Una respuesta HTTP completa no demuestra por sí sola integridad del dataset.
2. **Filtro:** aire/meteo por `ANO=2025` y `MES=1`, no por mes UTC. Tráfico por `int(id)%20=0` en enero; selección determinista, no aleatoria ni representativa de todas las vías.
3. **Granularidad:** H01–H24 son horas reales publicadas. No contar fila diaria y horas como mediciones adicionales. Tráfico mantiene un intervalo multivariable por documento/fila; no dividir ocupación, carga o velocidad para inflar el volumen.
4. **Elegibilidad:** flag `V` ambiental o `N` de tráfico, valor principal finito; intensidad no negativa, tipo URB/M30/C30, duración entera de 1–30 min, claves únicas y referencias coherentes. La bandera de QA no representa estado administrativo.
5. **Nulos y ceros:** NULL no se rellena con cero. Un cero válido permanece. `vmed=0` URB se preserva en original y queda NULL analítico, no velocidad medida. Valores opcionales ausentes no invalidan una intensidad elegible.
6. **Unicidad:** ledger local de identidad y hash de payload. Repetición idéntica permite replay; una misma clave con payload distinto bloquea/cuarentena, no sobrescribe ni cambia artificialmente la PK.
7. **Extremos:** no eliminar automáticamente máximos ni IQR; un candidato estadístico no demuestra error ni evento crítico. No se imputan observaciones faltantes.
8. **Procedencia:** hashes de inputs/outputs, localizador de fila/columna/miembro, reglas/versiones y origen por campo. Los originales retenidos permiten explicar exclusiones; no hubo síntesis de mediciones.

Implementación acotada: [phase5_contract.py](../../research/datasets/scripts/phase5_contract.py) y [phase5_prepare.py](../../research/datasets/scripts/phase5_prepare.py). La exportación está limitada a una muestra; la validación estructural de la selección completa usa ledger, no una carga masiva en motores.

## Tiempo, unidades y geografía

| Aspecto | Regla vigente | Limitación que impide afirmaciones definitivas |
|---|---|---|
| Aire H24 | Fin de hora 23–24, endpoint local del día siguiente; conservar H24 del 31 de enero | La selección se hace por fecha fuente, aunque `original_time` sea 1 de febrero |
| UTC/DST | `Europe/Madrid`, `zoneinfo`; instante UTC en SQL/BSON; conservar reloj original y papel temporal | Aire local documentado; **meteo/tráfico bajo hipótesis local pendiente**, no sincronía científica confirmada |
| Ampliación anual | Rechazar hora ambigua o inexistente sin evidencia de fold; no fabricar hora otoñal eliminada por publicador | Enero no resuelve DST anual; cambios de clock requieren nueva versión/migración de IDs |
| Unidades | Aire según diccionario, tráfico por campo/tipo; promediar solo misma variable/unidad | Meteo `unit=NULL`, `candidate_unit` y estado visibles; no presentarlo como grados/hPa confirmados |
| CRS | Preservar decimales y coordenadas originales, `coordinate_crs=unverified_decimal_geographic` | No WGS84 asumido, transformación, GeoJSON ni índice `2dsphere`; ETRS89 original no acredita todos los grupos de campos |
| Zonas | Aire/meteo NULL; tráfico distrito publicado en inventario | Posición y distrito históricos de enero de 2025 pendientes; proximidad no zona oficial ni identidad física |

Detalle de contrato y casos temporales: [05_data_contract.md](../../research/datasets/05_data_contract.md). Los joins exploratorios anteriores deben revalidarse si cambian relojes, unidades o vigencias; las puntuaciones históricas no se presentan como aprobación de esas hipótesis.

## Volumen potencial frente a ejecución

| Objetivo académico | Evidencia disponible | Lo que no se ha demostrado |
|---|---|---|
| 100.000 PostgreSQL | 832.668 candidatos estructurales actuales; 5.000 hechos probados en `draft5` | Carga mínima definitiva con contrato ratificado; maestros no se inflan |
| 500.000 MongoDB | 674.704 intervalos elegibles de tráfico; muestra mixta de 5.000 documentos | 500.000 documentos importados/validados en diseño final o bases compartidas |
| 1.000.000 Spark | Enero aporta 832.668, **inferior al mínimo**; histórico aire local contiene 1.795.279 slots V | Normalización UTC/QA anual definitiva, cardinalidad anual final y ejecución Spark distribuida |

Autoridad: [05_volume_strategy.md](../../research/datasets/05_volume_strategy.md), [aire completo](../../research/datasets/results/MAD-AIR-annual_counts.json), [muestra PostgreSQL](../../research/datasets/results/phase5/postgresql_sample.json) y [muestra MongoDB](../../research/datasets/results/phase5/mongodb_execution.json). Los slots V del archivo 2025–agosto 2026 no se llaman un año completo validado ni un resultado Spark. Tamaños de [storage.json](../../research/datasets/results/phase5/storage.json) distinguen bytes medidos de estimaciones; no incluyen índices, WAL, réplicas ni backups. Datos en bytes no sustituyen mínimos por motor.

## Brechas académicas y analíticas

- `sensor_id` NULL; cero identidades físicas acreditadas. Sitios/canales reales no constituyen instalación, estado, organismo individual o responsable personal.
- Primera lectura ≠ instalación; ausencia de lecturas ≠ falla; flag QA ≠ estado administrativo; publicador ≠ propietario/operador.
- Usuarios son datos de aplicación: aún no hay usuarios de demostración aprobados/consentidos en la muestra.
- MG04 necesita política de críticos; MG05 evidencia de emisión; no se generaron eventos/alertas. Un replay actual no acredita alertas oficiales de 2025.
- Accidentes de **2026** son complemento separado, no contemporáneos del tráfico de enero de 2025. MG08 requiere prueba nativa separada y autorización.
- Energía es **mensual**, no horaria. Jerarquía de medidores y unidades heterogéneas impiden sumas ingenuas.
- No hay fuente acreditada de **CO₂ ambiental** ni **tiempos de recorrido**. CO/NO₂/CO₂e/velocidad no son sustitutos silenciosos.
- Intensidad veh/h es tasa, no número de vehículos; requiere exposición/duración/cobertura para derivar conteos defendibles. Congestión no se declara validada solo por `carga`.
- La cuota de primeras observaciones válidas usada en las pruebas es reproducible, **no representativa de Madrid**. Una única corrida de tiempos no es benchmark de producción.
- Hadoop/HDFS, Spark, Streamlit, procesamiento distribuido, backup/restore y rendimiento remoto no fueron ejecutados.

Resolver con fuente real o aceptación explícita de alcance; no completar metadatos mediante invenciones. Véase el [ADR condicionado](../decisiones/ADR-001-madrid.md).
