# Documentación

## Documentación vigente del Sprint 1

- [Alcance y ejecución del Sprint 1](../ENTREGA_SPRINT1.md).
- [Alcance confirmado: requisitos completos de PostgreSQL y MongoDB](equipo/ALCANCE_CONFIRMADO_SPRINT1.md).
- [Estado y pendientes](equipo/ESTADO_SPRINT1.md).
- [Las 20 consultas](equipo/MATRIZ_CONSULTAS_SPRINT1.md).
- [Laboratorio académico MongoDB](../sprint1/mongodb/academico/README.md).
- [Cierre técnico MongoDB y evidencias actuales](../sprint1/mongodb/evidencia_final_mongodb.md).

## Informe del avance en LaTeX

El informe universitario empieza en [avance_1/main.tex](avance_1/main.tex).
Las seis secciones cubren alcance/datos, modelos, equivalencias de atributos,
consultas, validación y conclusiones, con resultados y limitaciones explícitos.

En Overleaf, subir la carpeta `avance_1/`, seleccionar `main.tex` como documento
principal y compilar con pdfLaTeX. Localmente, con TeX Live y `latexmk` instalados:

```bash
cd docs/avance_1
make pdf
```

Alternativa sin `latexmk`: ejecutar `pdflatex -halt-on-error main.tex` dos veces
desde esa misma carpeta. `main.pdf` y los auxiliares de compilación están
ignorados por Git mediante `avance_1/.gitignore`. Los PDF de entrega con nombre
`SmartCity_Sprint1_3NF_<fechaUTC>.pdf` o `SmartCity_Sprint1_PaqueteA_<fechaUTC>.pdf` no están ignorados: se incluyen como
artefactos revisados junto con su manifiesto SHA-256. Cada revisión documental
genera un PDF y un manifiesto nuevos; las versiones anteriores se conservan
como registros históricos. El manifiesto de cierre documental más reciente
identifica el PDF vigente y las fuentes exactas utilizadas.
La revisión vigente es el [PDF del paquete A con limpieza editorial](avance_1/SmartCity_Sprint1_PaqueteA_Editorial_20261028T163407.pdf),
con su [manifiesto editorial](avance_1/MANIFIESTO_EDITORIAL_20261028T163407.json)
y [checksum](avance_1/MANIFIESTO_EDITORIAL_20261028T163407.sha256).
El [PDF previo del paquete A](https://github.com/Alpizar28/SmartCity/blob/9d84a34e529a72b316c540bff549080c906b0126/docs/avance_1/SmartCity_Sprint1_PaqueteA_20261028T162209.pdf)
y su [manifiesto original](../sprint1/mongodb/evidencias/academico/cierre-20261028T162209/MANIFIESTO_PAQUETE_A.json)
se conservan como snapshot histórico; sus hashes documentales corresponden a esa revisión.
El [cierre del paquete A](equipo/CIERRE_PAQUETE_A_SPRINT1_20261028T162209.md) detalla los archivos y pruebas.
La revisión editorial anterior conserva su PDF y manifiesto históricos.
Los límites de las pruebas se describen en los cierres técnicos vigentes. La
[revisión académica y editorial](https://github.com/Alpizar28/SmartCity/blob/9d84a34e529a72b316c540bff549080c906b0126/docs/equipo/REVISION_ACADEMICA_EDITORIAL_SPRINT1_20261028T083357.md)
conserva el alcance de su propia fecha.
La [auditoría documental anterior](https://github.com/Alpizar28/SmartCity/blob/9d84a34e529a72b316c540bff549080c906b0126/docs/equipo/AUDITORIA_DOCUMENTAL_SPRINT1.md)
conserva el alcance y las verificaciones de su propia fecha.
El informe incluye el modelo completo de catorce tablas y la matriz de los 17
atributos exigidos. El [E-R con atributos y cardinalidades](arquitectura/diagrama_3nf.md)
se corresponde con el DDL normalizado. Los antecedentes de doce tablas se
conservan separados de la versión de entrega.

## Referencias técnicas, solo cuando hagan falta

- [Contrato histórico anual `smartcity` v1](equipo/CONTRATO_UNIFICADO.md) y
  [diccionario de campos](equipo/unified_fields.csv).
- [Código y modelo del núcleo local `sprint1`](../sprint1/README.md).
- [Resultados históricos de carga anual v1](equipo/CIERRE_VALIDACION_SPRINT1.md).
- [Autorización de datos administrativos sintéticos](equipo/EVIDENCIA_AUTORIZACION_DATOS_SINTETICOS.md).
- [Interfaz v2 implementada](../sprint1/postgres/schema_v2_3nf.sql), vista
  `observation_contract`; [adaptación histórica v2](../sprint1/postgres/contract_v2.sql),
  [ETL](../sprint1/basico/preparar_v2.py) y
  [cierre técnico MongoDB](../sprint1/mongodb/evidencia_final_mongodb.md).
- [Requisitos académicos abiertos](equipo/ALCANCE_CONFIRMADO_SPRINT1.md#aspectos-transversales-o-pendientes-de-confirmación).

## Archivo de consulta, no instrucciones vigentes de entrega

Los demás documentos conservan investigación, decisiones y checkpoints anteriores.
Se mantienen en sus rutas porque las pruebas y los manifiestos los referencian.
Sus estados describen cada fase histórica y no sustituyen los cierres técnicos actuales.
Los documentos y PDF retirados durante la limpieza se consultan mediante enlaces
a la revisión histórica de GitHub. Los manifiestos antiguos mantienen sus rutas
y hashes originales: describen aquel snapshot, no el árbol local simplificado.
La [propuesta previa v2](decisiones/PROPUESTA_MADRID_DRAFT_V2.md), las listas de
preguntas al profesor, actas y resúmenes dirigidos a integrantes son antecedentes
de planificación o coordinación, no especificaciones definitivas. La declaración
de asistencia de IA se conserva con su alcance histórico; las tareas editoriales
pendientes de los borradores no forman parte del informe vigente.

En particular, `academico/texto_para_informe.md`, las síntesis de `datasets/`,
el pipeline y los modelos históricos de `arquitectura/`, y los planes/checklists
anteriores de `equipo/` contienen secciones superadas. Esos borradores,
declaraciones de procedencia y matrices de investigación no forman parte del
informe académico vigente. Se conservan como antecedentes verificables.
El E-R de entrega es `arquitectura/diagrama_3nf.md`; los demás diagramas tienen
identificado el contrato o núcleo complementario al que corresponden.

Las fases `00_*`–`05_*` de [research/datasets](../research/datasets/README.md)
y el [contrato provisional](../CONTRATO_PROVISIONAL_DATASET.md) son antecedentes.
No mezclar sus cifras o contratos con la carga anual ni con los tres ejemplos locales.
