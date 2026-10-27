# Documentación

## Uso diario

- [Alcance y ejecución del Sprint 1](../ENTREGA_SPRINT1.md).
- [Estado y pendientes](equipo/ESTADO_SPRINT1.md).
- [Las 20 consultas](equipo/MATRIZ_CONSULTAS_SPRINT1.md).

## Informe del avance en LaTeX

El borrador editable empieza en [avance_1/main.tex](avance_1/main.tex).
Las cinco secciones de `avance_1/secciones/` cubren alcance/datos, modelos,
consultas, validación y cierre. Ya tienen contenido; no es una plantilla vacía.
Los pendientes están señalados y no deben presentarse como resultados terminados.

En Overleaf, subir la carpeta `avance_1/`, seleccionar `main.tex` como documento
principal y compilar con pdfLaTeX. Localmente, con TeX Live y `latexmk` instalados:

```bash
cd docs/avance_1
make pdf
```

Alternativa sin `latexmk`: ejecutar `pdflatex -halt-on-error main.tex` dos veces
desde esa misma carpeta. El PDF es un artefacto local ignorado por Git.
El diagrama incluido es un extracto del modelo, no el E-R completo aprobado.
Antes de entregar, completar portada, revisar 3FN/modelos y adjuntar resultados
de las veinte consultas con Daniel, Kembly y Fernanda.

## Referencias técnicas, solo cuando hagan falta

- [Contrato anual `smartcity`](equipo/CONTRATO_UNIFICADO.md) y
  [diccionario de campos](equipo/unified_fields.csv).
- [Código y modelo del núcleo local `sprint1`](../sprint1/README.md).
- [Resultados de carga anual](equipo/CIERRE_VALIDACION_SPRINT1.md).
- [Autorización de datos administrativos sintéticos](equipo/EVIDENCIA_AUTORIZACION_DATOS_SINTETICOS.md).
- [Propuesta de tráfico v2, todavía pendiente](decisiones/PROPUESTA_MADRID_DRAFT_V2.md).
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
