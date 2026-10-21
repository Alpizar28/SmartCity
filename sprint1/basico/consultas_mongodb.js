// Ejecutar con mongosh seleccionando una base LOCAL preparada.
// Solo consultas: este archivo no inserta, actualiza ni elimina documentos.
const base = db;

print('1. Primeras lecturas');
printjson(base.readings.find({}, { channel_id: 1, value: 1, unit: 1 })
  .sort({ original_time: 1, _id: 1 }).limit(20).toArray());

print('2. Cantidad de lecturas de aire');
print(base.readings.countDocuments({ source_id: 'MAD-AIR' }));

print('3. Lecturas válidas de aire, ordenadas por valor');
printjson(base.readings.find({ source_id: 'MAD-AIR', quality_flag: 'V' },
  { channel_id: 1, source_version: 1, value: 1, unit: 1 }).sort({ value: -1 }).limit(20).toArray());

print('4. Conteo por fuente, versión y calidad');
printjson(base.readings.aggregate([
  { $group: { _id: { fuente: '$source_id', version: '$source_version', calidad: '$quality_flag' },
    cantidad: { $sum: 1 } } },
  { $sort: { '_id.fuente': 1, '_id.version': 1, '_id.calidad': 1 } },
  { $limit: 20 },
]).toArray());

// Usar un canal REAL presente en la base, sin escribir un ID inventado.
const primeraLectura = base.readings.findOne({ source_id: 'MAD-AIR', quality_flag: 'V',
  timestamp_status: 'documented_local', unit_status: 'verified_dictionary' });

if (primeraLectura === null) {
  print('No hay aire válido. No se muestran resultados inventados.');
} else {
  const canal = primeraLectura.channel_id;
  const version = primeraLectura.source_version;
  print('5. Lecturas del canal y snapshot elegidos');
  printjson(base.readings.find({ channel_id: canal, source_version: version })
    .sort({ original_time: 1, _id: 1 }).limit(20).toArray());

  print('6. Rango de fechas de aire: inicio incluido, fin excluido');
  const filtro = { source_id: 'MAD-AIR', channel_id: canal, source_version: version,
    timestamp_status: 'documented_local', unit_status: 'verified_dictionary', quality_flag: 'V',
    observed_at: { $gte: new Date('2025-01-01T00:00:00Z'), $lt: new Date('2025-02-01T00:00:00Z') } };
  printjson(base.readings.find(filtro).sort({ observed_at: 1, _id: 1 }).limit(20).toArray());

  print('7. Mínimo, máximo y promedio del canal; unidades separadas');
  printjson(base.readings.aggregate([
    { $match: filtro },
    { $group: { _id: { variable: '$measurement_type', unidad: '$unit' },
      cantidad: { $sum: 1 }, minimo: { $min: '$value' },
      maximo: { $max: '$value' }, promedio: { $avg: '$value' } } },
  ]).toArray());
}

// Estas consultas no acreditan sensores físicos, alertas, eventos ni geografía.
