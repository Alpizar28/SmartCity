'use strict';
(async function verifyRestore() {
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
})().catch(error => { console.error(error); quit(1); });
