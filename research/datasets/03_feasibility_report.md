# Fase 3 — Validación académica y viabilidad técnica

**Fase 3 terminada: tres alternativas evaluadas, sin ganador y sin Fase 4.** Se revisaron el enunciado original, fases 0/1/2, veinte consultas Sprint 1 por alternativa, diez productos Spark, cinco entidades y los 21 KPIs del dashboard.

## Cobertura de consultas

| Alternativa | PostgreSQL estricto verificado | SQL funcional condicionado a canales lógicos | MongoDB nativo ejecutado | MongoDB datos/diseño factible |
|---|---|---|---|---|
| Madrid | 2/10;6 parciales,2 no cumplidas | 6/10 | 0/10 | 8/10 |
| NYC | 2/10;6 parciales,2 no cumplidas | 6/10, alcanceEPA | 0/10 | 7/10 +incidentes parcial |
| Londres | 2/10;6 parciales,2 no cumplidas | 6/10, alcanceLAQN | 0/10 | 7/10 |

Las dos verificadas estrictas son vistas y función SQL. Cuatro más funcionan sobre canales/sitios, pero no prueban dispositivos físicos completos. Estado/instalación no disponibles; organismo incompleto y actividad necesitan inventarios independientes. Se ejecutaron 30 diseñosSQL, no 30 cumplimientos académicos. Python no sustituye MongoDB nativo.

## Volúmenes

| Alternativa | ≥100 k PostgreSQL | ≥500 k MongoDB | ≥1 M Spark |
|---|---|---|---|
| Madrid | CUMPLE_VERIFICADO:993374 hechos cargados con PK/FK | FACTIBLE_NO_EJECUTADO:observaciones locales suficientes, sin duplicar atributos | FACTIBLE_NO_EJECUTADO:ampliar CSV aire local completo; muestra 993374<1 M |
| NYC | CUMPLE_VERIFICADO:112070 hechos no ambiguos | PARCIAL:236200 hechos/solicitudes locales;531503 IDs 311 en API previa requieren descarga/carga y aceptación semántica | PARCIAL:1,875 MrawDOT globales no son 1 Múnicos/QA verificados; local insuficiente |
| Londres | CUMPLE_VERIFICADO:354637 hechos cargados | FACTIBLE_NO_EJECUTADO:3997252 claves energéticas únicas locales | FACTIBLE_NO_EJECUTADO:histórico real>1 M, ejecución distribuida pendiente |

Maestros pequeños no se inflan a 100 k. Intervalo multivariable se conserva en un documento, no varios por atributo. No sumar raw y normalizado como mediciones nuevas. No se generaron mediciones sintéticas ni se modificaron originales.

## Hallazgos contrastados

- Madrid:13.351.700 filas principales raw, de granularidades distintas. Integración 19.087/33.821NO₂elegibles=56,435351%;14.722 sin co-localización y 12 sin temperatura válida. Unidades aire confirmadas; meteo provisional. Altas/bajas históricas son de sitios, no instalación individual.
- NYC:247.526 filas locales. Conflictos DOT:4.767 grupos/9.534 filas en campañas 36401 y 36828; persisten con todos los descriptores disponibles. DOT–EPA 146/322 gruposborough/día=45,34%; DOT–31111/322=3,42%por muestra de 16 fechas. Ninguna clave física correcta acreditada; no sumar conflictos arbitrariamente.
- Londres:4.007.440 filas raw,3.997.252 claves energéticas únicas locales y cero conflictos de valor globales. 100%de 1488 timestamps agregados coincide sin desplazar reloj, no 100%de geografía/sincronización. Geografía fina de hogares 0%; reloj de julio y licencia LAQN pendientes.

## Datos reales frente a sintéticos

Instalación/estado individual, usuarios, concentraciónCO₂ y emisiones históricas de alertas no están completos. Eventos críticos futuros serían **derived** con política específica, no incidentes observados. Solicitudes 311 son registros reales, no accidentes confirmados; CO₂e anual no concentraciónCO₂.

No existe síntesis inevitable: buscar fuente, conservarNULL, solicitar aceptación de derivado/alcance o declarar incumplimiento. Única propuesta synthetic opcional: hasta cuatro cuentas de prueba, namespace demo y correos@example.invalid, no generadas. Alternativa preferible: registrar miembros reales del equipo con consentimiento. No se proponen fechas ficticias sobre estaciones reales ni geografía inventada de hogares.

## Pruebas y viabilidad

42 pruebas aprobadas (22 heredadas +20 nuevas), sin fallos/errores/omisiones. SQL local aislado cargó hechos, validóPK/FK/nulos, CTE/ranking, vista/función y agregados contra Python; contenedor y volumen anónimo eliminados. MongoDB/Hadoop/Spark/dashboard no implementados ni remotos consultados. Comandos, logs ySHA en `03_tests_report.md` y `results/phase3/`.

**Las tres son técnicamente viables para subconjuntos, condicionadas para el proyecto completo. Ninguna cubre todos los atributos/KPIs estrictos actuales.** Madrid requiere unidades/inventarios y energía horaria/CO₂/alertas/recorridos; NYC exige claves DOT, exposición, ampliación de volumen y fuentes de velocidad/energía; Londres bloquea energía por zona fina y requiere timezone/permisos/complementos de movilidad e incidentes.

## Decisiones específicas para Fase 4

1. Acordar con docente canal/sitio frente a dispositivo físico, instalaciónNULL y estado administrativo desconocido; no aprobar sustitutos silenciosos.
2. Acordar eventos críticos derivados y semántica de solicitudes 311; conseguir fuentes deCO₂/alertas/energía horaria/recorridos si los mínimos siguen estrictos.
3. Madrid: cerrar diccionario meteo, inventarios por época/distritos y validez de intensidad/vmed/duración antes de KPIs de movilidad.
4. NYC: pedir identidad de contador/carril para dos campañas o aprobar cuarentena; confirmarCRS y ampliar cardinalidad/QA antes de prometer 500 klecturas/1 MSpark.
5. Londres: obtener geografía energética real o aprobar alcance de cohorte-ciudad; confirmar GMT/BST y permiso LAQN antes de dashboard público/exportaciones.
6. Ejecutar MongoDB nativo cuando exista entorno aislado, incluyendo CRUD/BSON/pipelines/índices. Comparar años/paneles estables y ejecutar Spark≥1 M en fase posterior autorizada.
7. Considerar costo de complementos, permisos y requisitos bloqueantes, sin asignar puntuación final ni escoger ganador aquí.

## Entregables y parada

Ocho archivos requeridos `03_*`: matrices PostgreSQL/MongoDB, gaps de integración, origenCSV, futuroSpark, coberturaDashboard, informe de viabilidad y pruebas. Matriz adicional `03_compliance_matrix.csv`, scripts `phase3_*.py`/`.js`, `test_phase3.py`, JUnit/logs/manifiestos. Reproducción completa: `.venv/bin/python scripts/phase3_run.py` desde `research/datasets/`.

**Sin commit/push/merge, cambios Coolify/Tailscale ni cargas de producción. Fase 4 no iniciada.**
