# Documentación

## Uso diario

- [Alcance y ejecución del Sprint 1](../ENTREGA_SPRINT1.md).
- [Alcance confirmado: requisitos completos de PostgreSQL y MongoDB](equipo/ALCANCE_CONFIRMADO_SPRINT1.md).
- [Estado y pendientes](equipo/ESTADO_SPRINT1.md).
- [Las 20 consultas](equipo/MATRIZ_CONSULTAS_SPRINT1.md).
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
`SmartCity_Sprint1_3NF_<fechaUTC>.pdf` no están ignorados: se incluyen como
artefactos revisados junto con su manifiesto SHA-256. Cada revisión documental
genera un PDF y un manifiesto nuevos; las versiones anteriores se conservan
como registros históricos. El manifiesto de cierre documental más reciente
identifica el PDF vigente y las fuentes exactas utilizadas.
La revisión vigente es el [PDF de cierre documental](avance_1/SmartCity_Sprint1_3NF_20261028T080911.pdf),
con su [manifiesto](../sprint1/postgres/evidencias/3nf/MANIFIESTO_CIERRE_DOCUMENTAL_20261028T080911.json).
Los límites académicos y la cobertura de pruebas se registran en la
[auditoría interna](equipo/AUDITORIA_DOCUMENTAL_SPRINT1.md).
El informe incluye el modelo completo de catorce tablas y la matriz de los 17
atributos exigidos. El [E-R con atributos y cardinalidades](arquitectura/diagrama_3nf.md)
se corresponde con el DDL normalizado. Los antecedentes de doce tablas se
conservan separados de la versión de entrega.

## Referencias técnicas, solo cuando hagan falta

- [Contrato anual `smartcity`](equipo/CONTRATO_UNIFICADO.md) y
  [diccionario de campos](equipo/unified_fields.csv).
- [Código y modelo del núcleo local `sprint1`](../sprint1/README.md).
- [Resultados de carga anual](equipo/CIERRE_VALIDACION_SPRINT1.md).
- [Autorización de datos administrativos sintéticos](equipo/EVIDENCIA_AUTORIZACION_DATOS_SINTETICOS.md).
- [Contrato v2 y ruta local de dos fuentes](decisiones/PROPUESTA_MADRID_DRAFT_V2.md).
- [Preguntas que siguen abiertas](../PREGUNTAS_PROFESOR.md).

## Archivo de consulta, no instrucciones vigentes de entrega

Los demás documentos conservan investigación, decisiones y checkpoints anteriores.
Se mantienen en sus rutas porque las pruebas y los manifiestos los referencian.
No hace falta leerlos todos para trabajar ni copiar sus estados al informe actual.

En particular, `academico/texto_para_informe.md`, las síntesis de `datasets/`,
los modelos y el pipeline de `arquitectura/`, y los planes/checklists anteriores
de `equipo/` contienen secciones superadas. Consultarlos por contexto, no como
lista actual de tareas o comandos de entrega. Los diagramas también requieren
revisión para la implementación elegida.

Las fases `00_*`–`05_*` de [research/datasets](../research/datasets/README.md)
y el [contrato provisional](../CONTRATO_PROVISIONAL_DATASET.md) son antecedentes.
No mezclar sus cifras o contratos con la carga anual ni con los tres ejemplos locales.
