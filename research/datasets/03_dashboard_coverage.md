# Fase 3 — Dashboard: cobertura y riesgos

No se implementó UI ni se ejecutóMongoDB/Hadoop/Spark. Los estados de la tabla evalúan datos/semántica, no componentes funcionando. Orígenes en `03_data_origin_matrix.csv`, matriz completa en `03_compliance_matrix.csv`. Un proxy no se renombra KPI observado.

| Dominio | KPI exacto | Madrid | NYC | Londres | Definición y evidencia de la limitación |
|---|---|---|---|---|---|
| Movilidad | Vehículos detectados | PARCIAL | PARCIAL | PARCIAL | Madrid intensidadveh/h≠conteo sin integración de duración; NYCvol intervalos reales de campañas; DfT 100 filas muestra inicial |
| Movilidad | Velocidad promedio | PARCIAL | NO_CUMPLE | NO_CUMPLE | Madrid vmed original, validez por tipo/flags a cerrar; NYC/DfT conteo no velocidad |
| Movilidad | Congestión promedio | PARCIAL | NO_CUMPLE | NO_CUMPLE | Madrid carga/ocupación son proxies medidos, umbral/métrica requiere definición; conteo no congestión |
| Movilidad | Accidentes/incidentes | FACTIBLE_NO_EJECUTADO | PARCIAL | NO_VERIFICADO | Madrid expediente real 2026; NYCsolicitudes, no accidente confirmado; LondresTfL pendiente |
| Movilidad | Tiempo promedio de recorrido | NO_CUMPLE | NO_CUMPLE | NO_CUMPLE | No rutas/tiempos observados en núcleos auditados |
| Ambiente | Temperatura global promedio | PARCIAL | NO_VERIFICADO | NO_VERIFICADO | MadridT 83 disponible/unidad provisional/promedio de estaciones NO temperatura global planeta; NOAA no auditado completo |
| Ambiente | PM₂.₅ promedio | FACTIBLE_NO_EJECUTADO | FACTIBLE_NO_EJECUTADO | NO_VERIFICADO | Madridmagnitud 9; EPAPM₂.₅ cinco sitios/tresboroughs; LAQN muestraNO₂noPM₂.₅ |
| Ambiente | CO₂ | NO_CUMPLE | NO_CUMPLE | NO_CUMPLE | CO, NO₂, CO₂e anual y consumo no concentración ambien talCO₂ |
| Ambiente | Humedad | PARCIAL | NO_VERIFICADO | NO_VERIFICADO | Madrid 86 real/unit percentprovisional; NOAA complementos sin prueba completa |
| Ambiente | Número de alertas ambien tales | NO_CUMPLE | NO_CUMPLE | NO_CUMPLE | Emisiones reales no acreditadas; umbral derivado requiere política y no es emisiónhistórica |
| Energía | Consumo total | PARCIAL | PARCIAL | PARCIAL | Madrid medidores/niveles/unidades; LL 84 padre/revisión; LCLtotalcohorte, no ciudad |
| Energía | Consumo promedio por zona | PARCIAL | PARCIAL | NO_CUMPLE | Madrid distrito mensual; LL 84 boroughanual; hogaresLCL sinzona fina |
| Energía | Consumo por hora | NO_CUMPLE | NO_CUMPLE | PARCIAL | Mensual/anual no se reparte a horas; LCLdos medias horas únicas, clockpendiente |
| Energía | Picos de consumo | PARCIAL | PARCIAL | PARCIAL | Picos mensuales/anuales no pico horario; LCL panel/clock requerido |
| Energía | Variación respecto al período anterior | PARCIAL | PARCIAL | PARCIAL | Revisiones/submedidores/panel estable/períodoscomparables antes de totals |
| IoT | Número de sensores | PARCIAL | PARCIAL | PARCIAL | Canales/sitios acreditados; no conteo automático de analizadores físicos |
| IoT | Mediciones recibidas | PARCIAL | PARCIAL | PARCIAL | Históricoobservado≠received_at; ingestiónfutura permitirá contar recepciónreal |
| IoT | Sensores activos/inactivos | NO_CUMPLE | NO_CUMPLE | NO_CUMPLE | Sin estado administrativo individual; actividadmuestreada nofalla |
| IoT | Alertas generadas | NO_CUMPLE | NO_CUMPLE | NO_CUMPLE | Nadaemitido enesta fase; futura regla derived a aprobar |
| IoT | Datos por minuto/hora/día | FACTIBLE_NO_EJECUTADO | FACTIBLE_NO_EJECUTADO | FACTIBLE_NO_EJECUTADO | Agrupaciónobserved_atreal, huecos/campañas explícitos, no recepciónstreaming |
| IoT | Total de lecturas registradas por segundo | PARCIAL | PARCIAL | PARCIAL | Tasa deobservación no recepción histórica; medir ingested_at en ingestiónfutura |


## Visualizaciones y filtros

Serie temporal: fuentes QA, mostrando huecos, ventana/campaña y reloj. Comparativa por zonas: Madridtráficodistrito y ambientesitio/ciudad; NYCboroughconEPA parcial; LondresLAQNautoridad, **no energíaLCLporborough**. Proporciones por tipo: canales/variables/categorías, no analizadores físicos inventados. Cuarto gráfico debe ser **resultado realmente generado por Spark**, aún inexistente.

Mapa: Madrid coordenadaspublicadas de inventarios yEPAWGS 84; DOTsolo después de confirmarCRS. LAQNpuntos, LCLhogares sin ubicación. Coordenadas plausibles no acreditan precisión/vigenciahistórica. Distrito ambien talMadrid requiere cartografíaoficial, no proximidad inventada.

Filtros obligatorios período/zona/tipo: disponibles en subconjuntos geográficos conocidos; NULL visible como no disponible, ciudad no barrio. Sensores/categorías recomendados conIDcanal estable y selectores separados para campaña/hogar/solicitud. Tabla detalle/paginación y panel único conselectorPG/Mongo/HDFS/Spark siguen sin implementar.

Etiquetas tecnológicas deben indicar el motor ejecutado: no PythoncomoMongo/Spark. Los cuatro dominios completos no están cubiertos por ninguna alternativa; CO₂, alertas reales, tiempo de recorrido, estado e instalación individual siguen sin acreditarse. Energía mensual/anual y total de cohorte no KPIs horarios/ciudad intercambiables.
