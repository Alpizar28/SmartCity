# Scripts necesarios

## Validación habitual

- `validate_sprint1.sh`: pruebas offline; `--engines` añade motores desechables y
  `--datos` reproduce la ruta v2 histórica, no el modelo PostgreSQL normalizado.
- `validate_repo.sh`: validación documental y pruebas públicas que usa la CI.
- `validar_postgresql_3nf.py`: carga y prueba el modelo normalizado vigente.
- `validar_mongodb_academico.py`: laboratorio sintético de sensor, tipo y texto.

## Datos y reproducción

- `validar_v2.py`: carga y compara la generación v2 en motores desechables.
- `verificar_v2.py`: verifica los reportes de ambos motores sin repetir la carga.
- `empaquetar_dataset.py`: genera el paquete privado para compartir con el equipo.

## Dependencias de las pruebas

- `auditar_cierre_postgresql.py`: auditoría y funciones usadas por el validador 3FN.
- `test_sprint1_sql.py`: consultas SQL históricas con fixtures controladas.
- `test_sprint1_engines.py`: integración del núcleo de práctica SQL/Mongo.
- `test_mongo_v2_sample.py`: control nativo pequeño previo a la carga masiva.
- `probar_cierre_postgresql.py`: ejecutor histórico conservado porque las pruebas
  comprueban su hash contra la evidencia de cierre anterior.

No ejecutar todos los scripts indiscriminadamente: los validadores de motores
necesitan sus dependencias y los datos privados. Consultar `ENTREGA_SPRINT1.md`
en la raíz antes de cargar. El capturador retirado de SQL avanzado sigue disponible
en el historial de GitHub; no se modificaron sus reportes.
