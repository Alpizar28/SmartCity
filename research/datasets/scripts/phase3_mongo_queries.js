// Native MongoDB DESIGN ONLY. Not executed in Phase3 (no local MongoDB engine).
// Never connect to production. Supply a disposable database and audited documents.
// IDs share the exact channel_id/location_id contract used in PostgreSQL proof.
// One document per actual interval/observation, values stay in original units.
function phase3Queries(proofDb, channel, from, until) {
  if (!proofDb.getName().startsWith('smartcity_phase3_proof_')) {
    throw new Error('Only an explicitly created disposable proof database is allowed');
  }
  const readings = proofDb.getCollection('readings');
  readings.createIndex({channel_id: 1, time: 1}, {unique: true});
  readings.createIndex({zone: 1, source: 1, variable: 1, unit: 1, time: 1});
  const valid = {quality: 'valid', value: {$type: 'number'}};
  return {
    MG01: () => readings.find({channel_id: channel}).sort({time: 1}),
    MG02: () => readings.find({time: {$gte: from, $lt: until}}),
    MG03: () => readings.aggregate([
      {$match: valid},
      {$group: {_id: {source: '$source', variable: '$variable', unit: '$unit'},
        minimum: {$min: '$value'}, maximum: {$max: '$value'}}}
    ]),
    // Critical events require an accepted unit-specific duration/threshold policy.
    // IQR candidates are anomaly candidates, NOT detected critical incidents.
    MG04: () => proofDb.getCollection('derived_events').find({policy_approved: true, event_kind: 'critical'}),
    // No historical emissions are available. Empty results do not meet this requirement.
    MG05: () => proofDb.getCollection('alerts').aggregate([
      {$match: {zone: {$ne: null}, emission_provenance_verified: true}},
      {$group: {_id: '$zone', emitted_alerts: {$sum: 1}}}
    ]),
    MG06: () => readings.aggregate([
      {$match: {...valid, zone: {$ne: null}}},
      {$group: {_id: {zone: '$zone', source: '$source', variable: '$variable', unit: '$unit'},
        mean: {$avg: '$value'}, observations: {$sum: 1}}}
    ]),
    MG07: () => readings.aggregate([
      {$match: valid},
      {$group: {_id: {source: '$source', variable: '$variable', unit: '$unit'},
        mean: {$avg: '$value'}}}
    ]),
    MG08: () => proofDb.getCollection('incidents').aggregate([
      {$group: {_id: {source: '$source', category: '$category', record_kind: '$record_kind'},
        incidents: {$sum: 1}}}
    ]),
    MG09: () => readings.aggregate([
      {$match: {...valid, time: {$gte: from, $lt: until}}},
      {$group: {_id: '$channel_id', n: {$sum: 1}, mean: {$avg: '$value'}}},
      {$sort: {n: -1, _id: 1}}
    ]),
    MG10: () => readings.find({...valid, channel_id: channel, time: {$gte: from, $lt: until}},
      {_id: 1, channel_id: 1, time: 1, value: 1, unit: 1})
  };
}

// CRUD proof is a DESIGN, not an executed success:
// insertOne/insertMany: copied observed docs with deterministic IDs in a disposable DB.
// find/findOne: compare originals; updateOne/updateMany: annotation.reviewed only;
// deleteOne: a disposable copy with namespace proof:, never original historical records.
// Date policy: convert to BSON Date only UTC/GMT or confirmed local timezone.
// LCL wall timestamps stay explicit original_time + clock_unverified until resolved.
// Never apply new Date(local_string) silently: the runner timezone is not evidence.
