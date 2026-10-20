# CI y reproducción local

## CI pública

`.github/workflows/validate.yml` se ejecuta en push y pull request. Solo valida material que existe en un clon limpio:

- validación documental Fase 6;
- pruebas deterministas de contrato, evidencia, documentación y seed administrativo;
- sintaxis de `unified_full_mongo.js`;
- espacios y marcadores de conflicto.

La CI no recibe secretos, `private_results/`, JSONL, SQLite, ZIPs, volúmenes Docker ni socket Docker. Ejecuta `./scripts/validate_repo.sh` en modo público, que usa únicamente las pruebas públicas deterministas de contrato, documentación, evidencia y seed administrativo. Por tanto, una ejecución verde de GitHub Actions no equivale a una carga completa del dataset.

## Validación pública local

```bash
./scripts/validate_repo.sh
```

## Reproducción privada local

Quien tenga el paquete autorizado debe extraerlo sin añadirlo a Git en:

```text
research/datasets/private_results/expanded-2025/
```

Luego, desde la raíz, con `.venv` preparado y las imágenes Docker locales:

```bash
FULL_DATASET_VALIDATION=1 ./scripts/validate_repo.sh
.venv/bin/python research/datasets/scripts/unified_full_load.py --generation expanded-2025 --engine postgresql
.venv/bin/python research/datasets/scripts/unified_full_load.py --generation expanded-2025 --engine mongodb
.venv/bin/python research/datasets/scripts/unified_full_verify.py --generation expanded-2025
```

El último comando debe devolver `verified: true`, 1.076.813 mediciones reales y cero enlaces de lecturas/canales a sensores sintéticos. Los cargadores crean únicamente contenedores locales desechables sin red ni puertos publicados y luego los eliminan.

No compartir ni versionar `.env`, credenciales, el lote privado, dumps o volúmenes. Verificar los hashes publicados en los manifiestos antes de importar.
