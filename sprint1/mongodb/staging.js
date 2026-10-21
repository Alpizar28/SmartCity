'use strict';

// Pass only ReadingDTO.mongo_document() validated with independent catalogs.
// Collections must have the strict validator and unique_staging_tuple index.
// Append-only readings: do not concurrently delete/update accepted documents.
async function stageReading(readings, quarantine, document) {
  if (typeof document.staging_key !== 'string' || !document.staging_key
      || typeof document.payload_hash !== 'string') throw new TypeError('validated_DTO_required');
  try {
    // Driver may assign _id to this shallow copy; preserve caller's input.
    await readings.insertOne({ ...document });
    return 'accepted';
  } catch (error) {
    if (error.code !== 11000) throw error;
    const existing = await readings.findOne({ staging_key: document.staging_key });
    if (!existing) throw error; // Unrelated uniqueness violation: fail closed.
    if (existing.payload_hash === document.payload_hash) return 'duplicate';
    await quarantine.insertOne({ reason: 'conflicting_payload_same_original_key',
      existing_id: existing._id, incoming: document, recorded_at: new Date() });
    return 'quarantined';
  }
}

module.exports = { stageReading };
