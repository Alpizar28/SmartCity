# Datos locales

## Qué usar

- Muestra pública de 200 lecturas: [muestra_v2.csv](../docs/datasets/muestra_v2.csv).
- Paquete completo privado: `releases/SmartCity_DATASET_COMPLETO_PRIVADO.zip`.
- Checksum del paquete: el archivo `.zip.sha256` junto al ZIP.
- Inventario del paquete: `releases/DATASET_COMPLETO_manifest.json`.
- Instrucciones de restauración y privacidad:
  `releases/DATASET_COMPLETO_LEER_PRIMERO.md`.
- Resumen de la generación v2: `releases/dataset_resumen.json`.

Los archivos de `releases/` son locales e ignorados por Git. El ZIP contiene
originales con información sensible: no subirlo a GitHub ni compartirlo con
acceso público. GitHub no sirve de respaldo de estos datos privados.

Los cargadores leen los datos preparados desde
`research/datasets/private_results/expanded-v2-2025-01/`, no desde el ZIP.
Las instrucciones completas están en [ENTREGA_SPRINT1.md](../ENTREGA_SPRINT1.md).

## Limpieza

Se retiró de `releases/` una copia idéntica de la muestra pública. El empaquetador
puede volver a generarla; no es el dataset completo. Los manifiestos antiguos se
conservaron en `research/datasets/private_results/respaldo_releases_historicos/`:
no están en GitHub y no se eliminaron. El paquete actual no fue modificado.
