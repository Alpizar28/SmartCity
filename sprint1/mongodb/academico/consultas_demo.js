'use strict';

// El ámbito es una base académica sintética, independiente de Madrid v2.
async function buscarOrdenado(collection, filter, order) {
  let cursor = await collection.find(filter);
  cursor = await cursor.sort(order);
  return await cursor.toArray();
}
async function lecturasPorSensor(base, sensorId) {
  if (typeof sensorId !== 'string' || !sensorId.trim()) {
    throw new Error('Se requiere sensor_id explícito');
  }
  return await buscarOrdenado(base.readings, { sensor_id: sensorId, data_origin: 'synthetic' },
    { observed_at: 1, _id: 1 });
}

async function promediosPorTipo(base) {
  const cursor = await base.readings.aggregate([
    { $match: { data_origin: 'synthetic' } },
    { $lookup: { from: 'sensors', localField: 'sensor_id', foreignField: '_id', as: 'sensor' } },
    { $unwind: '$sensor' },
    { $lookup: { from: 'sensor_types', localField: 'sensor.sensor_type', foreignField: '_id', as: 'device_type' } },
    { $unwind: '$device_type' },
    { $group: { _id: { sensor_type: '$device_type._id', measurement_type: '$measurement_type', unit: '$unit' },
      cantidad: { $sum: 1 }, promedio: { $avg: '$value' } } },
    { $sort: { '_id.sensor_type': 1, '_id.measurement_type': 1, '_id.unit': 1 } },
  ]);
  return await cursor.toArray();
}

async function informacionDinamica(base, sensorId) {
  return {
    texto: await buscarOrdenado(base.dynamic_information, { body: { $regex: 'vibración', $options: 'i' } }, { _id: 1 }),
    atributo: await buscarOrdenado(base.dynamic_information, { 'attributes.maintenance': { $exists: true } }, { _id: 1 }),
    revisiones: await buscarOrdenado(base.dynamic_information, { subject_sensor_id: sensorId }, { revision: 1 }),
  };
}

module.exports = { lecturasPorSensor, promediosPorTipo, informacionDinamica };
