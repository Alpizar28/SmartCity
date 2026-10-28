# Evidencias actuales de MongoDB v2

Ejecución nativa: `execution-20261028T055755-3fea400d`, `main` 804d6a5.
Entrada al cierre: [RESUMEN_FERNANDA.md](RESUMEN_FERNANDA.md).

`originales/` conserva los 18 archivos verificados y su manifiesto original.
Los `.log` se renombraron a `.txt` **sin cambiar bytes**, para que las evidencias
revisadas no queden ocultas por las reglas generales de logs. La correspondencia
exacta y sus hashes están en `MANIFIESTO_ORIGEN.json`. El manifiesto original
conserva los nombres previos, por eso no debe ejecutarse directamente sobre los
nombres nuevos; para toda esta carpeta usar el manifiesto exterior:

```bash
sha256sum --check SHA256SUMS
```

Desde la raíz del repositorio, el inventario de código oficial se verifica con:

```bash
sha256sum --check sprint1/mongodb/evidencias/20261028T055755-3fea400d/CODIGO_OFICIAL_SHA256SUMS.txt
```

`verificacion_independiente.json` registra el recálculo de las diez consultas
desde los datos privados, sin nuevas cargas. `comprobacion_cierre.json` consolida
el cotejo actual. `auxiliares/` contiene recolectores externos para trazabilidad;
no son cambios del código oficial.

No contiene ZIP, JSONL completos, catálogos privados, SQLite, dumps, entornos,
credenciales ni registros personales. Sí contiene agregados, metadatos técnicos
y muestras acotadas de lecturas públicas necesarias para documentar consultas y
CRUD. Se revisaron los archivos con búsqueda de patrones de secretos.

La reconciliación actual cita una referencia PostgreSQL anterior por hash;
no constituye una nueva ejecución PostgreSQL. Los FAIL previos del repositorio
se conservaron y no sustituyen el PASS MongoDB de esta carpeta.
