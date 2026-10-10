# Preguntas priorizadas al profesor

**Sin respuestas acreditadas.** Fernanda coordina la consulta; cada respuesta debe conservar fecha, medio, alcance y referencia. E/P/I y páginas están en [requisitos](../../research/datasets/00_requirements.md). Esta lista no autoriza implementación ni sustituye acuerdos del equipo.

## Prioridad 1 — bloqueos de modelo y consultas

1. **Sensor físico frente a canal lógico:** ¿se aceptan consultas por canal/sitio explícitamente rotuladas para PG01/02/05/08 y MG01/07, si `sensor_id` permanece NULL? Si se exige dispositivo individual, falta inventario verificable; no son equivalentes.
2. **Instalación y estado administrativo:** ¿se permite NULL y una consulta alternativa declarada para PG03/PG06? Alta de sitio, primera lectura, QA y actividad en ventana no acreditan instalación ni estado activo/inactivo del dispositivo.
3. **Organismos y usuarios:** ¿qué evidencia de relación dispositivo–organismo y responsable/cargo satisface PG04? ¿Los integrantes reales con consentimiento, o usuarios demo aislados aprobados, satisfacen la entidad de aplicación? Publicador no basta y no se inventarán personas/correos.
4. **Críticos y alertas:** ¿MG04 admite eventos derivados con regla/unidad/duración/QA/versiones y MG05 un replay actual con `emitted_at` real y evidencia de emisión? No existen alertas oficiales históricas acreditadas; colección vacía no demuestra cumplimiento.

## Prioridad 2 — volumen y alcance de fuentes/KPIs

5. **Mínimos:** ¿100.000 hechos relacionales y 500.000 intervalos multivariables únicos son unidades aceptadas? ¿Cómo se computan los 100 MB propuestos: globales, comprimidos o lógicos? Para Spark se ampliará historia real y se probará ≥1 millón; no se presenta enero como suficiente.
6. **Sintéticos:** si se autorizan, ¿qué entidades/consultas pueden demostrarse con fixtures y qué declaración se exige? Preferimos fuentes reales y NULL explícitos; la autorización de E no implica permiso del equipo/usuario para generación masiva.
7. **KPIs sin fuente:** ¿se exigen todos los indicadores estrictos o puede declararse alcance parcial? No hay CO₂ ambiental ni tiempos de recorrido acreditados; energía municipal mensual no equivale a horaria. No sustituiremos CO₂ por CO/NO₂/CO₂e ni recorridos por velocidad.
8. **Complementos y repositorios:** ¿se aceptan incidentes de 2026 y energía mensual en consultas separadas, sin falso join con enero de 2025? E p. 6 exige fuentes distintas y p. 23 recomienda repositorios distintos: ¿hay requisito adicional para el avance?

## Prioridad 3 — entrega y transparencia

9. **Fecha/rúbrica del avance:** ¿se confirma el 28 de octubre de 2026 y una rúbrica específica? E fija 25 de noviembre; la fecha de avance procede de P. Confirmar también CE-3191 frente al nombre CE3101 del PDF.
10. **Uso de IA:** ¿qué formato, identificación de herramientas, anexos o registro de prompts exige la normativa? Se declarará asistencia automatizada, sin atribuir análisis manual independiente ni aprobación humana inexistente.

## Decisiones internas que no debe resolver el profesor por el equipo

- Los cuatro ratifican ciudad, fuentes, período, contrato, reparto y calendario; una puntuación técnica no firma por ellos.
- José acredita unidades, clocks, CRS y vigencias con fuentes técnicas; una aceptación académica no convierte hipótesis en metadatos confirmados.
- Daniel/Kembly revisan DDL, dependencias, colecciones, índices y consultas; registran estados parciales antes de afirmar cumplimiento.
- El equipo acuerda consentimiento de usuarios, minimización de datos, namespace demo, reglas propuestas y condiciones de publicación.
- José autoriza acceso/cargas y evalúa despliegue con el administrador; la respuesta docente no autoriza tocar Coolify ni hacer push.

## Registro breve por completar

| Campo | Valor actual |
|---|---|
| Pregunta, respuesta literal y alcance | Pendientes |
| Fecha/medio y evidencia | Pendientes |
| Impacto en requisitos/contrato | Por evaluar tras respuesta |
| Acuerdo de José/Daniel/Kembly/Fernanda | Pendiente |

No cambiar NO_CUMPLE/PARCIAL a cumplido hasta contar con fuente, aceptación y ejecución aplicables. Referencia detallada: [05_academic_decisions.md](../../research/datasets/05_academic_decisions.md).
