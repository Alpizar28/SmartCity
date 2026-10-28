'use strict';

// Solo lo invoca validar_v2.py en su contenedor aislado. Sin conexiones remotas.
if (!/^smartcity_v2_[a-f0-9]{12}$/.test(db.getName())) throw new Error('Base desechable requerida');
const fs = require('fs');
const crypto = require('crypto');
const { StringDecoder } = require('string_decoder');
const { consultar } = require('/tmp/consultas_mongodb_v2.js');
const informe = JSON.parse(fs.readFileSync('/inputs/preparation.json', 'utf8'));
const regla = informe.demo_rule;

function comprobar(condicion, mensaje) {
  if (!condicion) throw new Error(mensaje);
}

function* leerLineas(ruta) {
  const fd = fs.openSync(ruta, 'r');
  const bloque = Buffer.alloc(65536);
  const decoder = new StringDecoder('utf8'); // No cortar una tilde entre dos bloques.
  let pendiente = '';
  try {
    let cantidad;
    while ((cantidad = fs.readSync(fd, bloque, 0, bloque.length, null)) > 0) {
      pendiente += decoder.write(bloque.subarray(0, cantidad));
      let fin;
      while ((fin = pendiente.indexOf('\n')) >= 0) {
        const linea = pendiente.slice(0, fin);
        pendiente = pendiente.slice(fin + 1);
        if (linea) yield linea;
      }
    }
    pendiente += decoder.end();
    if (pendiente) yield pendiente;
  } finally { fs.closeSync(fd); }
}

function canonico(valor) {
  if (valor instanceof Date) return canonico({ $date: valor.toISOString().replace('.000Z', 'Z') });
  if (Array.isArray(valor)) return '[' + valor.map(canonico).join(',') + ']';
  if (valor && typeof valor === 'object') return '{' + Object.keys(valor).sort()
    .map(k => JSON.stringify(k) + ':' + canonico(valor[k])).join(',') + '}';
  return JSON.stringify(valor);
}

function insertarLecturas(replay) {
  let lote = [], leidas = 0;
  function guardar() {
    if (!lote.length) return;
    if (!replay) db.readings.insertMany(lote, { ordered: true });
    else {
      const existentes = new Map(db.readings.find({ _id: { $in: lote.map(d => d._id) } })
        .toArray().map(d => [d._id, d]));
      for (const documento of lote) {
        comprobar(existentes.has(documento._id), 'Falta lectura durante replay');
        comprobar(canonico(existentes.get(documento._id)) === canonico(documento),
          'Conflicto de contenido: no se sobrescribe la lectura');
      }
    }
    leidas += lote.length;
    lote = [];
  }
  for (const linea of leerLineas('/inputs/accepted.extjsonl')) {
    lote.push(EJSON.parse(linea));
    if (lote.length === 1000) guardar();
  }
  guardar();
  return leidas;
}

db.createCollection('readings', { validationAction: 'error', validationLevel: 'strict',
  validator: { $and: [
    { $jsonSchema: { bsonType: 'object', required: ['_id', 'measurement_id', 'source_id',
      'source_version', 'channel_id', 'station_id', 'observed_at', 'value', 'unit',
      'quality_flag', 'payload_hash', 'raw_reference', 'schema_version', 'catalog_version',
      'data_origin', 'sensor_id', 'zone_scope', 'integration_sample_count'], properties: {
      _id: { bsonType: 'string' }, measurement_id: { bsonType: 'string' },
      observed_at: { bsonType: 'date' }, value: { bsonType: ['double', 'int', 'long', 'decimal'] },
      sensor_id: { bsonType: 'null' }, schema_version: { enum: ['madrid-draft-v2'] },
      catalog_version: { enum: ['madrid-draft-v2'] }, data_origin: { enum: ['observed'] },
      source_id: { enum: ['MAD-AIR', 'MAD-TRAFFIC'] },
      integration_sample_count: { bsonType: ['int', 'long', 'null'] },
    } } },
    { $expr: { $and: [ { $eq: ['$_id', '$measurement_id'] },
      { $eq: ['$source_version', '$raw_reference.sha256'] },
      { $gt: ['$value', -Infinity] }, { $lt: ['$value', Infinity] } ] } },
    { $or: [
      { source_id: 'MAD-AIR', quality_flag: 'V', timestamp_status: 'documented_local', integration_sample_count: null },
      { source_id: 'MAD-TRAFFIC', quality_flag: 'N', element_type: { $in: ['URB', 'M30'] },
        value: { $gte: 0 }, interval_minutes: 15, integration_sample_count: { $gt: 0 },
        timestamp_role: 'publisher_label', timestamp_status: 'publisher_confirmed_local' },
    ] },
  ] } });
db.readings.createIndex({ channel_id: 1, observed_at: 1, timestamp_role: 1 }, { unique: true });
db.readings.createIndex({ source_id: 1, measurement_type: 1, observed_at: 1 });
db.readings.createIndex({ zone_id: 1, measurement_type: 1 });
const leidas = insertarLecturas(false);
comprobar(leidas === informe.accepted, 'Conteo importado incorrecto');
comprobar(insertarLecturas(true) === leidas && db.readings.countDocuments({}) === leidas,
  'El replay modificó el volumen');

// Incidentes reales anonimizados; no mezclar 2026 con las lecturas de enero 2025.
let loteIncidentes = [];
for (const linea of leerLineas('/inputs/incidents.extjsonl')) loteIncidentes.push(JSON.parse(linea));
db.createCollection('incidents', { validator: { $jsonSchema: { bsonType: 'object',
  required: ['_id', 'category', 'reported_date', 'source_id', 'source_version', 'person_fields_removed'],
  properties: { source_id: { enum: ['MAD-CRASH'] }, person_fields_removed: { enum: [true] },
    reported_date: { bsonType: 'string', pattern: '^2026-' } } } }, validationAction: 'error' });
db.incidents.insertMany(loteIncidentes);
db.incidents.createIndex({ category: 1 });
const admin = JSON.parse(fs.readFileSync('/inputs/administrative_seed.json', 'utf8'));
for (const [coleccion, clave] of [['organizations', 'organization_id'], ['users', 'user_id'], ['sensors', 'sensor_id']]) {
  db.getCollection(coleccion).insertMany(admin[coleccion].map(d => ({ _id: d[clave], ...d })));
}

// Emitir eventos y alertas locales de DEMOSTRACIÓN, no alertas oficiales históricas.
const instante = new Date();
db.createCollection('derived_events', { validationAction: 'error', validator: { $jsonSchema: {
  bsonType: 'object', required: ['measurement_id', 'rule_version', 'threshold', 'data_origin', 'official_event'],
  properties: { data_origin: { enum: ['derived'] }, official_event: { enum: [false] } },
} } });
db.createCollection('alerts', { validationAction: 'error', validator: { $jsonSchema: {
  bsonType: 'object', required: ['event_id', 'emitted_at', 'data_origin', 'delivery', 'replay', 'official_alert'],
  properties: { emitted_at: { bsonType: 'date' }, data_origin: { enum: ['derived'] },
    delivery: { enum: ['local_collection_only'] }, replay: { enum: [true] }, official_alert: { enum: [false] } },
} } });
function generarDerivados() {
  db.readings.aggregate([
    { $match: { source_id: 'MAD-TRAFFIC', quality_flag: 'N', value: { $gt: regla.threshold } } },
    { $project: { _id: { $concat: [regla.version + ':gt' + regla.threshold + ':', '$_id'] },
      measurement_id: '$_id', value: 1, unit: 1, zone_id: 1, zone_scope: 1, observed_at: 1,
      source_version: 1, reading_payload_hash: '$payload_hash',
      rule_version: { $literal: regla.version }, threshold: { $literal: regla.threshold },
      severity: { $literal: 'demo_high_intensity' },
      data_origin: { $literal: 'derived' }, official_event: { $literal: false },
      generated_at: { $literal: instante } } },
    { $merge: { into: 'derived_events', on: '_id', whenMatched: 'keepExisting', whenNotMatched: 'insert' } },
  ]).toArray();
  db.derived_events.aggregate([
    { $match: { zone_id: { $ne: null } } },
    { $project: { _id: { $concat: ['alert:', '$_id'] }, event_id: '$_id',
      zone_id: 1, zone_scope: 1, rule_version: 1, observed_at: 1,
      emitted_at: { $literal: instante }, data_origin: { $literal: 'derived' },
      replay: { $literal: true }, delivery: { $literal: 'local_collection_only' },
      official_alert: { $literal: false } } },
    { $merge: { into: 'alerts', on: '_id', whenMatched: 'keepExisting', whenNotMatched: 'insert' } },
  ]).toArray();
}
generarDerivados();
const eventos = db.derived_events.countDocuments({});
const alertas = db.alerts.countDocuments({});
generarDerivados();
comprobar(db.derived_events.countDocuments({}) === eventos && db.alerts.countDocuments({}) === alertas,
  'Replay de eventos/alertas duplicó documentos');
comprobar(eventos === informe.expected_events, 'Eventos distintos del cálculo del ETL');
comprobar(alertas === informe.expected_alerts_with_zone, 'Alertas distintas del cálculo del ETL');
comprobar(eventos > 0 && alertas > 0, 'La demostración no tiene eventos/alertas que mostrar');
db.derived_events.createIndex({ rule_version: 1, observed_at: 1 });
db.alerts.createIndex({ zone_id: 1, emitted_at: 1 });

const resultados = consultar(db, regla);
comprobar(Object.keys(resultados).length === 10, 'Faltan consultas MG01-MG10');
const hash = crypto.createHash('sha256');
for (const d of db.readings.find({}, { measurement_id: 1, payload_hash: 1 }).sort({ _id: 1 })) {
  hash.update(JSON.stringify([d.measurement_id, d.payload_hash]) + '\n');
}
print('V2_MONGO_RESULT=' + JSON.stringify({ count: leidas,
  count_by_source: db.readings.aggregate([{ $group: { _id: '$source_id', cantidad: { $sum: 1 } } }]).toArray(),
  ids_payload_sha256: hash.digest('hex'), incidents: db.incidents.countDocuments({}),
  events: eventos, alerts: alertas, replay_verified: true,
  results: resultados, zone_scope: informe.zone_scope,
  notice: 'Events and alerts are a derived classroom replay, not official warnings. Incident year: 2026.' }));
