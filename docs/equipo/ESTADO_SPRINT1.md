# Estado del Sprint 1 — 27/10/2026

**Alcance:** PostgreSQL y MongoDB. Spark, Hadoop e interfaz no bloquean este avance.
Instrucciones: [ENTREGA_SPRINT1.md](../../ENTREGA_SPRINT1.md).

## Comprobado

- **PostgreSQL v2: PASS masivo.** 748.889 lecturas (91.959 aire + 656.930
  tráfico), metadatos comparados, replay sin duplicados y diez consultas ejecutadas.
  Contenedor y volúmenes eliminados. Evidencia:
  `research/datasets/results/expanded-v2-2025-01/execution-0652c6cd8bbc.json`.
  PG07 devuelve cero por ausencia de vínculos observados: no acredita actividad física.
- **MongoDB v2 masivo: todavía sin PASS confirmado.** Se corrigió el problema
  asíncrono y pasó la prueba nativa pequeña; no equivale a aprobar el lote completo.

- Suite unificada: 51 pruebas Python y 13 Node aprobadas; diez consultas SQL
  `smartcity` ejecutadas con resultados comprobados y fixtures revertidas.
  El parser anual vuelve a reconocer PG01–PG10. SQL de práctica separado en
  `staging_queries.sql`; PG07 excluye relaciones sensor–canal desconocidas.
- Núcleo complementario `sprint1`: integración local
  PostgreSQL 16.6/MongoDB 7.0.16 con tres ejemplos, replay, cuarentena,
  CRUD, respaldo/restauración y carrera PostgreSQL de ocho conexiones.
- Carga anual `smartcity`: los manifiestos registran 1.076.813 lecturas reales
  de aire por motor. Es evidencia local anterior, no una carga compartida verificada hoy.
- El paquete anual incluye 1 organización, **5.133 usuarios y 5.133 sensores**
  administrativos **sintéticos**, con procedencia. No acreditan inventario físico
  ni se vinculan a lecturas reales. La [autorización registrada](EVIDENCIA_AUTORIZACION_DATOS_SINTETICOS.md)
  permite esos atributos administrativos, no inventar mediciones.
- Preparación v2 local separada: **748.889 lecturas** de enero de 2025,
  91.959 de aire y 656.930 de tráfico. Las cargas nativas se comprueban con
  `scripts/validar_v2.py`; preparación y carga no son el mismo paso.
- Código Mongo v2: diez consultas reales, eventos derivados por regla demo,
  replay de alertas locales y accidentes de 2026 anonimizados (14.388 expedientes,
  deduplicados desde 33.322 filas de personas). No son avisos oficiales históricos.

## Pendientes de entrega

1. Completar la evidencia de las [20 consultas](MATRIZ_CONSULTAS_SPRINT1.md).
   La ruta SQL canónica es `smartcity`; el núcleo `sprint1` queda como práctica
   complementaria. Los manifiestos anuales v1 mantienen sus bloqueos originales;
   la ruta v2 crea resultados nuevos, no cambia esas banderas históricas.
   Faltan aceptación del alcance canal/sensor, zonas de inventario y reglas demo.
2. Confirmar las cargas y comparaciones de las dos fuentes en los informes v2.
   El lote anual v1 sigue admitiendo solo aire; no sumar ambos paquetes.
   Meteorología conserva bloqueos de reloj. PG07 sigue sin relación física observada.
3. Probar los cargadores Python con autenticación real y cerrar el informe/diagramas.
   La CI ya invoca la suite offline unificada; su ejecución remota falta hasta publicar.
4. Si la entrega usa bases compartidas, comprobar acceso, carga y respaldo por separado.
   Las pruebas desechables no acreditan su estado.

## Antecedentes que no bloquean desarrollar

La [recuperación histórica](RECUPERACION_INSUMOS_HISTORICOS.md) conserva un
checkpoint de 83/85 pruebas y 15 artefactos pendientes. No se reejecutó hoy ni
se convierte en PASS con las pruebas nuevas. Enero y las muestras ya están
contenidos en sus generaciones: no sumarlos al volumen anual.
