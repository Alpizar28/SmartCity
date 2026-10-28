# Evidencia acotada del cierre PostgreSQL

Son ejecuciones nuevas de esta revisión, no nuevos manifiestos oficiales de JP.
No contienen JSONL originales, bases, credenciales ni filas personales.

* `cierre_auditoria_v2.json`: hashes/QA/identidades del ZIP v2 completo y cotejo
  independiente de las cantidades/muestras del PASS masivo PostgreSQL previo.
* `cierre_pg07_controlado.json`: SQL canónico exacto, fixtures sintéticas con
  ROLLBACK y nueve escenarios ampliados de PG07. No prueba actividad física.
* `cierre_subconjunto_v2.json`: SQL v2 en 2.907 lecturas reales seleccionadas y
  administración sintética; incluye agregados, ventanas, restricciones y planes.
  No es una carga del lote completo. Sus pruebas de limitaciones DDL no son
  aceptación académica de tales defectos.

`status=PASS` solo se interpreta junto con scope, source_hashes, selección y
limpieza. La suite offline coteja los hashes contra el código actual: cambios
posteriores requieren otra ejecución, nunca retocar los hashes guardados.

El PASS masivo original sigue intacto en
`research/datasets/results/expanded-v2-2025-01/execution-0652c6cd8bbc.json`;
los dos FAIL históricos tampoco se alteraron. Los intentos fallidos durante
desarrollo y las ejecuciones previas permanecen en `/tmp/opencode` y se resumen
en la entrega; no se los presenta como PASS.

Interpretación y comandos: [entrega técnica](../evidencia_final_postgresql.md),
[reproducción](../reproduccion_cierre.md), [3FN](../normalizacion_3fn.md),
[PG07](../pg07_limite_evidencia.md).
