# Entrega Sprint 1 — PostgreSQL y MongoDB

**Alcance de la asignación:** «Sección de PostgreSQL y Mongo». Esta entrega es
individual y no depende de Spark, Hadoop, una segunda fuente, alertas, sensores
físicos, ni infraestructura compartida.

## Qué se entrega

| Motor | Implementación demostrable | Archivos principales |
|---|---|---|
| PostgreSQL 16.6 | Esquema relacional, restricciones, índices, consultas, vista, función, replay, cuarentena y respaldo/restauración. | `sprint1/postgres/` |
| MongoDB 7.0.16 | Validador BSON, índices, consultas/agregaciones, replay, cuarentena, CRUD aislado y respaldo/restauración. | `sprint1/mongodb/`, `sprint1/basico/` |

La demostración usa tres ejemplos publicados, uno de aire, uno meteorológico y
uno de tráfico, en copias de prueba. Los datos de prueba no afirman representar
un inventario de sensores físicos.

## Ejecución para revisión

### Requisito

- Python 3.10+, Node.js 18+ y Docker.
- Imágenes locales `postgres:16.6-alpine` y `mongo:7.0.16`.

### Validación rápida

Desde la raíz del repositorio:

```bash
bash scripts/validate_sprint1.sh
```

Resultado esperado: **32 pruebas Python y 8 pruebas Node, sin fallos**. Esta
prueba no inicia servicios ni modifica datos.

### Demostración integrada de ambos motores

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_sprint1_engines.py
```

Resultado esperado:

```text
Sprint 1 disposable engines: PASS
```

El comando crea contenedores efímeros, sin puertos publicados ni conexión de red
entre ellos; al finalizar los elimina. Genera un informe verificable en
`/tmp/opencode/smartcity-s1-integration-*.json`.

La última ejecución local registrada el **26/10/2026** terminó en `PASS`:

- PostgreSQL: DDL, 3 lecturas, consultas, vista, función, replay, cuarentena,
  respaldo/restauración y una prueba de concurrencia de 8 conexiones.
- MongoDB: validador, 6 índices, 3 lecturas, búsquedas, agregaciones, CRUD en
  colección separada, replay, cuarentena y respaldo/restauración.

## Demostración corta en clase

1. Ejecutar la validación rápida.
2. Ejecutar la demostración integrada y mostrar la línea `PASS`.
3. Mostrar en PostgreSQL `sprint1/postgres/schema_proposal.sql`,
   `queries.sql` y `staging.sql`: tablas relacionadas, FK, índices, vista
   `quality_summary` y función `air_statistics`.
4. Mostrar en MongoDB `sprint1/mongodb/validator.js`, `indexes.js` y
   `queries.js`: validación de documentos, índices y agregaciones.
5. Abrir las consultas sencillas y comentadas:
   - `sprint1/basico/consultas_postgres.sql`
   - `sprint1/basico/consultas_mongodb.js`

## Límites declarados

- La prueba integrada valida funcionalidad con una muestra pequeña; no es un
  benchmark de volumen ni una carga en servidores compartidos.
- Canal y estación se tratan como entidades lógicas. No se presentan como
  sensores físicos acreditados.
- Las consultas no inventan datos de alertas, geografía, organizaciones o
  usuarios.
- Los componentes posteriores (Spark/Hadoop, interfaz y una segunda fuente
  aceptada) quedan fuera del alcance indicado para esta asignación.

## Evidencia adicional disponible

El repositorio también conserva evidencia de validaciones locales de volumen con
1.076.813 observaciones reales de aire en ambos motores en
`docs/equipo/CIERRE_VALIDACION_SPRINT1.md`. Es evidencia complementaria, no se
requiere para reproducir la demostración rápida anterior.
