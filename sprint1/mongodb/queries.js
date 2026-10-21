'use strict';

// Builders accept scalar allowlisted parameters, never arbitrary operators.
function string(value, name) {
  if (typeof value !== 'string' || !value.trim()) throw new TypeError(name);
  return value;
}
function source(value) {
  if (!['MAD-AIR', 'MAD-METEO', 'MAD-TRAFFIC'].includes(value)) throw new TypeError('source');
  return value;
}
function channel(value) {
  string(value, 'channel');
  if (!/^channel:[0-9a-f]{64}$/.test(value)) throw new TypeError('channel');
  return value;
}
function version(value) {
  string(value, 'version');
  if (!/^[0-9a-f]{64}$/.test(value)) throw new TypeError('version');
  return value;
}
function airRange(channelId, snapshot, start, end) {
  if (!(start instanceof Date) || !(end instanceof Date)
      || !Number.isFinite(start.getTime()) || !Number.isFinite(end.getTime()) || start >= end) {
    throw new TypeError('valid_half_open_date_range_required');
  }
  return { source_id: 'MAD-AIR', source_version: version(snapshot), channel_id: channel(channelId),
    timestamp_status: 'documented_local', unit_status: 'verified_dictionary', quality_flag: 'V',
    observed_at: { $gte: new Date(start), $lt: new Date(end) } };
}

// MG01 partial and MG10 scoped: logical channel, not a physical sensor.
function channelReadings(sourceId, snapshot, channelId, quality) {
  return { source_id: source(sourceId), source_version: version(snapshot),
    channel_id: channel(channelId), quality_flag: string(quality, 'quality') };
}

// MG02/03: documented air only, one channel/snapshot, never mixed units.
function airExtrema(channelId, snapshot, start, end) {
  return [
    { $match: airRange(channelId, snapshot, start, end) },
    { $group: { _id: { variable: '$measurement_type', unit: '$unit' },
      n: { $sum: 1 }, minimum: { $min: '$value' }, maximum: { $max: '$value' }, average: { $avg: '$value' } } },
    { $sort: { '_id.variable': 1, '_id.unit': 1 } },
  ];
}

// MG09 scoped: quality counts, not averages of unverified physical magnitudes.
function qualityCounts(sourceId, snapshot) {
  return [
    { $match: { source_id: source(sourceId), source_version: version(snapshot) } },
    { $group: { _id: { channel: '$channel_id', quality: '$quality_flag' }, n: { $sum: 1 } } },
    { $sort: { '_id.channel': 1, '_id.quality': 1 } },
  ];
}

module.exports = { channelReadings, airRange, airExtrema, qualityCounts };
