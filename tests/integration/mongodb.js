'use strict';
// mongosh integration program copied only into our isolated throwaway container.
async function main() {
if (process.env.SMARTCITY_TEST_PHASE === 'restore') {
  return await verifyRestore();
}
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { validator } = require('/tmp/validator.js');
const indexes = require('/tmp/indexes.js');
const queries = require('/tmp/queries.js');
const { stageReading } = require('/tmp/staging.js');
const docs = EJSON.parse(fs.readFileSync('/tmp/fixture.json', 'utf8'));
const database = db.getSiblingDB('sprint1_test');
const commandWorked = result => assert.equal(result.ok, 1);
assert.equal(database.getCollectionNames().length, 0, 'Must start in an empty test database');
commandWorked(database.createCollection('readings', {
  validator, validationLevel: 'strict', validationAction: 'error',
}));
const readings = database.readings;
for (const index of indexes) {
  const { key, ...options } = index;
  readings.createIndex(key, options);
}
const copy = doc => EJSON.parse(EJSON.stringify(doc));
function rejected(doc) {
  let code;
  try { readings.insertOne(doc); } catch (error) { code = error.code; }
  assert.equal(code, 121, 'Server must reject invalid document with validation code 121');
}

assert.equal(await stageReading(readings, database.quarantine, copy(docs[0])), 'accepted');
assert.equal(await stageReading(readings, database.quarantine, copy(docs[0])), 'duplicate');
readings.insertMany(docs.slice(1).map(copy)); // insertMany
const conflict = EJSON.parse(fs.readFileSync('/tmp/conflict.json', 'utf8'));
assert.equal(await stageReading(readings, database.quarantine, conflict), 'quarantined');
assert.equal(database.quarantine.countDocuments({}), 1);
assert.equal(readings.countDocuments({}), 3);
const [air, meteo, traffic] = docs;
const filter = queries.channelReadings(air.source_id, air.source_version, air.channel_id, 'V');
const found = readings.findOne(filter);
assert.equal(found.value, air.value);
assert.equal(found._id._bsontype, 'ObjectId');
assert.ok(found.observed_at instanceof Date);
assert.equal(readings.find(filter, { channel_id: 1, value: 1, _id: 0 }).sort({ value: -1 }).toArray().length, 1);
const start = new Date('2025-01-01T00:00:00Z');
const end = new Date('2025-02-01T00:00:00Z');
const statistics = readings.aggregate(queries.airExtrema(air.channel_id, air.source_version, start, end)).toArray();
assert.equal(statistics.length, 1);
assert.equal(statistics[0].n, 1);
assert.equal(statistics[0].minimum, air.value);
assert.equal(statistics[0].maximum, air.value);
assert.equal(statistics[0].average, air.value);
assert.equal(readings.find(queries.airRange(air.channel_id, air.source_version,
  new Date('2024-12-31T00:00:00Z'), start)).toArray().length, 0);
assert.equal(readings.aggregate(queries.qualityCounts('MAD-TRAFFIC', traffic.source_version)).toArray()[0].n, 1);
assert.equal(readings.findOne({ source_id: 'MAD-METEO' }).unit, null);
assert.equal(readings.findOne({ source_id: 'MAD-TRAFFIC' }).measurements.carga.value, 0);

let invalid = copy(air); invalid.sensor_id = 'invented'; rejected(invalid);
invalid = copy(air); invalid.observed_at = invalid.observed_at.toISOString(); rejected(invalid);
invalid = copy(air); invalid.source_version = meteo.source_version; rejected(invalid);
invalid = copy(meteo); invalid.unit = 'm/s'; rejected(invalid);
invalid = copy(traffic); delete invalid.raw_reference.member; rejected(invalid);
invalid = copy(air); invalid.schema_version = 'madrid-draft-v1'; rejected(invalid);
assert.equal(readings.countDocuments({}), 3);
assert.equal(readings.getIndexes().length, indexes.length + 1);

// CRUD demonstration affects only a separate, empty, disposable collection.
// It reuses real examples; no synthetic physical devices or historical alerts.
commandWorked(database.createCollection('crud_scratch', { validator }));
const scratch = database.crud_scratch;
scratch.insertOne(copy(air));
scratch.insertMany([copy(meteo), copy(traffic)]);
assert.equal(scratch.updateOne({ channel_id: air.channel_id }, { $set: { integration_reviewed: true } }).modifiedCount, 1);
assert.equal(scratch.updateMany({}, { $set: { integration_reviewed: true } }).matchedCount, 3);
assert.equal(scratch.deleteOne({ channel_id: air.channel_id }).deletedCount, 1);
assert.equal(scratch.countDocuments({}), 2);
scratch.drop();
assert.equal(readings.countDocuments({}), 3, 'CRUD must not change the query sample');
print(JSON.stringify({ result: 'MONGODB_INTEGRATION_PASS', version: database.version(),
  readings: 3, indexes: readings.getIndexes().length, crud_isolated: true,
  replay: 'duplicate', conflict: 'quarantined' }));
}

async function verifyRestore() {
  const assert = require('node:assert/strict');
  const crypto = require('node:crypto');
  const { stageReading } = require('/tmp/staging.js');
  const queries = require('/tmp/queries.js');
  const source = db.getSiblingDB('sprint1_test');
  const restored = db.getSiblingDB('sprint1_restore');
  function canonical(value) {
    if (Array.isArray(value)) return value.map(canonical);
    if (value !== null && typeof value === 'object') {
      return Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])]));
    }
    return value;
  }
  function snapshot(database) {
    return JSON.stringify(canonical(EJSON.serialize(database.getCollectionInfos()
      .sort((a, b) => a.name.localeCompare(b.name)).map(info => ({
        name: info.name, type: info.type, options: info.options,
        indexes: database.getCollection(info.name).getIndexes().map(index => {
          const { ns, ...logical } = index;
          return logical;
        }).sort((a, b) => a.name.localeCompare(b.name)),
        documents: database.getCollection(info.name).find().sort({ _id: 1 }).toArray(),
      })), { relaxed: false })));
  }
  const original = snapshot(source);
  assert.equal(snapshot(restored), original, 'Documents, BSON types, options and indexes must survive restore');
  assert.equal(restored.readings.countDocuments({}), 3);
  assert.equal(restored.quarantine.countDocuments({}), 1);
  const air = restored.readings.findOne({ source_id: 'MAD-AIR' });
  assert.ok(air.observed_at instanceof Date);
  const incoming = { ...air }; delete incoming._id;
  assert.equal(await stageReading(restored.readings, restored.quarantine, incoming), 'duplicate');
  const extrema = restored.readings.aggregate(queries.airExtrema(air.channel_id, air.source_version,
    new Date('2025-01-01T00:00:00Z'), new Date('2025-02-01T00:00:00Z'))).toArray();
  assert.equal(extrema[0].average, air.value);
  let rejection;
  try { restored.readings.insertOne({ ...incoming, sensor_id: 'invented' }); }
  catch (error) { rejection = error.code; }
  assert.equal(rejection, 121, 'Restored validator must still enforce schema');
  assert.equal(snapshot(source), original, 'Restore checks must not modify source');
  assert.equal(snapshot(restored), original, 'Replay and rejected input must not change restored data');
  print(JSON.stringify({ result: 'MONGODB_RESTORE_PASS', readings: 3, quarantine: 1,
    logical_sha256: crypto.createHash('sha256').update(original).digest('hex'),
    indexes_options_bson_equal: true }));
}

main().catch(error => { console.error(error); quit(1); });
