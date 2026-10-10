# Preguntas que requieren validación docente

Esta es la fuente canónica, breve y lista para enviar. El contexto, impacto y registro de respuestas se mantienen en [`docs/equipo/preguntas_profesor.md`](docs/equipo/preguntas_profesor.md). Estas preguntas tratan aceptación académica o interpretación de la rúbrica; no sustituyen la evidencia técnica que el equipo debe obtener de fuentes oficiales.

1. **Sensor físico frente a canal/sitio.** Mientras no exista un inventario individual verificable, ¿se acepta que las consultas y el modelo se expresen como canal lógico/sitio, con `sensor_id=NULL`, declarando explícitamente que no representan dispositivos físicos?

2. **Instalación y estado administrativo.** Para requisitos que dependan de instalación o activo/inactivo, ¿se acepta mantener esos atributos en `NULL` y presentar una consulta alternativa de actividad observada, sin afirmar que actividad, QA, primera lectura o ausencia de lecturas son estado administrativo?

3. **Organismos y usuarios.** ¿Qué evidencia mínima satisface el requisito de relación dispositivo–organismo/responsable? Para usuarios de la aplicación, ¿se aceptan únicamente cuentas reales del equipo con consentimiento o se permite una demo aislada autorizada? No se usarán personas de datasets ni identidades inventadas.

4. **Eventos y alertas derivados.** Si la rúbrica exige eventos/alertas, ¿acepta reglas derivadas versionadas y un replay con `emitted_at` real de la ejecución, claramente distinto de una alerta histórica oficial? Sin esa aceptación no se generarán alertas.
