# Estado del Sprint 1 — 27/10/2026

**Alcance:** PostgreSQL y MongoDB. Spark, Hadoop e interfaz no bloquean este avance.
Instrucciones: [ENTREGA_SPRINT1.md](../../ENTREGA_SPRINT1.md).

## Comprobado

- Suite unificada: 38 pruebas Python y 8 Node aprobadas; diez consultas SQL
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

## Pendientes de entrega

1. Completar la evidencia de las [20 consultas](MATRIZ_CONSULTAS_SPRINT1.md).
   La ruta SQL canónica es `smartcity`; el núcleo `sprint1` queda como práctica
   complementaria. Los manifiestos anuales mantienen PG07 y MG04/05/08 bloqueadas; otras consultas
   necesitan aclarar alcance por canal/sensor y zona. Las banderas declarativas
   del harness anual Mongo no sustituyen resultados de cada pipeline.
2. Resolver la segunda fuente aceptada: el lote anual solo admite aire.
   Tráfico v2 requiere aprobación y pruebas; meteorología conserva bloqueos de reloj.
3. Probar los cargadores Python con autenticación real y cerrar el informe/diagramas.
   La CI ya invoca la suite offline unificada; su ejecución remota falta hasta publicar.
4. Si la entrega usa bases compartidas, comprobar acceso, carga y respaldo por separado.
   Las pruebas desechables no acreditan su estado.

## Antecedentes que no bloquean desarrollar

La [recuperación histórica](RECUPERACION_INSUMOS_HISTORICOS.md) conserva un
checkpoint de 83/85 pruebas y 15 artefactos pendientes. No se reejecutó hoy ni
se convierte en PASS con las pruebas nuevas. Enero y las muestras ya están
contenidos en sus generaciones: no sumarlos al volumen anual.
