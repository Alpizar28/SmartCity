# Propuesta `madrid-draft-v2`: segunda fuente real de tráfico

**Actualización 27/10/2026:** el usuario autorizó implementar la segunda fuente
y las consultas Mongo pendientes en un entorno local. La ruta nueva está en
`sprint1/basico/preparar_v2.py`, `scripts/validar_v2.py` y
`sprint1/postgres/contract_v2.sql`. La preparación de enero produjo **748.889
lecturas reales**: 91.959 de aire y 656.930 de tráfico. La carga nativa se
verifica aparte; preparación no significa carga terminada.

La autorización es de implementación local, no aprobación docente del contrato,
del umbral demo, de alternativas por canal ni de cambios al servidor compartido.
La especificación de diseño que sigue se conserva como referencia. V1 no cambia.

## 1. Por qué se necesita otra revisión

La implementación preliminar interpreta `periodo_integracion` como minutos. El [intérprete oficial de históricos de tráfico](https://datos.madrid.es/dataset/208627-0-transporte-ptomedida-historico/resource/208627-81-transporte-ptomedida-historico/download/208627-81-transporte-ptomedida-historico.pdf), páginas 4–5, establece dos conceptos distintos:

- La base SICTRAM integra en **periodos de 15 minutos**.
- `periodo_integracion` es el **número de muestras recibidas y consideradas**.

No es seguro corregir solo `timestamp_status`, renombrar una columna o reinterpretar datos ya exportados sin versionarlos. Las lecturas de tráfico de enero siguen en cuarentena en v1. La documentación describe `fecha` como «fecha y hora oficiales de Madrid», no como hora UTC; no define inequívocamente si la etiqueta es inicio o fin del intervalo.

Procedencia verificada: SHA-256 del PDF `17562978ce1b7930c6c720db37f055cb3459e30b8cec50d2a671682b215b9de9`; URL, adquisición y hash registrados en `research/datasets/results/expanded-2025/research_sources.json`. Las citas son del publicador, no de tesis o convenciones inferidas.

## 2. Cambios semánticos propuestos

| Campo | Decisión propuesta v2 | Evidencia / límite |
|---|---|---|
| `interval_minutes` | Constante documentada **15** para esta fuente histórica | Periodo de integración SICTRAM, p. 4; nunca copiar `periodo_integracion` |
| `integration_sample_count` | Nuevo entero positivo con el valor original de `periodo_integracion` | p. 5; no imponer máximo 15: el snapshot contiene hasta 30 muestras |
| `original_time` | Conservar literalmente el reloj local publicado, con formato normalizado sin pérdida | Validar ISO real del CSV; el formato `dd/mm/yyyy` del PDF no coincide con este snapshot |
| `original_timezone` | `Europe/Madrid` | «Fecha y hora oficiales de Madrid», p. 4; no usar zona del host |
| `timestamp_role` | **`publisher_label`** | No atribuir inicio/fin cuando el documento no lo acredita |
| `timestamp_status` | `publisher_confirmed_local` solo tras validaciones y aprobación de esta revisión | Referencia explícita al documento y su hash |
| `observed_at` | UTC únicamente para etiquetas locales inequívocas y existentes | `zoneinfo`, round-trip; no inventar `fold` |
| `value` / `measurement_type` | Intensidad original finita y no negativa, `MAD-TRAFFIC:intensidad` | Intensidad veh/h publicada; no dividir por cuatro ni crear otra observación de conteo |
| `quality_flag` | Solo **N** se propone como aceptado | E/S/vacío quedan en cuarentena; calidad no equivale a estado administrativo |
| `element_type` | Aceptar inicialmente URB y M30; C30 en cuarentena | El documento enumera Urbano y M30; C30 requiere evidencia adicional |
| `measurements.ocupacion` | Porcentaje publicado, rango documentado 0–100; negativo → faltante explícito | Guardar raw y causa; no tratar sentinelas como valores reales |
| `measurements.carga` | Índice documentado 0–100, no porcentaje físico acreditado | Corregir etiqueta de unidad a índice adimensional en v2, con evidencia |
| `measurements.vmed` | km/h solo para M30 con valor no negativo | URB no acredita velocidad; conservar raw sin presentar cero como medición válida |

Las variables complementarias siguen dentro del mismo documento/intervalo. Un dato opcional inválido se representa como faltante con estado y raw; no se imputa ni se multiplica el número de observaciones. La política exacta de rechazo opcional y sus estados se debe aprobar en el diccionario v2 antes de generar datos.

`schema_version` y `catalog_version` pasan a `madrid-draft-v2`; transformación propuesta `madrid-normalize-v3`, con método estable y algoritmo versionado. Se preservan `source_version` SHA-256 del ZIP, miembro original, fila, columna y raw de campos afectados. Mantener la nomenclatura y los IDs compartidos; no añadir UUID ni IDs por motor.

## 3. Tiempo y DST

1. Parsear estrictamente las etiquetas del snapshot; rechazar fechas inválidas o formatos mezclados no documentados. No adivinar día/mes ni tratar fechas sin zona como UTC.
2. Convertir el reloj oficial de Madrid con `Europe/Madrid`, independiente de la zona del host.
3. Hora inexistente de primavera → cuarentena; hora ambigua de otoño sin offset/fold acreditado → cuarentena. No desplazarla a una hora válida ni elegir primera/segunda ocurrencia.
4. Fuera de esas horas, comprobar round-trip local → UTC → local e identidad temporal única.
5. No exigir ni inventar continuidad perfecta. Huecos, sustituciones y muestras faltantes se reportan; no se rellenan.
6. `publisher_label` no permite construir límites exactos de intervalo, joins por solapamiento o simultaneidad científica con aire. Los análisis por fuente sí son posibles. La integración mínima puede ser contractual y de catálogos, sin afirmar sincronización demostrada.

Enero de 2025 no incluye cambios DST. Para ampliar a marzo/octubre deben ejecutarse fixtures y casos reales, manteniendo en cuarentena lo no desambiguable. No se afirma conocer cómo el publicador resolvió históricamente el fold: precisamente por eso se rechazan los casos ambiguos.

## 4. Volumen recuperable: estimación basada en lectura real

Se evaluó el estrato auditado **ID % 20 == 0**, no el ZIP completo, usando el cache con SHA-256 `6f1e7c63e8267e0bdcfa62e5e8890d2b6aae1b91f71b8a36d81d43ba0f2bb848`. El ZIP original tiene SHA-256 `4c3aac6c95939995ca6afd3b90c96ac72e59beb8770c34c6da5c92c20d8d167c`.

| Control del estrato enero 2025 | Filas |
|---|---:|
| Total seleccionado | 677.724 |
| Flag N | 674.704 |
| Flag vacío | 3.020 |
| Clase URB | 611.153 |
| Clase M30 | 48.797 |
| Clase C30 sin significado acreditado | 17.774 |
| **Candidatas bajo política conservadora propuesta** | **656.930** |
| Candidatas URB | 611.153 |
| Candidatas M30 | 45.777 |
| Claves lógicas distintas entre candidatas | 656.930 |
| Extras duplicados entre candidatas | 0 |

Criterios de dimensionamiento: N, intensidad finita/no negativa, clase URB/M30, etiqueta de enero válida, muestra contada como entero no negativo (todas las candidatas tienen de 1 a 30). **Esto NO es una exportación aceptada ni una validación de payloads v2.** Los conflictos y cargas nativas v2 todavía deben probarse. Los 17.774 C30 y 3.020 flags vacíos se excluyen; no se ocultan para alcanzar volumen.

Si la revisión y pruebas confirmaran todas esas candidatas, el conjunto combinado podría alcanzar **1.733.743 observaciones reales distintas**: 1.076.813 aire anual + 656.930 tráfico enero. Es una estimación técnica, no un conteo cargado ni un requisito ya cumplido. No extrapolar el estrato al ZIP completo multiplicando por 20 como si fuera evidencia.

Reproducir el dimensionamiento, sin alterar contratos ni datos:

```bash
.venv/bin/python research/datasets/scripts/traffic_v2_assessment.py
```

Evidencia compacta: `research/datasets/results/expanded-2025/traffic_v2_assessment.json`.

## 5. DDL y ETL propuestos, pendientes de aprobación

### PostgreSQL

- Conservar **una única definición lógica** en `smartcity`; desarrollar la revisión en otra base local desechable, no crear un diseño alternativo permanente `sprint1`/`draft5`.
- Añadir `integration_sample_count integer` nullable para fuentes que no lo publican; para tráfico aceptado exigir positivo y `interval_minutes=15`.
- Versionar CHECK de `schema_version`, `catalog_version`, dominios y reglas de unidades; no ampliar estados para aceptar una interpretación todavía no aprobada.
- Preservar PK `measurement_id`, unicidad canal/UTC/rol y FK de fuente/estación/canal/tipo/versión. Mantener inmutabilidad de observaciones.
- Extender `observation_contract` con el campo nuevo y los estados complementarios necesarios. Índices solo tras medición; no crear índices duplicados.

### ETL común

- Reutilizar `stable_id`, JSON canónico, validación temporal y referencias de origen; parametrizar lectores por política versionada y mes, sin duplicar el ETL de aire.
- Interpretar el campo original como conteo, conservarlo, y asignar duración 15 desde la evidencia documental.
- Mantener un intervalo como una observación; validar antes de aceptar; separar cuarentena y conflictos.
- Extender los catálogos con significado, origen, unidad y evidencia de cada campo y clase aceptados.
- Escribir en una nueva generación sellada, por ejemplo `expanded-v2-2025`, nunca sobre `expanded-2025` ni sobre la cuarentena v1.

### MongoDB

- `readings` estándar; mismo `_id=measurement_id` del ETL y fecha BSON Date real.
- Añadir validación de `integration_sample_count` y duración 15 bajo la revisión v2.
- Preservar índices únicos y validación de referencias; no recalcular IDs ni convertir muestras en documentos adicionales.
- Actualizar el importador de Kembly mediante cambios revisados en su implementación, no sustituirlo por el harness de prueba.
- `derived_events`, alertas, incidentes, energía, metadata dinámica y demos mantienen procedencia y ciclo de vida propios.

## 6. Migración desde v1: sin sobrescritura silenciosa

1. Conservar íntegros manifiestos, catálogos, exportaciones y evidencia v1.
2. Aprobar diccionario, contrato y reglas v2 antes de codificar la interpretación nueva.
3. Regenerar **desde originales** el paquete v2 de ambas fuentes en un directorio nuevo. No convertir en sitio el `interval_minutes` erróneo de los prototipos.
4. Los algoritmos de ID no cambian. Aire conserva los mismos IDs; cambiar versión/metadatos cambia su `payload_hash`. Tráfico, si se mantiene canal/etiqueta/rol, puede compartir IDs con prototipos provisionales; eso **no** autoriza mezclar payloads ni tratarlos como observaciones previamente aceptadas.
5. Por ese motivo, un lote v2 **no es un replay normal sobre una base v1**. Los conflictos esperados de versión se resuelven mediante migración explícita a una base/colección local nueva y revisión, no desactivando triggers o sobrescribiendo lecturas.
6. Producir correspondencia por `measurement_id`, fuente, referencia original, hash v1/v2 y motivo del cambio; registrar registros añadidos y cuarentenas conservadas/resueltas. Si cambia una identidad por evidencia temporal futura, conservar también la relación explícita old/new.
7. Ejecutar la carga completa, replay completo y reconciliación SQL/Mongo v2. Confirmar conteos por fuente/mes, IDs, valores, metadatos y cuarentena.
8. Daniel y Kembly revisan sus consultas/importadores; Fernanda actualiza la entrega oficial. Recién después se propone un procedimiento remoto separado con respaldo, permisos y recuperación. **Esta propuesta no autoriza ejecutarlo.**

## 7. Pruebas obligatorias antes de aceptar v2

- `periodo_integracion=30` produce `integration_sample_count=30` y `interval_minutes=15`, nunca 30 minutos.
- Caso de aire conserva valor y mismo ID; cambios de hash por versión quedan documentados como migración, no como conflicto oculto.
- Fecha local enero inequívoca convierte UTC+1; caso de verano inequívoco UTC+2; límites de mes y año preservados.
- Primavera inexistente y otoño ambiguo van a cuarentena sin fold inventado; formatos inválidos se rechazan.
- Flag E/S/vacío y clases no acreditadas como C30 quedan fuera de aceptados; cero imputaciones.
- Sentinelas negativos opcionales no entran en agregaciones; URB no fabrica velocidad; carga no se etiqueta como porcentaje físico.
- IDs estables por fuente/estación/canal/etiqueta/rol; ninguna colisión por mezcla de códigos o formatos.
- Reinicio interrumpido, segunda ejecución, duplicados entre archivos y conflicto real de contenido producen las respuestas esperadas y evidencia.
- Carga completa y reimportación de ambos motores: conteos exactos, BSON Date, referencias, hashes, valores y campos nuevos iguales.
- La misma identidad con payload distinto bloquea la importación y registra el conflicto; probar también contenido cambiado conservando hash antiguo.
- PG01–PG10 adaptadas y agregaciones Mongo por fuente/tipo/unidad, sin convertir canales en sensores físicos ni equiparar ausencia de lecturas con avería.
- Comparación entre motores y contra originales en muestras verificables; tiempo/memoria/espacio y planes registrados. La suite v1 permanece aprobada y la evidencia histórica no se reescribe.

## 8. Aprobaciones solicitadas

1. Adoptar esta corrección como **`madrid-draft-v2`**, sin considerar v1 silenciosamente corregido.
2. Empezar tráfico con **URB/M30**, enero de 2025, etiquetas locales inequívocas, y conservar C30 en cuarentena.
3. Aprobar la migración por regeneración y bases locales nuevas, manteniendo IDs compartidos y sin actualizaciones destructivas.
4. Acordar que integración de dos fuentes no significa sincronización temporal demostrada ni inventario de sensores acreditado.

La restricción original de no implementar queda superada únicamente para la
ruta local autorizada del 27/10. No se suman sus lecturas a los conteos v1 ni se
ejecutan cargas remotas. Los permisos académicos restantes no se presuponen.

## 9. Ruta local implementada

```bash
bash scripts/validate_sprint1.sh --datos
```

Requiere originales privados verificados, el intérprete oficial de tráfico en
`research/datasets/raw/sprint1-v2/traffic_dictionary.pdf`, dependencias del entorno
de investigación y las imágenes locales PostgreSQL/Mongo. No descarga mediciones.

La generación es `expanded-v2-2025-01`, **solo enero**, en un directorio nuevo.
No son 1.733.743 registros ni una ampliación anual cargada. Se excluyen 17.774
C30 y 3.020 flags vacíos de tráfico; las 1.761 filas rechazadas de aire conservan
su motivo. Las variables opcionales negativas pasan a faltantes, URB no recibe
velocidad inventada y `carga` se etiqueta como índice.

Las diez consultas Mongo están comentadas en
`sprint1/basico/consultas_mongodb_v2.js`. MG04 usa intensidad **>2.000 veh/h**
como regla de ejercicio, con `official_rule=false`, versión y severidad demo.
MG05 registra emisiones reales de replay **ahora**, solo en una colección local;
no simula alertas oficiales de 2025 ni envía mensajes externos.

MG08 usa **14.388 accidentes de 2026**, deduplicados desde 33.322 filas de
personas. No exporta edad, sexo, lesiones, dirección ni expediente en claro;
no une esos accidentes a las lecturas de enero de 2025.

Los distritos proceden del inventario disponible y llevan alcance
`current_inventory_not_historically_verified`; no se acredita su vigencia en 2025.
PG07 sigue sin poder acreditar actividad de dispositivos físicos: no se inventan
enlaces entre sensores demo y canales observados.
