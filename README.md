# SmartCity Analytics

Proyecto académico de Bases de Datos — II Semestre 2026.

## Leer solo esto para trabajar

1. [Sprint 1: alcance y ejecución](ENTREGA_SPRINT1.md).
2. [Estado y pendientes](docs/equipo/ESTADO_SPRINT1.md).
3. [Las 20 consultas y su evidencia](docs/equipo/MATRIZ_CONSULTAS_SPRINT1.md).

Para redactar la entrega: [informe en LaTeX](docs/avance_1/main.tex), con
[instrucciones para Overleaf y compilación local](docs/README.md#informe-del-avance-en-latex).

**Primer avance, 28 de octubre:** PostgreSQL y MongoDB, modelos, datos,
10 consultas por motor y documentación. Hadoop, Spark e interfaz quedan para
la entrega final del 25 de noviembre. Referencia: `Plan_de_trabajo.pdf` del equipo.

## Dos implementaciones distintas

- **Carga anual:** esquema `smartcity`, contrato `madrid-draft-v1`.
  Evidencia local de 1.076.813 lecturas reales de aire por motor.
- **Demostración local:** código en `sprint1/`, esquema `sprint1`, contrato
  `madrid-draft-v1-frozen`. Prueba tres ejemplos; no acredita el volumen anual
  ni las 20 consultas completas.

No mezclar sus esquemas, identificadores o resultados. La segunda fuente aceptada
y varias consultas siguen pendientes. No se ha comprobado aquí el servidor compartido.

## Comprobar el código

Con Python 3.10+ y Node.js 18+, desde la raíz:

```bash
bash scripts/validate_sprint1.sh
```

La demostración con Docker y la validación documental están en
[ENTREGA_SPRINT1.md](ENTREGA_SPRINT1.md).

## Carpetas

- `sprint1/`: código local y consultas de práctica; `tests/`: sus pruebas.
- `research/datasets/scripts/`: ETL y validación de la carga anual e investigación.
- `research/datasets/results/`: evidencia de ejecuciones anteriores, no datos actuales del servidor.
- `docs/`: [documentación técnica y archivo histórico](docs/README.md).
- `compose.yaml`: infraestructura local; no instala automáticamente el esquema del dataset.

No subir credenciales, `.env`, claves, dumps ni datos privados. El acceso al servidor
se coordina con el administrador. No aplicar cargas o migraciones compartidas sin autorización.
