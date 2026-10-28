# Documentación

## Documentación vigente del Sprint 1

- [Alcance y ejecución del Sprint 1](../ENTREGA_SPRINT1.md).
- [Alcance confirmado: requisitos completos de PostgreSQL y MongoDB](equipo/ALCANCE_CONFIRMADO_SPRINT1.md).
- [Estado y pendientes](equipo/ESTADO_SPRINT1.md).
- [Las 20 consultas](equipo/MATRIZ_CONSULTAS_SPRINT1.md).
- [Laboratorio académico MongoDB](../sprint1/mongodb/academico/README.md).
- [Cierre técnico MongoDB y evidencias actuales](../sprint1/mongodb/evidencia_final_mongodb.md).

## Informe del avance en LaTeX

**Versión breve para revisión y entrega:**
[SmartCity_Sprint1_Entrega.tex](avance_1/SmartCity_Sprint1_Entrega.tex), con
[PDF de 9 páginas](avance_1/SmartCity_Sprint1_Entrega.pdf), incluida la portada.
Mantiene las diez secciones del texto compartido por Fernanda, corrige las cifras
y el alcance técnico, incorpora tres diagramas (flujo, modelo relacional y
colecciones MongoDB) y omite los anexos de código. El relacional separa catálogos
y administración en dos paneles, con las FK entre paneles identificadas. Los otros
diagramas distinguen flujo, derivación y referencias mediante leyendas y estilos.
Para Overleaf basta subir ese `.tex`: no necesita imágenes externas.

En Overleaf, seleccionar `SmartCity_Sprint1_Entrega.tex` como documento principal
y compilar con pdfLaTeX o XeLaTeX. Localmente, con TeX Live:

```bash
cd docs/avance_1
pdflatex -halt-on-error SmartCity_Sprint1_Entrega.tex
pdflatex -halt-on-error SmartCity_Sprint1_Entrega.tex
```

La carpeta `avance_1/` contiene únicamente el `.tex` y el PDF vigentes, además
de las reglas de exclusión de auxiliares. Las versiones antiguas del informe y
sus manifiestos se retiraron de la carpeta; las que estuvieron publicadas pueden
consultarse en el [historial anterior a la limpieza](https://github.com/Alpizar28/SmartCity/tree/5eb3db7/docs/avance_1).
Las evidencias de ejecución de PostgreSQL y MongoDB conservan sus propios
reportes y hashes, separados de la documentación de entrega.
El [E-R con atributos y cardinalidades](arquitectura/diagrama_3nf.md) complementa
el diagrama resumido del informe.

## Referencias técnicas, solo cuando hagan falta

- [Contrato histórico anual `smartcity` v1](equipo/CONTRATO_UNIFICADO.md) y
  [diccionario de campos](equipo/unified_fields.csv).
- [Código y modelo del núcleo local `sprint1`](../sprint1/README.md).
- [Resultados históricos de carga anual v1](https://github.com/Alpizar28/SmartCity/blob/5eb3db7/docs/equipo/CIERRE_VALIDACION_SPRINT1.md).
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
