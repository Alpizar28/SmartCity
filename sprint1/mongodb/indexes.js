'use strict';

// Proposed specifications only. No createIndex calls, no network side effects.
// Canonical scalar staging_key encodes the original tuple, NOT UTC or a new
// scientific identity. Never place a unique multikey index on source_key itself.
module.exports = [
  { key: { staging_key: 1 }, name: 'unique_staging_tuple', unique: true },
  { key: { source_id: 1, source_version: 1, channel_id: 1 }, name: 'source_channel' },
  { key: { channel_id: 1, quality_flag: 1 }, name: 'channel_quality' },
  { key: { measurement_type: 1, unit_status: 1 }, name: 'variable_evidence' },
  { key: { observed_at: 1 }, name: 'documented_air_time',
    partialFilterExpression: { source_id: 'MAD-AIR', timestamp_status: 'documented_local' } },
];
