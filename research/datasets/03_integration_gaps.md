# Fase 3 — Integración: evidencia y tratamientos

## Recuento de Fase 2

Madrid **13.351.700** filas principales:76513 diarias aire+56383 meteo+13218804 tráfico. NYC **247.526**:85106 DOT+38290 EPA local+124130 solicitudes. Londres **4.007.440**:4000000 energía+7440 LAQN. Recontados desde originales/ZIP y muestras; **son granularidades distintas**, no cantidades de dispositivos ni mediciones únicas comparables. Complementos/inventarios excluidos. Evidencia `validation.json`, hashes en manifiestos 02/inputs_manifest.csv.

## Madrid

**19087/33821NO₂elegibles=56,435351%**, enero/julio 2025, magnitud 8 frente a temperatura 83. 14722 lecturas sin sitio co-localizado;19099 mapeadas y 12 sin temperatura elegible. Coincidencia temporal dentro de sitios mapeados 99,94%. Los 13 sitios co-localizados se identificaron por código y coordenadas<1 m, no identidad de analizador. El porcentaje no es tasa de fallas ni cobertura de todo el archivo.

Pérdidas por sitio/mes/causa: `madrid_no2_losses.csv`. Sitios con alguna pérdida: MAD-AIR:11, MAD-AIR:17, MAD-AIR:18, MAD-AIR:27, MAD-AIR:4, MAD-AIR:40, MAD-AIR:47, MAD-AIR:48, MAD-AIR:49, MAD-AIR:50, MAD-AIR:57, MAD-AIR:60. Catálogo independiente contrastado en `catalog_activity.csv`: Urb.Embajada(MAD-AIR:55)sin lecturas de la muestra, no evidencia de estado inactivo. Distritos ambien tales/historia de inventario siguen pendientes.

H24 representa fin 23–24 h y se lleva a 00 h siguiente; enero/julio evitan transicionesDST. `PUNTO_MUESTREO` de aire incluye técnica, no inventario de dispositivos persistentes; meteo 100%vacío. Unidades aire verificadas con AnexoII (NO₂/PM₂.₅µg/m³, COmg/m³); meteo sigue provisional. AnexoI contiene altas/bajas/recodificaciones de sitio, **no instalación individual** ni vigencia cartográfica completa en 2025.

Tráfico intensidadveh/h no conteo: intervalos de integración 1–30 min, ponderación/exposición y validez vmed/carga por tipo pendientes. Energía municipal mensual no responde energía horaria; concentraciónCO₂ y alertas históricas no se resuelven limpiando valores.

## NYC

**4767 grupos con dos valores distintos,9534 filas**, campañas 36401 y 36828. Clave campaña-segmento-dirección-fecha/hora:4767 extras; añadirWKT ytodos los descriptores (boro, street, fromst, tost) no los elimina. Cero filas originales idénticas. No hay clave física correcta acreditada: índice de fila/localizador de raw identifica procedencia, no carril/contador. Conservar cuarentena y 75572 lecturas no ambiguas; no sumar conflictos como si fueran carriles.

DOT tiene 219 días observados en el archivo, campañas discontinuas, no actividad esperada constante del borough. EPA 88101 cubre cinco sitios en Bronx/Brooklyn/Queens; no Manhattan/StatenIsland para este parámetro. UTC evita falsas colisionesDST, calendario local se deriva solo al agregar. CRS delWKT candidato 2263 pendiente, no usado en join aceptado.

DOT–EPA **146/322 gruposborough/día=45,34%** (176 DOTsinEPA,737 EPAsin DOT). DOT–311 **11/322=3,416149%**: porcentaje de gruposDOT con solicitudes en la muestra, **no porcentaje de solicitudes ligadas ni tasa de fallas**. 311 solo 16 fechas/96 grupos; los 11 gruposDOT que caen en fechas solicitadas sí coinciden. Ampliar 311 en fechas de campaña puede aumentar cobertura, pero no corrige identidadDOT, desigual exposición niEPA parcial. Intersección triple:1 grupo/322(0,31%). Detalle en `nyc_borough_day_matches.csv`.

311 created_date es reporte, no fecha de hecho. AgregadosEPA promedian primero sitio, despuésborough, perdiendoPOC/métodos/horas/picos. LL 84CO₂e anual no concentraciónCO₂. Energía horaria, velocidad y recorridos requieren fuente real adicional.

## Londres

Se deduplicaron 233 extras idénticos enJan/Jul;44 horas/hogar parciales excluidas. Suma de dos intervalos únicos semihorarios por hogar/hora →cohorte; promedioNO₂ de sitios disponibles. **1488/1488 timestamps coinciden**(744 enero+744 julio)sin desplazar reloj. No es 100%de lecturas/hogares emparejados, sincronización demostrada ni geografía.

Panel 108–119 hogares por hora; **0%ubicación fina de hogares**: sin lat/lon/borough. ReferenciaSQLunknowncon geografíaNULL, no casas inventadas; cohorte no totalLondres. LAQNtimestamp GMT; LCLtimezone pendiente. Sensibilidad al desplazar julio:

| DesplazamientoLCL | Horas coincidentes | Coberturaizquierda | Pearson exploratorio |
|---|---:|---:|---:|
| -1 h | 1487 | 99.9328% | 0.378197 |
| 0 h | 1488 | 100.0000% | 0.373043 |
| 1 h | 1487 | 99.9328% | 0.359689 |

Ningún desplazamiento se declara correcto: la variación prueba la necesidad de confirmarGMT/BST, no valida una correlación urbana niSpark/causalidad. LCL global:3997252 claves únicas/2748 extras/0 conflictos de valor, nuevo escaneo 4 M, solo cuatro miembros completosCRC.

Licencia LAQN permite finalidadinformativa/educativa y excluyeoperativa/comercial; no se acredita redistribución general. API pública no licenciaCCBY; LCLCCBY no concede derechosLAQN. Mantener lecturas/integraciones privadas y consultar permiso para dashboard/exportación pública.

## Clasificación y resolución

| Problema | Categoría | Estado/tratamiento |
|---|---|---|
| LCLduplicados idénticos | Limpieza | Deduplicación derivada comprobada, raw intacto |
| Falsos duplicadosEPA DST | Modelado temporal | Resuelto conservandoUTC, regresión aprobada |
| DOTvalores conflictivos | Fuente complementaria/no resuelto | Falta identidad; cuarentena, no sumas arbitrarias |
| Madrid 12 huecos y no co-localizados | Modelado/agregación o complemento | QA/NULL y alcance parcial; fuente/cartografía para zonas |
| Inventarios históricos/instalación/estado | Fuente complementaria/potencial bloqueo | Alta/apertura de sitio no instalación individual |
| CampañasNYC/3,42% | Fuente complementaria/agregación | Ampliar fechas 311 y controlar exposición; no ausencia=falla |
| LCLreloj | Fuente complementaria/potencial bloqueo | Confirmar definición de tiempo, sensibilidad no resuelve |
| HogaresLCL sin zona | Fuente complementaria/bloqueo espacial | No recuperable por limpieza; no geografía sintética |
| Licencia LAQN | No resuelto/potencial bloqueo | Permiso/alcance de publicación |
| Usuariosapp | Observado futuro/synthetic opcional | Registro autorizado o hasta 4 fixtures de prueba, no generados |
| Eventos/alertas | Derived o fuente complementaria | Política aprobada y evidencia de emisión; sin historia ficticia |

Ningún problema exige síntesis inevitable: buscar fuente, mantenerNULL, aceptar alcance/derivado o declarar incumplimiento. **Originales sin modificaciones.**
