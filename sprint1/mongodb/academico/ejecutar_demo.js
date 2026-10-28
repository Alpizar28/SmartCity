'use strict';
const fs = require('fs');
const { COLECCIONES, comprobarAislamiento, comprobarReferencias, crearModelo, cargar } = require(ACADEMIC_DIR + '/modelo_demo.js');
const { lecturasPorSensor, promediosPorTipo, informacionDinamica } = require(ACADEMIC_DIR + '/consultas_demo.js');
const copiar = d => EJSON.parse(EJSON.stringify(d));
function comprobar(c, m) { if (!c) throw new Error(m); }

async function ejecutar() {
  comprobarAislamiento(db.getName());
  comprobar(Number((await db.serverStatus()).pid) === EXPECTED_PID, 'El servidor no pertenece al ejecutor');
  const datos = EJSON.parse(fs.readFileSync(ACADEMIC_DIR + '/fixtures.json', 'utf8'));
  await crearModelo(db);
  await cargar(db, datos);
  async function snapshot() {
    const result = {};
    for (const n of COLECCIONES) result[n] = await db.getCollection(n).find().sort({ _id: 1 }).toArray();
    return result;
  }
  const inicial = await snapshot();
  comprobarReferencias(inicial);
  await cargar(db, datos);
  comprobar(EJSON.stringify(inicial) === EJSON.stringify(await snapshot()), 'Replay alteró documentos');
  const negativos = {};
  async function rechazar(nombre, operacion, criterio) {
    let error;
    try { await operacion(); } catch (e) { error = e; }
    comprobar(error && criterio(error), 'Rechazo incorrecto: ' + nombre);
    comprobar(EJSON.stringify(inicial) === EJSON.stringify(await snapshot()), 'El rechazo alteró la base: ' + nombre);
    negativos[nombre] = { rejected: true, code: error.code || null, message: String(error.message) };
  }
  await rechazar('missing_sensor', async () => {
    const d = copiar(datos); d.readings[0].sensor_id = 'academic:nonexistent'; await cargar(db, d);
  }, e => /Sensor inexistente/.test(e.message));
  await rechazar('missing_type', async () => {
    const d = copiar(datos); d.sensors[0].sensor_type = 'academic:nonexistent'; await cargar(db, d);
  }, e => /Tipo de sensor inexistente/.test(e.message));
  await rechazar('missing_narrative_subject', async () => {
    const d = copiar(datos); d.dynamic_information[0].subject_sensor_id = 'academic:nonexistent'; await cargar(db, d);
  }, e => /Sujeto narrativo inexistente/.test(e.message));
  await rechazar('unit_mismatch', async () => {
    const d = copiar(datos); d.readings[0].unit = '%'; await cargar(db, d);
  }, e => /Magnitud\/unidad incompatible/.test(e.message));
  await rechazar('replay_conflict', async () => {
    const d = copiar(datos); d.readings[0].value += 1; await cargar(db, d);
  }, e => /Conflicto de replay/.test(e.message));
  await rechazar('observed_origin', async () => {
    await db.readings.insertOne({ ...copiar(datos.readings[0]), _id: 'academic:bad-origin', data_origin: 'observed' });
  }, e => e.code === 121);
  await rechazar('non_bson_date', async () => {
    await db.readings.insertOne({ ...copiar(datos.readings[0]), _id: 'academic:bad-date', observed_at: '2026-10-28' });
  }, e => e.code === 121);
  await rechazar('duplicate_natural_key', async () => {
    await db.readings.insertOne({ ...copiar(datos.readings[0]), _id: 'academic:duplicate' });
  }, e => e.code === 11000);
  await rechazar('duplicate_revision', async () => {
    await db.dynamic_information.insertOne({ ...copiar(datos.dynamic_information[0]), _id: 'academic:duplicate' });
  }, e => e.code === 11000);
  await rechazar('missing_explicit_sensor', () => lecturasPorSensor(db), e => /sensor_id explícito/.test(e.message));
  await rechazar('official_database_guard', () => comprobarAislamiento('smartcity'), e => /exclusiva/.test(e.message));
  await rechazar('v2_database_guard', () => comprobarAislamiento('smartcity_v2_012345abcdef'), e => /exclusiva/.test(e.message));
  await rechazar('reuse_database', () => crearModelo(db), e => /nueva y vacía/.test(e.message));
  const results = {
    MG01: await lecturasPorSensor(db, datos.mg01_sensor_id),
    MG01_unknown: await lecturasPorSensor(db, 'academic:nonexistent'),
    MG07: await promediosPorTipo(db),
    dynamic: await informacionDinamica(db, datos.mg01_sensor_id),
  };
  const metadata = {};
  for (const n of COLECCIONES) metadata[n] = {
    count: await db.getCollection(n).countDocuments({}),
    options: (await db.getCollectionInfos({ name: n }))[0].options,
    indexes: await db.getCollection(n).getIndexes(),
  };
  print('ACADEMIC_RESULT=' + JSON.stringify({ status: 'PASS', scope: 'synthetic_academic_only',
    version: (await db.adminCommand({ buildInfo: 1 })).version, database: db.getName(),
    replay_verified: true, negatives: negativos, results, metadata, documents: await snapshot() }));
}
ejecutar().catch(e => { console.error(e.stack || e); quit(1); });
