'use strict';
const VERSION = 'smartcity-academic-v1';
const COLECCIONES = ['sensor_types', 'sensors', 'readings', 'dynamic_information'];

function canonico(v) {
  if (v && typeof v.toISOString === 'function') return JSON.stringify(v.toISOString());
  if (Array.isArray(v)) return '[' + v.map(canonico).join(',') + ']';
  if (v && typeof v === 'object') return '{' + Object.keys(v).sort()
    .map(k => JSON.stringify(k) + ':' + canonico(v[k])).join(',') + '}';
  return JSON.stringify(v);
}

function comprobar(condicion, mensaje) {
  if (!condicion) throw new Error(mensaje);
}

function comprobarAislamiento(nombre) {
  comprobar(/^smartcity_academic_[a-f0-9]{16}$/.test(nombre), 'Base académica exclusiva requerida');
}

// Las referencias entre colecciones se comprueban explícitamente; no son FK BSON.
function comprobarReferencias(datos) {
  const map = {};
  for (const nombre of COLECCIONES) {
    comprobar(Array.isArray(datos[nombre]), 'Colección ausente: ' + nombre);
    map[nombre] = new Map();
    for (const d of datos[nombre]) {
      comprobar(d.data_origin === 'synthetic' && d.schema_version === VERSION, 'Procedencia académica requerida');
      comprobar(typeof d._id === 'string' && !map[nombre].has(d._id), 'Identificador duplicado o inválido');
      map[nombre].set(d._id, d);
    }
  }
  for (const s of datos.sensors) {
    comprobar(s.sensor_id === s._id, 'Identidad de sensor contradictoria');
    comprobar(map.sensor_types.has(s.sensor_type), 'Tipo de sensor inexistente');
  }
  const natural = new Set();
  const unidades = { 'demo:temperature': 'degC', 'demo:humidity': '%' };
  for (const r of datos.readings) {
    comprobar(map.sensors.has(r.sensor_id), 'Sensor inexistente');
    comprobar(unidades[r.measurement_type] === r.unit, 'Magnitud/unidad incompatible');
    comprobar(typeof r.value === 'number' && Number.isFinite(r.value), 'Valor no finito');
    const key = JSON.stringify([r.sensor_id, r.observed_at, r.measurement_type, r.unit]);
    comprobar(!natural.has(key), 'Clave natural duplicada');
    natural.add(key);
  }
  const revisiones = new Set();
  for (const n of datos.dynamic_information) {
    comprobar(map.sensors.has(n.subject_sensor_id), 'Sujeto narrativo inexistente');
    comprobar(typeof n.body === 'string' && n.body.trim().length >= 30, 'Texto narrativo requerido');
    const key = JSON.stringify([n.subject_sensor_id, n.revision]);
    comprobar(!revisiones.has(key), 'Revisión duplicada');
    revisiones.add(key);
  }
}

function esquema(required, properties) {
  return { $jsonSchema: { bsonType: 'object', required: ['_id', 'data_origin', 'schema_version', ...required],
    properties: { _id: { bsonType: 'string' }, data_origin: { enum: ['synthetic'] },
      schema_version: { enum: [VERSION] }, ...properties } } };
}
function validadores() {
  return {
    sensor_types: esquema(['name', 'category_id'], { name: { bsonType: 'string' }, category_id: { bsonType: 'string' } }),
    sensors: { $and: [esquema(['sensor_id', 'name', 'sensor_type', 'provenance'], {
      sensor_id: { bsonType: 'string' }, name: { bsonType: 'string' }, sensor_type: { bsonType: 'string' },
      provenance: { bsonType: 'object' } }), { $expr: { $eq: ['$_id', '$sensor_id'] } }] },
    readings: { $and: [esquema(['sensor_id', 'measurement_type', 'unit', 'value', 'observed_at'], {
      sensor_id: { bsonType: 'string' }, measurement_type: { bsonType: 'string' }, unit: { bsonType: 'string' },
      observed_at: { bsonType: 'date' }, value: { bsonType: ['double', 'int', 'long', 'decimal'] } }),
    { $expr: { $and: [{ $gt: ['$value', -Infinity] }, { $lt: ['$value', Infinity] }] } }] },
    dynamic_information: esquema(['subject_sensor_id', 'revision', 'created_at', 'body', 'attributes'], {
      subject_sensor_id: { bsonType: 'string' }, revision: { bsonType: 'int', minimum: 1 },
      created_at: { bsonType: 'date' }, body: { bsonType: 'string', minLength: 30 }, attributes: { bsonType: 'object' } }),
  };
}

async function crearModelo(base) {
  comprobarAislamiento(base.getName());
  comprobar((await base.getCollectionNames()).length === 0, 'La base debe ser nueva y vacía');
  for (const [nombre, validator] of Object.entries(validadores())) {
    await base.createCollection(nombre, { validator, validationAction: 'error', validationLevel: 'strict' });
  }
  await base.readings.createIndex({ sensor_id: 1, observed_at: 1, measurement_type: 1, unit: 1 }, { unique: true });
  await base.dynamic_information.createIndex({ subject_sensor_id: 1, revision: 1 }, { unique: true });
}

// Un replay compara el documento completo y nunca convierte un conflicto en UPDATE.
async function cargar(base, datos) {
  comprobarAislamiento(base.getName());
  comprobarReferencias(datos);
  for (const nombre of COLECCIONES) {
    for (const d of datos[nombre]) {
      const existente = await base.getCollection(nombre).findOne({ _id: d._id });
      if (existente) comprobar(canonico(existente) === canonico(d),
        'Conflicto de replay: ' + nombre + '/' + d._id);
      else await base.getCollection(nombre).insertOne(d);
    }
  }
}

module.exports = { COLECCIONES, comprobarAislamiento, comprobarReferencias, crearModelo, cargar };
