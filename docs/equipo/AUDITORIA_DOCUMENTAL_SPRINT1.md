# Auditoría interna de cierre documental — Sprint 1

Fecha: 28/10/2026. Rama: `fix/sprint1-postgresql-3nf`.
Base Git: `804d6a551dc84e22d901b64554c30a712b951f77`.

## Dictamen y alcance

Las correcciones documentales y de presentación están completadas. El
[PDF vigente](../avance_1/SmartCity_Sprint1_3NF_20261028T080911.pdf) tiene 14 páginas
y fue revisado visualmente en su totalidad. Este cierre no constituye la auditoría
académica general del Sprint 1 ni una nueva ejecución de PostgreSQL o MongoDB.

El [manifiesto de esta revisión](../../sprint1/postgres/evidencias/3nf/MANIFIESTO_CIERRE_DOCUMENTAL_20261028T080911.json)
identifica el PDF, las fuentes y las verificaciones. Su archivo `.sha256` permite
comprobarlo. El PDF anterior y `MANIFIESTO_ENTREGA_3NF.json` se conservan como
snapshot histórico; sus huellas documentales no describen las fuentes corregidas.

No se modificaron DDL, consultas, contratos, cargadores, validadores nativos,
fixtures SQL, registros históricos ni bases de datos. La única prueba de código
modificada es la comprobación offline de argumentos del validador: inspecciona el
AST y exige que la única opción configurable sea `--sample`, sin direcciones internas.

## Normalización técnicamente verificada

Las 14 tablas, 83 columnas y 17 FK corresponden al modelo normalizado. La prueba
de 3FN calcula cierres exhaustivos sobre las DF declaradas y deriva claves
candidatas; la evidencia nativa coteja los atributos con el catálogo real.
JSONB se considera un dominio SQL tipado indivisible, los opcionales NULL no se
utilizan como claves y no se infieren DF de coincidencias del lote. La conclusión
no es una demostración recursiva sobre las propiedades JSON ni una acreditación
del inventario físico. La reconstrucción contractual de 748.889 lecturas
complementa la prueba formal sin sustituir sus supuestos.

## Versiones de las evidencias PostgreSQL

| Informe en `sprint1/postgres/evidencias/3nf/` | Resultado registrado | Correspondencia con el validador |
|---|---|---|
| `20261028T071042-3f9f038f.json` | FAIL al iniciar el socket local | Versión anterior; prefijo SHA-256 `e36c589ed9e3` |
| `20261028T071112-8aeb341f.json` | PASS de 1.000 lecturas | Misma versión anterior; prefijo `e36c589ed9e3` |
| `20261028T071356-04a8cc67.json` | PASS de 1.000 lecturas | Versión intermedia; prefijo `0cc8442677af` |
| `20261028T071812-55791345.json` | PASS de 748.889 lecturas | Validador actual; prefijo `217ee35b632a` |

Las huellas completas figuran en `source_hashes` de cada informe. La huella del
validador actual es
`217ee35b632acbdb1df6e20f72190b55d11b854d2342cbbbe277a5bd3eee6da1`.
Los ocho archivos registrados por el informe masivo coinciden con sus versiones
actuales, incluida la fixture SQL. La evidencia de SQL avanzado
`advanced-20261028T073507-abef9831.json` coincide con sus tres archivos de código
registrados. Las muestras y el FAIL conservan sus bytes y checksums originales;
no se presentan como ejecución del script actual.

## Alcance efectivo de las ocho pruebas negativas

El ejecutor usa `EXCEPTION WHEN OTHERS` y solo registra `rejected`. No conserva
SQLSTATE, nombre de restricción ni mensaje de cada excepción. La clasificación
siguiente resulta de leer el DDL y las operaciones; no es una traza nueva del motor.

| Caso | Recorrido esperado según el código | Cobertura acreditada por el registro |
|---|---|---|
| `channel_source` | Trigger `check_channel`: fuentes distintas | Rechazo de operación dirigida a integridad entre fuentes; no aislamiento de FK |
| `sensor_station` | Trigger `check_channel_sensor`: estaciones distintas | Rechazo de asignación incompatible; no aislamiento de FK |
| `parent_source_update` | Trigger de identidad inmutable en estaciones | Rechazo de modificación del catálogo |
| `payload_conflict` | Trigger `check_observation`: observación inmutable | Rechazo del cambio de valor |
| `raw_locator_sha` | Inmutabilidad antes del CHECK de `raw_locator` | Rechazo de UPDATE; no prueba aislada del CHECK |
| `observation_version` | Inmutabilidad antes de consultar la nueva versión o comprobar su FK | Rechazo de UPDATE; no prueba aislada de FK |
| `zone_parent` | Trigger `check_zone_parent`: padre ausente | Rechazo del padre inválido; no prueba aislada de la FK autorreferencial |
| `duplicate_natural` | Inserción dirigida a UNIQUE de canal/UTC | Rechazo del duplicado propuesto; causa exacta no registrada |

**Ningún caso aísla específicamente un CHECK o una FK.** La prueba de duplicado
está diseñada para alcanzar UNIQUE, pero el registro genérico no certifica la
restricción responsable. Las 22 CHECK y 17 FK constan en el catálogo; no se afirma
haber probado negativamente cada una. Las pruebas positivas de jerarquía y
asignación, y los casos controlados de PG07, conservan su alcance con rollback.

## Limitaciones para la auditoría académica general

| Aspecto | Estado de la evidencia |
|---|---|
| Dispositivos físicos y canales | No hay asignaciones observadas sensor–canal. PG07 no permite inferir inactividad física. MG01 usa canal lógico y MG07 tipo de medición |
| Administración sintética | Sensores, tipos, categorías, usuarios, fechas, estados y organismo demo están identificados; no acreditan inventario u operadores municipales reales |
| Períodos y geografía | Lecturas v2 de enero de 2025, incidentes de 2026 y distritos del inventario disponible se mantienen separados. No se acredita vigencia histórica individual ni causalidad entre períodos |
| Eventos y alertas | Regla académica y replay local; no alertas oficiales retrospectivas ni notificaciones externas |
| Información dinámica MongoDB | Cobertura parcial: objetos anidados y atributos opcionales. No hay demostración suficiente para declarar completo ese requisito académico |
| Restricciones declarativas | No hay aislamiento negativo individual de CHECK/FK en los ocho casos examinados; tampoco una batería negativa MongoDB completa |
| Producción y entorno compartido | Las pruebas locales no acreditan carga compartida, autenticación real, alta disponibilidad o restauración remota |
| Aspectos transversales | El alcance de materializadas, particionamiento y componente distribuido para octubre no está confirmado. Los componentes de noviembre permanecen fuera de este cierre |
| Antecedentes v1 | Las banderas constantes de `query_evidence` no acreditan por sí solas la ejecución de los pipelines; la evidencia v2 se verifica por separado |

No existe evidencia de aceptación académica global de esas adaptaciones. Se
mantienen expresadas como límites del informe; los faltantes se registran aquí
sin transformarlos en resultados aprobados.

## Archivos modificados en esta revisión

1. `docs/README.md`: tratamiento de PDF y manifiestos en Git; enlaces a la revisión vigente.
2. `docs/avance_1/main.tex`: identificación institucional, resumen e índice en página propia.
3. `docs/avance_1/secciones/01-alcance-datos.tex`: redacción académica y distinción explícita de v1/v2.
4. `docs/avance_1/secciones/02-modelos.tex`: cobertura de pruebas, límites documentales y recorridos de flechas sin atravesar etiquetas.
5. `docs/avance_1/secciones/03-consultas.tex`: identificación de antecedentes anuales y evidencia v2.
6. `docs/avance_1/secciones/04-validacion.tex`: clasificación de rechazos y versiones de las evidencias; eliminación de detalles innecesarios de compilación.
7. `docs/avance_1/secciones/05-cierre.tex`: cobertura parcial MongoDB y aceptación semántica no acreditada.
8. `docs/avance_1/secciones/06-equivalencias.tex`: macro corregida y tabla completa en una página.
9. `docs/equipo/ALCANCE_CONFIRMADO_SPRINT1.md`: 3FN técnicamente completada con sus supuestos y límites.
10. `docs/equipo/CHECKLIST_CIERRE_SPRINT1.md`: estado de integración documental.
11. `docs/equipo/ESTADO_SPRINT1.md`: separación de cierre técnico y auditoría académica general.
12. `sprint1/postgres/cierre_3nf.md`: identificación histórica de muestras y límites de las pruebas negativas.
13. `tests/sprint1/test_modelo_3nf.py`: comprobación equivalente de opciones CLI sin IP privada literal.

Se añaden este informe interno, el nuevo PDF y el nuevo manifiesto JSON con su
checksum. No se reemplazan el PDF ni los manifiestos anteriores.

## Validación del cierre documental

- Suite offline: 65 pruebas Python y dos archivos Node aprobados; incluye los
  seis casos de `test_modelo_3nf.py` y la comprobación estática LaTeX.
- Pruebas documentales: seis casos de `research/datasets/tests/test_phase6_docs.py`
  aprobados, sin generar caché dentro del repositorio.
- PDF: 14 páginas revisadas visualmente; índice estable, tabla de 17 atributos
  completa, diagrama legible y referencias resueltas. La extracción no presenta
  comandos LaTeX literales, marcadores editoriales ni `??`.
- Compilación final: salida 0, auxiliares estables entre las dos últimas pasadas,
  sin cajas desbordadas ni errores de maquetación. Solo permanece el aviso no
  fatal de `epstopdf` por shell escape deshabilitado; no afecta a las figuras TikZ.
- Integridad: informes PostgreSQL y sus checksums históricos intactos; 29
  archivos sellados MongoDB y 19 archivos de código oficial verificados.
- DDL, consultas, contratos y evidencia nativa conservan sus hashes de entrada a
  esta revisión. No se ejecutaron motores ni se modificaron bases de datos.
- No se realizaron commit, push ni merge; el índice de Git permanece vacío.
