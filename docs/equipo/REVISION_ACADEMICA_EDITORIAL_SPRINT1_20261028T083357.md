# Revisión académica y editorial del Sprint 1

Fecha: 28/10/2026. Rama: `fix/sprint1-postgresql-3nf`.
Referencia del repositorio: `3c12f8ee5602b6b822036cddc404420df982e569`.

## Resultado y alcance

La revisión editorial está completada para la documentación vigente, el informe
y sus referencias técnicas. El [PDF revisado](../avance_1/SmartCity_Sprint1_3NF_20261028T083357.pdf)
contiene 14 páginas, examinadas visualmente en su totalidad. La corrección es
documental: no se modificaron código ejecutable, comentarios de código, consultas,
DDL, contratos, pruebas ni registros históricos de ejecución.

El [manifiesto editorial](../../sprint1/postgres/evidencias/3nf/MANIFIESTO_REVISION_EDITORIAL_20261028T083357.json)
identifica las fuentes actuales, el PDF, el inventario revisado y los archivos
preservados. Los manifiestos anteriores conservan las huellas de sus propias
versiones documentales; no se actualizan para aparentar que describen esta revisión.

Se examinó un inventario de 179 archivos de entrega y soporte en `docs/`,
`sprint1/`, `scripts/`, `tests/` y las dos entradas principales. Como control
complementario del árbol público de 439 archivos, se analizaron léxicamente
232 archivos de texto y se verificó la sintaxis de 77 archivos Python y 124 JSON.
Ese control estático no equivale a ejecutar todos los caminos del código ni a
reproducir las cargas nativas. La revisión de contenido se centró en las rutas
vigentes, sus consultas, comentarios, diagramas, evidencias y referencias.

## Problemas encontrados y correcciones

| Hallazgo | Corrección editorial |
|---|---|
| La guía indicaba clonar `main`, que no contiene este respaldo normalizado | Se identifica la rama `fix/sprint1-postgresql-3nf` en los comandos y en las instrucciones de acceso |
| Cifras antiguas de 51 pruebas Python y 13 Node aparecían como estado vigente | Se distingue la suite actual de 65 pruebas Python y dos archivos Node de la integración nativa histórica |
| `--datos`, `queries.sql` y el núcleo de práctica podían confundirse con el DDL normalizado | Las guías y la matriz separan el validador normalizado, la reproducción v2 anterior y el staging complementario |
| La guía básica negaba el uso de asincronía sin delimitar la ruta | Se identifica `async`/`await` en los módulos v2 y se restringe la explicación de carga acotada al núcleo de práctica |
| Los índices de modelos incluían referencias a contratos anteriores como si fueran vigentes | Se enlazan el E-R de catorce tablas, el DDL normalizado y su cierre; los diagramas históricos conservan sus nodos y relaciones |
| La cardinalidad general del informe omitía la excepción canal–asignación | Se aclara que la PK de `channel_sensors` admite como máximo una fila por canal |
| El lote de enero podía confundirse con el resultado de MG02 | Se documentan 748.889 lecturas aceptadas, 748.765 dentro de la ventana y 124 fuera del filtro, sin tratarlas como rechazos o duplicados |
| La bibliografía incluía tres entradas no citadas y carecía de una referencia específica al nuevo cierre relacional | Se retiran las entradas no citadas y se incorpora la prueba de DF y el informe nativo normalizado; todas las referencias restantes se citan |
| Había una instrucción de revisión dirigida al equipo en el índice de diagramas | Se sustituye por la identificación del alcance histórico |
| Una línea de las conclusiones quedaba aislada al inicio de la página de referencias | Se mantiene unido el párrafo final para conservar una presentación coherente |

Las instrucciones de instalación, reproducción y distribución privada son
documentación de uso. No se consideran marcadores editoriales. Los comentarios
de código revisados describen precondiciones, invariantes, tratamiento de errores,
replay y separación de datos. Los imperativos técnicos, como conservar unidades
homogéneas o excluir vínculos desconocidos, mantienen su significado operativo.
No se identificaron stubs funcionales en el material vigente; el `pass` de una
excepción simulada en pruebas forma parte del doble de prueba.
Las etiquetas `madrid-draft-v1`, `madrid-draft-v1-frozen` y `madrid-draft-v2`
son identificadores de contratos distintos. Se conservan literalmente para
mantener la trazabilidad entre código, datos y evidencia.

## Correspondencia con la evidencia

- El DDL, el E-R y la cobertura de DF conservan 14 tablas, 83 columnas y 17 FK.
  La normalización sigue limitada a las DF declaradas y a JSONB como dominio
  indivisible; no se infieren dependencias de coincidencias del lote.
- El informe nativo PostgreSQL `20261028T071812-55791345.json` conserva sus ocho
  hashes de código actuales, cero diferencias contractuales y 748.889 lecturas.
  La evidencia de SQL avanzado coincide con sus tres archivos de código registrados.
- Las muestras anteriores y el FAIL inicial mantienen sus versiones y checksums.
  Los conteos de muestras no se presentan como una nueva carga masiva.
- MG02 coincide con el informe nativo MongoDB y la verificación independiente.
  Los eventos y alertas son derivados de una regla demo; la administración es
  sintética y las lecturas fuente son observadas. Los IDs derivados no acreditan
  dispositivos físicos.
- Los incidentes anonimizados de 2026 permanecen separados de las lecturas de
  la generación de enero de 2025; el inventario territorial no acredita vigencia
  histórica individual.

## Material histórico y límites de la revisión

Los borradores de `docs/academico/`, las matrices de investigación y las propuestas
de fases anteriores permanecen en el archivo de consulta identificado por
`docs/README.md`. No se incorporan como secciones del informe vigente. Sus
declaraciones de procedencia, incluidos los registros de asistencia automatizada,
se conservan como antecedentes; no se atribuye una norma institucional no acreditada.

El rastreo global encontró `TBD` en dos documentos de Fase 1 y tres secciones
sin contenido propio en matrices históricas de Fase 3. No son secciones del
informe ni componentes pendientes del código de entrega. Se preservan sus bytes
y alcance original, al igual que las instrucciones de trabajo contenidas en
borradores antiguos o notas selladas de evidencia. El PDF vigente no contiene
esos marcadores, instrucciones editoriales ni referencias a herramientas de IA.

El PDF histórico `SmartCity_Sprint1_3NF_20261028T075148.pdf` conserva la macro
literal de `locations.name` identificada en la revisión anterior. La versión
`20261028T080911` y el PDF vigente ya la corrigen. Las tres versiones tienen
14 páginas y se conservan con sus hashes propios; la primera no se presenta
como documento vigente de entrega.

## Asuntos académicos y técnicos que permanecen abiertos

| Aspecto | Alcance acreditado y limitación |
|---|---|
| Sensor físico frente a canal | PG07 no permite evaluar actividad física sin asignaciones acreditadas. MG01 utiliza canal y MG07 tipo de medición; no hay aceptación académica global de esas equivalencias |
| Datos sintéticos | Los tipos, categorías, usuarios, sensores y demás atributos administrativos demo mantienen su procedencia; no acreditan inventario municipal real |
| Información dinámica MongoDB | Existen objetos anidados y atributos opcionales, con cobertura académica parcial; no se declara satisfecho por almacenar JSON |
| Eventos, alertas y períodos | Regla demo y replay local; no alertas oficiales retrospectivas ni causalidad entre incidentes de 2026 y lecturas de 2025 |
| Restricciones negativas | Los ocho casos registran rechazos genéricos; no aíslan cada CHECK o FK ni una batería negativa completa MongoDB |
| Entorno de producción | No se acredita servidor compartido, autenticación real de clientes, alta disponibilidad ni restauración remota |
| Automatización de reproducción | `--datos` conserva el esquema relacional anterior. El DDL normalizado se verifica con su ejecutor independiente; unificar ambas rutas requeriría una modificación funcional que no se realizó |
| Alcance transversal | Materializadas, particionamiento y componente distribuido de octubre conservan su alcance no confirmado; los componentes de noviembre están fuera de esta revisión |

No se identificó una nueva inconsistencia que exigiera modificar funcionalidad
para corregir el texto. Los límites anteriores permanecen visibles en el informe
y en la auditoría interna. Este cierre editorial no constituye aprobación docente
ni cumplimiento integral del Sprint 1.

## Validación

- Suite offline: 65 pruebas Python y dos archivos Node aprobados.
- Pruebas documentales: seis casos aprobados.
- PDF: 14 páginas revisadas visualmente, referencias resueltas, índice estable,
  tablas legibles y ausencia de comandos LaTeX literales o texto fuera de página.
- Compilación sin errores ni cajas desbordadas. Se conserva únicamente el aviso
  no fatal de `epstopdf` por shell escape deshabilitado.
- Integridad PostgreSQL: checksums históricos y hashes del ejecutor nativo
  completos verificados; no se reejecutaron bases de datos.
- Integridad MongoDB: 29 archivos sellados y 19 archivos oficiales verificados.
- Los bloques Mermaid y el código de las figuras mantienen su estructura.
  Los archivos históricos de ejecución, los PDF anteriores y sus manifiestos
  permanecen intactos.
- Cambios limitados a Markdown y LaTeX, más el nuevo PDF, este informe interno
  y el manifiesto con su checksum. La relación exacta de archivos está en el
  manifiesto editorial. No se realizaron commit, push, merge ni cambios en bases.
