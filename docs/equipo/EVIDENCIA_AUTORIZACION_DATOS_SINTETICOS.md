# Evidencia de autorización para datos sintéticos administrativos

## Alcance autorizado

Respuesta docente aportada por José, 10/10/2026, 21:14:

> “Pueden poner datos aleatorios a la hora de la carga.”

La consulta previa se refería a fechas de instalación, estado de sensores, usuarios y organismo responsable cuando esos atributos no existen en la fuente pública.

## Aplicación en Sprint 1

- Permitido: organizaciones, usuarios, sensores, fechas de instalación y estados administrativos sintéticos para demostración.
- No permitido inferir: mediciones reales, unidades, reloj de publicación, ubicación histórica o identidad física observada.
- Invariante: `observations` y `readings` conservan `data_origin=observed`; las entidades demo llevan `data_origin=synthetic`, semilla, versión del generador y procedencia.
- Los sensores demo no se enlazan a `channels` ni a lecturas reales. La autorización permite completar entidades administrativas, no afirmar que un dispositivo ficticio produjo una medición pública.

No se versionan captura de pantalla, teléfono, foto de perfil ni otros datos personales de la conversación.
