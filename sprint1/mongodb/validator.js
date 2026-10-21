'use strict';

// Pure proposal. Importing this file NEVER creates a collection or connects.
// Application validation + catalog references remain mandatory before insertion.
const text = { bsonType: 'string', minLength: 1 };
const nullableText = { bsonType: ['string', 'null'] };
const schema = {
  bsonType: 'object',
  required: ['source_id', 'source_version', 'station_id', 'channel_id', 'source_key',
    'measurement_type', 'value', 'original_time', 'original_timezone',
    'timestamp_role', 'timestamp_status', 'quality_flag', 'unit_status',
    'raw_reference', 'data_origin', 'schema_version', 'catalog_version',
    'transformation_method', 'payload_hash', 'staging_key'],
  properties: {
    // _id is a Mongo-generated staging locator, NEVER a measurement identity.
    _id: { bsonType: 'objectId' },
    measurement_id: { bsonType: 'null' },
    sensor_id: { bsonType: 'null' },
    organization_id: { bsonType: 'null' },
    user_id: { bsonType: 'null' },
    installation_date: { bsonType: 'null' },
    administrative_status: { bsonType: 'null' },
    source_id: { enum: ['MAD-AIR', 'MAD-METEO', 'MAD-TRAFFIC'] },
    source_version: { bsonType: 'string', pattern: '^[0-9a-f]{64}$' },
    station_id: { bsonType: 'string', pattern: '^station:[0-9a-f]{64}$' },
    channel_id: { bsonType: 'string', pattern: '^channel:[0-9a-f]{64}$' },
    source_key: { bsonType: 'array', minItems: 1 },
    measurement_type: text,
    value: { bsonType: ['double', 'int', 'long', 'decimal'] },
    unit: nullableText,
    candidate_unit: nullableText,
    unit_status: text,
    zone_id: nullableText,
    original_time: text,
    original_timezone: { enum: ['Europe/Madrid'] },
    timestamp_role: text,
    timestamp_status: text,
    observed_at: { bsonType: ['date', 'null'] },
    quality_flag: text,
    raw_reference: {
      bsonType: 'object', required: ['path', 'sha256', 'row', 'column'],
      properties: {
        path: text, sha256: { bsonType: 'string', pattern: '^[0-9a-f]{64}$' },
        row: { bsonType: ['int', 'long'], minimum: 1 }, column: text, member: text,
      },
    },
    data_origin: { enum: ['observed'] },
    schema_version: { enum: ['madrid-draft-v1-frozen'] },
    catalog_version: text,
    transformation_method: { enum: ['sprint1-local-core-v1'] },
    payload_hash: { bsonType: 'string', pattern: '^payload:[0-9a-f]{64}$' },
    staging_key: text,
    interval_minutes: { bsonType: ['int', 'long', 'null'], minimum: 1 },
    element_type: nullableText,
    measurements: { bsonType: ['object', 'null'] },
  },
};

const validator = { $and: [
  { $jsonSchema: schema },
  { $expr: { $eq: ['$source_version', '$raw_reference.sha256'] } },
  { $or: [
    { source_id: 'MAD-AIR', timestamp_role: 'hour_end', timestamp_status: 'documented_local',
      unit: { $type: 'string' }, unit_status: 'verified_dictionary', zone_id: null },
    { source_id: 'MAD-METEO', timestamp_role: 'hour_end',
      timestamp_status: 'assumed_same_H_format_pending_dictionary',
      unit: null, unit_status: 'pending_dictionary', zone_id: null },
    { source_id: 'MAD-TRAFFIC', timestamp_role: 'publisher_label',
      timestamp_status: 'assumed_local_label_pending_provider_confirmation',
      unit: 'veh/h', unit_status: 'documented_phase1_dictionary',
      element_type: { $type: 'string' }, measurements: { $type: 'object' },
      interval_minutes: { $gt: 0 }, 'raw_reference.member': { $type: 'string' } },
  ] },
] };

module.exports = { schema, validator };
