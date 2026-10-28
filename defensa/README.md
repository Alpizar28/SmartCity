# Código para la defensa

Esta carpeta reúne accesos directos al código vigente. No son copias: al abrirlos
se consulta el archivo original del repositorio. En GitHub también se puede usar
los enlaces de esta guía. Para compartir un ZIP independiente, incluir los
archivos originales; no enviar solamente los accesos directos.

## 1. PostgreSQL

- [Modelo SQL](../sprint1/postgres/schema_v2_3nf.sql): catorce tablas, claves,
  restricciones, índices, triggers, vistas y función.
- [Diez consultas](../sprint1/postgres/queries_v2_3nf.sql): PG01–PG10 y SQL adicional.
- [Diagrama](../docs/arquitectura/diagrama_3nf.md): atributos y cardinalidades.

Explicar primero fuente → estación → canal → observación. Luego mostrar tipos,
sensores y la asignación opcional sensor–canal. El modelo está normalizado según
las dependencias declaradas; JSONB se trata como dominio indivisible.

## 2. MongoDB

- [Carga](../sprint1/basico/cargar_mongodb_v2.js): lotes, validadores, índices,
  eventos derivados y alertas locales.
- [Diez consultas](../sprint1/basico/consultas_mongodb_v2.js): MG01–MG10.
- [CRUD paso a paso](../sprint1/basico/crud_mongodb.js): colección de práctica,
  separada de las lecturas reales.
- [Laboratorio](../sprint1/mongodb/academico/README.md): demostraciones sintéticas
  por sensor, tipo de dispositivo y texto libre; código completo en `laboratorio/`.

Explicar documento, filtro, proyección, orden y las etapas `$match`, `$group` y
`$sort`. La carga masiva y el laboratorio son demostraciones distintas.

## 3. Informe y resultados

- [PDF compilado](../docs/avance_1/SmartCity_Sprint1_PaqueteA_Editorial_20261028T163407.pdf).
- [Fuente LaTeX](../docs/avance_1/main.tex): tiene ampliaciones posteriores al PDF;
  requiere recompilación para incluirlas.
- [Resultados PostgreSQL](../sprint1/postgres/cierre_3nf.md).
- [Resultados MongoDB](../sprint1/mongodb/evidencia_final_mongodb.md).

## Límites que debemos explicar

- Hay evidencia de 748.889 lecturas por motor; no sumar generaciones ni replay.
- Los sensores administrativos son sintéticos; no acreditan dispositivos físicos.
- PG07 está probada funcionalmente, sin asignaciones físicas observadas en el lote.
- Eventos y alertas son una regla demo y replay local, no avisos oficiales.
- Los accidentes son de 2026; aire y tráfico corresponden a enero de 2025.
- No se demostró almacenamiento distribuido MongoDB.

## Antes de ejecutar

Esta carpeta es un recorrido de lectura, no un instalador. No ejecutar el DDL en
una base poblada ni el cargador de forma aislada: requieren el entorno y los datos
descritos en [las instrucciones de entrega](../ENTREGA_SPRINT1.md).
Los archivos históricos, datasets y evidencias se conservan fuera de esta carpeta.
