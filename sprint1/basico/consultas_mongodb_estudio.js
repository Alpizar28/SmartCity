'use strict';

// Versión para estudiar. No reemplaza las consultas oficiales ni sus evidencias.
// Los campos conservan los nombres del dataset para no cambiar los resultados.

async function buscarMuestra(coleccion, filtro, campos, orden) {
  let cursor = await coleccion.find(filtro, campos);
  cursor = await cursor.sort(orden);
  cursor = await cursor.limit(5);
  return await cursor.toArray();
}

async function ejecutarAgregacion(coleccion, etapas) {
  const cursor = await coleccion.aggregate(etapas);
  return await cursor.toArray();
}

function fechasDeEnero() {
  // Enero de 2025 en Madrid, expresado en UTC. El final no se incluye.
  return {
    observed_at: {
      $gte: new Date('2024-12-31T23:00:00Z'),
      $lt: new Date('2025-01-31T23:00:00Z'),
    },
  };
}

function grupoPorMedicion() {
  // Una media solo tiene sentido si coinciden fuente, magnitud y unidad.
  return {
    fuente: '$source_id',
    tipo: '$measurement_type',
    unidad: '$unit',
  };
}

// MG01: el dataset identifica canales lógicos, no sensores físicos.
async function lecturasPorCanal(base, canal) {
  const total = await base.readings.countDocuments(canal);
  const muestra = await buscarMuestra(
    base.readings,
    canal,
    { _id: 1, channel_id: 1, observed_at: 1, value: 1, unit: 1 },
    { observed_at: 1 },
  );
  return { parametros: canal, total, muestra };
}

// MG02: lecturas dentro del mes seleccionado.
async function lecturasPorFecha(base) {
  const filtro = fechasDeEnero();
  const total = await base.readings.countDocuments(filtro);
  const muestra = await buscarMuestra(
    base.readings,
    filtro,
    { _id: 1, observed_at: 1, source_id: 1 },
    { observed_at: 1, _id: 1 },
  );
  return { parametros: filtro, total, muestra };
}

// MG03: mínimos, máximos y promedios de las mediciones válidas de aire.
async function extremosDeAire(base) {
  return await ejecutarAgregacion(base.readings, [
    {
      $match: {
        source_id: 'MAD-AIR',
        quality_flag: 'V',
        unit_status: 'verified_dictionary',
      },
    },
    {
      $group: {
        _id: grupoPorMedicion(),
        cantidad: { $sum: 1 },
        minimo: { $min: '$value' },
        maximo: { $max: '$value' },
        promedio: { $avg: '$value' },
      },
    },
    { $sort: { '_id.tipo': 1, '_id.unidad': 1 } },
  ]);
}

// MG04: eventos generados por nuestra regla demo, no eventos oficiales.
async function eventosPorRegla(base, regla) {
  const filtro = { rule_version: regla.version };
  const total = await base.derived_events.countDocuments(filtro);
  const muestra = await buscarMuestra(
    base.derived_events,
    filtro,
    {
      _id: 1,
      measurement_id: 1,
      value: 1,
      threshold: 1,
      zone_id: 1,
      data_origin: 1,
    },
    { _id: 1 },
  );
  return { regla, total, muestra };
}

// MG05: alertas locales de replay agrupadas por zona conocida.
async function alertasPorZona(base, regla) {
  return await ejecutarAgregacion(base.alerts, [
    { $match: { zone_id: { $ne: null }, rule_version: regla.version } },
    {
      $group: {
        _id: '$zone_id',
        cantidad: { $sum: 1 },
        primera_emision: { $min: '$emitted_at' },
        ultima_emision: { $max: '$emitted_at' },
      },
    },
    { $sort: { _id: 1 } },
  ]);
}

// MG06: no incluimos lecturas sin zona en los promedios territoriales.
async function promedioPorZona(base) {
  return await ejecutarAgregacion(base.readings, [
    { $match: { zone_id: { $ne: null } } },
    {
      $group: {
        _id: { zona: '$zone_id', ...grupoPorMedicion() },
        cantidad: { $sum: 1 },
        promedio: { $avg: '$value' },
      },
    },
    {
      $sort: {
        '_id.zona': 1,
        '_id.fuente': 1,
        '_id.tipo': 1,
        '_id.unidad': 1,
      },
    },
  ]);
}

// MG07: tipo de medición, no tipo de dispositivo físico.
async function promedioPorMedicion(base) {
  return await ejecutarAgregacion(base.readings, [
    {
      $group: {
        _id: grupoPorMedicion(),
        cantidad: { $sum: 1 },
        promedio: { $avg: '$value' },
      },
    },
    { $sort: { '_id.fuente': 1, '_id.tipo': 1, '_id.unidad': 1 } },
  ]);
}

// MG08: estos accidentes son de 2026 y se consultan por separado.
async function incidentesPorCategoria(base) {
  return await ejecutarAgregacion(base.incidents, [
    { $group: { _id: '$category', cantidad: { $sum: 1 } } },
    { $sort: { _id: 1 } },
  ]);
}

// MG09: cantidad de lecturas por fuente y marca de calidad.
async function conteoPorCalidad(base) {
  return await ejecutarAgregacion(base.readings, [
    {
      $group: {
        _id: { fuente: '$source_id', calidad: '$quality_flag' },
        cantidad: { $sum: 1 },
      },
    },
    { $sort: { '_id.fuente': 1, '_id.calidad': 1 } },
  ]);
}

// MG10: combinamos fecha, fuente, calidad, umbral y zona.
async function lecturasConFiltros(base, regla) {
  const filtro = {
    ...fechasDeEnero(),
    source_id: 'MAD-TRAFFIC',
    quality_flag: 'N',
    value: { $gt: regla.threshold },
    zone_id: { $ne: null },
  };
  const total = await base.readings.countDocuments(filtro);
  const muestra = await buscarMuestra(
    base.readings,
    filtro,
    { _id: 1, zone_id: 1, value: 1, unit: 1 },
    { value: -1, _id: 1 },
  );
  return { parametros: filtro, total, muestra };
}

async function consultar(base, regla) {
  const primeraLectura = await base.readings.findOne({ source_id: 'MAD-TRAFFIC' });
  if (!primeraLectura) {
    throw new Error('Falta la segunda fuente real de tráfico');
  }

  const canal = {
    channel_id: primeraLectura.channel_id,
    source_version: primeraLectura.source_version,
  };

  const resultados = {};
  resultados.MG01 = await lecturasPorCanal(base, canal);
  resultados.MG02 = await lecturasPorFecha(base);
  resultados.MG03 = await extremosDeAire(base);
  resultados.MG04 = await eventosPorRegla(base, regla);
  resultados.MG05 = await alertasPorZona(base, regla);
  resultados.MG06 = await promedioPorZona(base);
  resultados.MG07 = await promedioPorMedicion(base);
  resultados.MG08 = await incidentesPorCategoria(base);
  resultados.MG09 = await conteoPorCalidad(base);
  resultados.MG10 = await lecturasConFiltros(base, regla);
  return resultados;
}

module.exports = {
  consultar,
  lecturasPorCanal,
  lecturasPorFecha,
  extremosDeAire,
  eventosPorRegla,
  alertasPorZona,
  promedioPorZona,
  promedioPorMedicion,
  incidentesPorCategoria,
  conteoPorCalidad,
  lecturasConFiltros,
};
