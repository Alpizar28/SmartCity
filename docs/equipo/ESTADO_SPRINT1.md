# Estado del Sprint 1 — 27/10/2026

**Alcance:** PostgreSQL y MongoDB. Spark, Hadoop e interfaz no bloquean este avance.
Instrucciones: [ENTREGA_SPRINT1.md](../../ENTREGA_SPRINT1.md).

## Comprobado

- Núcleo `sprint1`: 32 pruebas Python y 8 Node aprobadas; integración local
  PostgreSQL 16.6/MongoDB 7.0.16 con tres ejemplos, replay, cuarentena,
  CRUD, respaldo/restauración y carrera PostgreSQL de ocho conexiones.
- Carga anual `smartcity`: los manifiestos registran 1.076.813 lecturas reales
  de aire por motor. Es evidencia local anterior, no una carga compartida verificada hoy.
- El paquete anual incluye 1 organización, **5.133 usuarios y 5.133 sensores**
  administrativos **sintéticos**, con procedencia. No acreditan inventario físico
  ni se vinculan a lecturas reales. La [autorización registrada](EVIDENCIA_AUTORIZACION_DATOS_SINTETICOS.md)
  permite esos atributos administrativos, no inventar mediciones.

## Pendientes de entrega

1. Elegir una ruta de entrega coherente: el esquema anual `smartcity` y el núcleo
   `sprint1` tienen contratos e identidades diferentes.
2. Separar los archivos de consultas: `sprint1/postgres/queries.sql` fue reemplazado
   por el núcleo local y rompe el parser del validador anual `validate_real_postgres.py`.
3. Completar y ejecutar las [20 consultas](MATRIZ_CONSULTAS_SPRINT1.md).
   Los manifiestos anuales mantienen PG07 y MG04/05/08 bloqueadas; otras consultas
   necesitan aclarar alcance por canal/sensor y zona. Las banderas declarativas
   del harness anual Mongo no sustituyen resultados de cada pipeline.
4. Resolver la segunda fuente aceptada: el lote anual solo admite aire.
   Tráfico v2 requiere aprobación y pruebas; meteorología conserva bloqueos de reloj.
5. Probar los cargadores Python con autenticación real, incorporar la suite nueva
   al CI y cerrar el informe/diagramas de la implementación elegida.
6. Si la entrega usa bases compartidas, comprobar acceso, carga y respaldo por separado.
   Las pruebas desechables no acreditan su estado.

## Antecedentes que no bloquean desarrollar

La [recuperación histórica](RECUPERACION_INSUMOS_HISTORICOS.md) conserva un
checkpoint de 83/85 pruebas y 15 artefactos pendientes. No se reejecutó hoy ni
se convierte en PASS con las pruebas nuevas. Enero y las muestras ya están
contenidos en sus generaciones: no sumarlos al volumen anual.
