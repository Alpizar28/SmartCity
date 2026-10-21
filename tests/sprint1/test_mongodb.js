'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { schema, validator } = require('../../sprint1/mongodb/validator');
const indexes = require('../../sprint1/mongodb/indexes');
const queries = require('../../sprint1/mongodb/queries');
const fs = require('node:fs');
const path = require('node:path');
const historical = JSON.parse(fs.readFileSync(path.join(__dirname,
  '../../research/datasets/results/phase5/examples.extjson'), 'utf8'));
const air = historical[0];
const start = new Date('2025-01-01T00:00:00Z');
const end = new Date('2025-02-01T00:00:00Z');

test('BSON proposal requires traceability and a local ObjectId, not scientific ID', () => {
  assert.equal(schema.properties._id.bsonType, 'objectId');
  assert.equal(schema.properties.sensor_id.bsonType, 'null');
  assert.deepEqual(schema.properties.observed_at.bsonType, ['date', 'null']);
  assert.ok(schema.required.includes('payload_hash'));
  assert.ok(schema.required.includes('source_key'));
  assert.deepEqual(validator.$and[1].$expr.$eq, ['$source_version', '$raw_reference.sha256']);
});

test('only the scalar original staging tuple is unique, never UTC or geography', () => {
  assert.deepEqual(indexes.filter(index => index.unique).map(index => index.key), [{ staging_key: 1 }]);
  assert.ok(!JSON.stringify(indexes).includes('2dsphere'));
  assert.equal(indexes.find(i => i.name === 'documented_air_time')
    .partialFilterExpression.source_id, 'MAD-AIR');
});

test('staging propagates validation/network failures without treating them as duplicates', async () => {
  const { stageReading } = require('../../sprint1/mongodb/staging');
  const failure = Object.assign(new Error('validation failure'), { code: 121 });
  const readings = { insertOne: async () => { throw failure; } };
  await assert.rejects(stageReading(readings, {}, { staging_key: 'key', payload_hash: 'hash' }), /validation failure/);
  await assert.rejects(stageReading(readings, {}, {}), /validated_DTO_required/);
});

test('staging fails closed on unrelated duplicate keys and failed quarantine writes', async () => {
  const { stageReading } = require('../../sprint1/mongodb/staging');
  const duplicate = Object.assign(new Error('duplicate'), { code: 11000 });
  const input = { staging_key: 'key', payload_hash: 'new' };
  const readings = { insertOne: async () => { throw duplicate; }, findOne: async () => null };
  await assert.rejects(stageReading(readings, {}, input), /duplicate/);
  readings.findOne = async () => ({ _id: 'local', payload_hash: 'old' });
  const quarantine = { insertOne: async () => { throw new Error('quarantine unavailable'); } };
  await assert.rejects(stageReading(readings, quarantine, input), /quarantine unavailable/);
});

test('channel builder scopes snapshot and rejects operator injection', () => {
  const query = queries.channelReadings(air.source_id, air.source_version, air.channel_id, 'V');
  assert.equal(query.channel_id, air.channel_id);
  assert.equal(query.source_version, air.source_version);
  assert.throws(() => queries.channelReadings(air.source_id, air.source_version, { $ne: null }, 'V'));
  assert.throws(() => queries.channelReadings(air.source_id, { $ne: null }, air.channel_id, 'V'));
  assert.throws(() => queries.channelReadings(air.source_id, air.source_version, air.channel_id, { $gt: '' }));
});

test('date builder requires Date objects and valid nonempty half-open ranges', () => {
  const query = queries.airRange(air.channel_id, air.source_version, start, end);
  assert.equal(query.observed_at.$gte.getTime(), start.getTime());
  assert.equal(query.observed_at.$lt.getTime(), end.getTime());
  assert.notEqual(query.observed_at.$gte, start);
  assert.equal(query.source_id, 'MAD-AIR');
  assert.equal(query.timestamp_status, 'documented_local');
  assert.throws(() => queries.airRange(air.channel_id, air.source_version, end, start));
  assert.throws(() => queries.airRange(air.channel_id, air.source_version, start, start));
  assert.throws(() => queries.airRange(air.channel_id, air.source_version, '2025-01-01', end));
  assert.throws(() => queries.airRange(air.channel_id, air.source_version, new Date('invalid'), end));
});

test('extrema group by variable/unit and only use valid documented air', () => {
  const pipeline = queries.airExtrema(air.channel_id, air.source_version, start, end);
  assert.equal(pipeline[0].$match.quality_flag, 'V');
  assert.equal(pipeline[0].$match.unit_status, 'verified_dictionary');
  assert.deepEqual(pipeline[1].$group._id, { variable: '$measurement_type', unit: '$unit' });
});

test('quality aggregation counts only one source snapshot; no physical averaging', () => {
  const pipeline = queries.qualityCounts('MAD-METEO', historical[1].source_version);
  assert.equal(pipeline[0].$match.source_id, 'MAD-METEO');
  assert.deepEqual(pipeline[1].$group.n, { $sum: 1 });
  assert.ok(!JSON.stringify(pipeline).includes('$avg'));
  assert.throws(() => queries.qualityCounts('unknown', air.source_version));
});
