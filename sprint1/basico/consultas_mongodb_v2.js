'use strict';

// Consultas de entrega: datos reales v2. El identificador es un CANAL lógico,
// no un dispositivo físico inventado. No mezclar unidades ni fuentes al promediar.
function consultar(base, regla) {
  const primera = base.readings.findOne({ source_id: 'MAD-TRAFFIC' });
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
  resultados.MG01 = { parametros: canal, total: base.readings.countDocuments(canal),
    muestra: base.readings.find(canal, { _id: 1, channel_id: 1, observed_at: 1, value: 1, unit: 1 })
      .sort({ observed_at: 1 }).limit(5).toArray() };
  // MG02: inicio incluido, final excluido. H24 del último día puede caer fuera.
  resultados.MG02 = { parametros: fechas, total: base.readings.countDocuments(fechas),
    muestra: base.readings.find(fechas, { _id: 1, observed_at: 1, source_id: 1 })
      .sort({ observed_at: 1, _id: 1 }).limit(5).toArray() };
  // MG03: extremos de aire válido por variable y unidad.
  resultados.MG03 = base.readings.aggregate([
    { $match: validas },
    { $group: { _id: porTipo, cantidad: { $sum: 1 }, minimo: { $min: '$value' },
      maximo: { $max: '$value' }, promedio: { $avg: '$value' } } },
    { $sort: { '_id.tipo': 1, '_id.unidad': 1 } },
  ]).toArray();
  // MG04: eventos DERIVADOS con regla docente de demostración, no eventos oficiales.
  resultados.MG04 = { regla, total: base.derived_events.countDocuments({ rule_version: regla.version }),
    muestra: base.derived_events.find({ rule_version: regla.version },
      { _id: 1, measurement_id: 1, value: 1, threshold: 1, zone_id: 1, data_origin: 1 })
      .sort({ _id: 1 }).limit(5).toArray() };
  // MG05: alertas emitidas AHORA a una colección local, por distrito de inventario.
  // Son replay de lecturas históricas. No son notificaciones oficiales de 2025.
  resultados.MG05 = base.alerts.aggregate([
    { $match: { zone_id: { $ne: null }, rule_version: regla.version } },
    { $group: { _id: '$zone_id', cantidad: { $sum: 1 },
      primera_emision: { $min: '$emitted_at' }, ultima_emision: { $max: '$emitted_at' } } },
    { $sort: { _id: 1 } },
  ]).toArray();
  // MG06: solo zonas conocidas del inventario; no acredita su vigencia en 2025.
  resultados.MG06 = base.readings.aggregate([
    { $match: { zone_id: { $ne: null } } },
    { $group: { _id: { zona: '$zone_id', ...porTipo }, cantidad: { $sum: 1 },
      promedio: { $avg: '$value' } } },
    { $sort: { '_id.zona': 1, '_id.fuente': 1, '_id.tipo': 1, '_id.unidad': 1 } },
  ]).toArray();
  // MG07: tipo de medición, no una clasificación física de dispositivos.
  resultados.MG07 = base.readings.aggregate([
    { $group: { _id: porTipo, cantidad: { $sum: 1 }, promedio: { $avg: '$value' } } },
    { $sort: { '_id.fuente': 1, '_id.tipo': 1, '_id.unidad': 1 } },
  ]).toArray();
  // MG08: un documento por ACCIDENTE de 2026, no por persona involucrada.
  resultados.MG08 = base.incidents.aggregate([
    { $group: { _id: '$category', cantidad: { $sum: 1 } } }, { $sort: { _id: 1 } },
  ]).toArray();
  // MG09: agregación de volumen por fuente y flag de calidad.
  resultados.MG09 = base.readings.aggregate([
    { $group: { _id: { fuente: '$source_id', calidad: '$quality_flag' }, cantidad: { $sum: 1 } } },
    { $sort: { '_id.fuente': 1, '_id.calidad': 1 } },
  ]).toArray();
  // MG10: filtros combinados de tiempo, fuente, calidad, valor y zona.
  resultados.MG10 = { parametros: multiples, total: base.readings.countDocuments(multiples),
    muestra: base.readings.find(multiples, { _id: 1, zone_id: 1, value: 1, unit: 1 })
      .sort({ value: -1, _id: 1 }).limit(5).toArray() };
  return resultados;
}

module.exports = { consultar };
