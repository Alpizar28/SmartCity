'use strict';

// Consultas de entrega: datos reales v2. El identificador es un CANAL lógico,
// no un dispositivo físico inventado. No mezclar unidades ni fuentes al promediar.
// Un módulo require no recibe el await automático de la consola mongosh.
// Esperar cada operación también permite usar estas funciones desde un cliente real.
async function buscar(coleccion, filtro, campos, orden) {
  let cursor = await coleccion.find(filtro, campos);
  cursor = await cursor.sort(orden);
  cursor = await cursor.limit(5);
  return await cursor.toArray();
}
async function agrupar(coleccion, etapas) {
  const cursor = await coleccion.aggregate(etapas);
  return await cursor.toArray();
}

async function consultar(base, regla) {
  const primera = await base.readings.findOne({ source_id: 'MAD-TRAFFIC' });
  if (!primera) throw new Error('Falta la segunda fuente real de tráfico');
  const fechas = { observed_at: {
    $gte: new Date('2024-12-31T23:00:00Z'),
    $lt: new Date('2025-01-31T23:00:00Z'),
  } };
  const canal = { channel_id: primera.channel_id, source_version: primera.source_version };
  const validas = { source_id: 'MAD-AIR', quality_flag: 'V', unit_status: 'verified_dictionary' };
  const porTipo = { fuente: '$source_id', tipo: '$measurement_type', unidad: '$unit' };
  const multiples = { ...fechas, source_id: 'MAD-TRAFFIC', quality_flag: 'N',
    value: { $gt: regla.threshold }, zone_id: { $ne: null } };

  const resultados = {};
  // MG01: lecturas de un canal concreto, rotulado como alternativa a sensor físico.
  resultados.MG01 = { parametros: canal, total: await base.readings.countDocuments(canal),
    muestra: await buscar(base.readings, canal,
      { _id: 1, channel_id: 1, observed_at: 1, value: 1, unit: 1 }, { observed_at: 1 }) };
  // MG02: inicio incluido, final excluido. H24 del último día puede caer fuera.
  resultados.MG02 = { parametros: fechas, total: await base.readings.countDocuments(fechas),
    muestra: await buscar(base.readings, fechas,
      { _id: 1, observed_at: 1, source_id: 1 }, { observed_at: 1, _id: 1 }) };
  // MG03: extremos de aire válido por variable y unidad.
  resultados.MG03 = await agrupar(base.readings, [
    { $match: validas },
    { $group: { _id: porTipo, cantidad: { $sum: 1 }, minimo: { $min: '$value' },
      maximo: { $max: '$value' }, promedio: { $avg: '$value' } } },
    { $sort: { '_id.tipo': 1, '_id.unidad': 1 } },
  ]);
  // MG04: eventos DERIVADOS con regla docente de demostración, no eventos oficiales.
  resultados.MG04 = { regla, total: await base.derived_events.countDocuments({ rule_version: regla.version }),
    muestra: await buscar(base.derived_events, { rule_version: regla.version },
      { _id: 1, measurement_id: 1, value: 1, threshold: 1, zone_id: 1, data_origin: 1 }, { _id: 1 }) };
  // MG05: alertas emitidas AHORA a una colección local, por distrito de inventario.
  // Son replay de lecturas históricas. No son notificaciones oficiales de 2025.
  resultados.MG05 = await agrupar(base.alerts, [
    { $match: { zone_id: { $ne: null }, rule_version: regla.version } },
    { $group: { _id: '$zone_id', cantidad: { $sum: 1 },
      primera_emision: { $min: '$emitted_at' }, ultima_emision: { $max: '$emitted_at' } } },
    { $sort: { _id: 1 } },
  ]);
  // MG06: solo zonas conocidas del inventario; no acredita su vigencia en 2025.
  resultados.MG06 = await agrupar(base.readings, [
    { $match: { zone_id: { $ne: null } } },
    { $group: { _id: { zona: '$zone_id', ...porTipo }, cantidad: { $sum: 1 },
      promedio: { $avg: '$value' } } },
    { $sort: { '_id.zona': 1, '_id.fuente': 1, '_id.tipo': 1, '_id.unidad': 1 } },
  ]);
  // MG07: tipo de medición, no una clasificación física de dispositivos.
  resultados.MG07 = await agrupar(base.readings, [
    { $group: { _id: porTipo, cantidad: { $sum: 1 }, promedio: { $avg: '$value' } } },
    { $sort: { '_id.fuente': 1, '_id.tipo': 1, '_id.unidad': 1 } },
  ]);
  // MG08: un documento por ACCIDENTE de 2026, no por persona involucrada.
  resultados.MG08 = await agrupar(base.incidents, [
    { $group: { _id: '$category', cantidad: { $sum: 1 } } }, { $sort: { _id: 1 } },
  ]);
  // MG09: agregación de volumen por fuente y flag de calidad.
  resultados.MG09 = await agrupar(base.readings, [
    { $group: { _id: { fuente: '$source_id', calidad: '$quality_flag' }, cantidad: { $sum: 1 } } },
    { $sort: { '_id.fuente': 1, '_id.calidad': 1 } },
  ]);
  // MG10: filtros combinados de tiempo, fuente, calidad, valor y zona.
  resultados.MG10 = { parametros: multiples, total: await base.readings.countDocuments(multiples),
    muestra: await buscar(base.readings, multiples,
      { _id: 1, zone_id: 1, value: 1, unit: 1 }, { value: -1, _id: 1 }) };
  return resultados;
}

module.exports = { consultar };
