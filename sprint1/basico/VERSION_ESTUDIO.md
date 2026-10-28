# Muestra de un estilo más sencillo

Comparar `consultas_mongodb_v2.js` (oficial) con
`consultas_mongodb_estudio.js` (propuesta para estudiar).

La propuesta separa las diez consultas en funciones con nombres descriptivos,
usa un formato uniforme y mantiene los comentarios sobre las decisiones de datos.
Es más larga, pero permite leer y explicar una consulta a la vez.

Por ejemplo, `promedioPorZona` tiene tres pasos:

1. `$match` excluye las lecturas sin zona.
2. `$group` calcula cantidad y promedio por zona, fuente, magnitud y unidad.
3. `$sort` ordena los grupos para presentar el resultado.

Se conservan los nombres del dataset, las fechas, los filtros y las salidas.
También se conserva `await`: es necesario para las operaciones asíncronas del
módulo en mongosh. No se añadieron errores ni se eliminaron validaciones para
simular un nivel de experiencia.

## Comparar el comportamiento sin conectar a MongoDB

```bash
node --test tests/sprint1/test_mongodb.js
```

La prueba compara los resultados y la secuencia completa de llamadas a una base
simulada: filtros, proyecciones, orden, límite y etapas de agregación. Incluye
operaciones síncronas y asíncronas, y el rechazo cuando falta tráfico.
No sustituye una prueba sobre un motor real.

Esta muestra no está conectada al cargador; sus pruebas forman parte de la suite principal. El código
oficial y sus evidencias no se modificaron. Adoptarla requiere actualizar los
imports, integrar sus pruebas y volver a validar el código nuevo; no cambiar
los hashes de reportes antiguos para hacerlos pasar por ejecuciones nuevas.
