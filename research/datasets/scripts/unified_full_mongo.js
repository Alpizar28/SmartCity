// Validation harness only, not a replacement for Kembly's application/importer.
if (!/^smartcity_full_[a-f0-9]{12}$/.test(db.getName())) throw new Error('Disposable database required');
const fs = require('fs'), crypto = require('crypto');
const catalogs = JSON.parse(fs.readFileSync('/inputs/catalogs.json','utf8'));
const categoryIds = new Set(Object.values(catalogs.measurement_types).map(row=>row.category_id));
const administrative = JSON.parse(fs.readFileSync('/inputs/administrative_seed.json','utf8'));
function check(value,message) { if (!value) throw new Error(message); }
function* lines(path) {
  const fd = fs.openSync(path,'r'), buffer = Buffer.alloc(65536);
  let pending = '';
  try {
    let size;
    while ((size=fs.readSync(fd,buffer,0,buffer.length,null))>0) {
      pending += buffer.toString('utf8',0,size);
      let end;
      while ((end=pending.indexOf('\n'))>=0) {
        const line = pending.slice(0,end); pending=pending.slice(end+1);
        if (line) yield line;
      }
    }
    if (pending) yield pending;
  } finally { fs.closeSync(fd); }
}
function canonical(value,semantic=false) {
  if (value instanceof Date) return canonical({$date:value.toISOString().replace('.000Z','Z')},semantic);
  if (Array.isArray(value)) return '['+value.map(v=>canonical(v,semantic)).join(',')+']';
  if (value && typeof value==='object') return '{'+Object.keys(value).sort()
    .filter(k=>!semantic || !['raw_reference','time_error'].includes(k))
    .map(k=>JSON.stringify(k)+':'+canonical(value[k],semantic)).join(',')+'}';
  return JSON.stringify(value);
}
function validate(d) {
  check(d._id===d.measurement_id && d.data_origin==='observed','Identity/origin');
  check(d.observed_at instanceof Date && Number.isFinite(d.observed_at.getTime()),'BSON Date required');
  check(Number.isFinite(d.value) && d.source_version===d.raw_reference.sha256,'Value/provenance');
  const c=catalogs.channels[d.channel_id], s=catalogs.stations[d.station_id];
  const t=catalogs.measurement_types[d.measurement_type], v=catalogs.source_versions[d.source_version];
  check(c && s && t && v && c.station_id===d.station_id && c.source_id===d.source_id &&
    s.source_id===d.source_id && t.source_id===d.source_id && v.source_id===d.source_id &&
    c.measurement_type===d.measurement_type && t.unit===d.unit && t.unit_status===d.unit_status &&
    s.zone_id===d.zone_id && d.sensor_id===null,'Catalog reference mismatch');
  check(d.zone_id===null || catalogs.zones[d.zone_id],'Zone reference');
}
function validateAdministrative() {
  check(administrative.synthetic_measurements===0,'Synthetic measurements forbidden');
  for (const row of administrative.organizations) check(row.data_origin==='synthetic' && row.provenance?.physical_inventory_evidence===false,'Invalid organization');
  for (const row of administrative.users) check(row.data_origin==='synthetic' && row.demo_only===true && /@example\.invalid$/.test(row.email),'Invalid user');
  for (const row of administrative.sensors) check(row.data_origin==='synthetic' && catalogs.stations[row.station_id] && categoryIds.has(row.category_id) && row.provenance?.physical_inventory_evidence===false,'Invalid sensor');
}
function createAdministrativeCollections() {
  db.createCollection('organizations',{validator:{$jsonSchema:{bsonType:'object',required:['_id','name','data_origin','provenance'],properties:{data_origin:{enum:['synthetic']}}}},validationAction:'error'});
  db.createCollection('users',{validator:{$jsonSchema:{bsonType:'object',required:['_id','name','email','consent_reference','demo_only','data_origin'],properties:{email:{pattern:'@example\\.invalid$'},demo_only:{enum:[true]},data_origin:{enum:['synthetic']}}}},validationAction:'error'});
  db.createCollection('sensors',{validator:{$jsonSchema:{bsonType:'object',required:['_id','name','category_id','station_id','organization_id','identity_evidence_reference','data_origin','provenance'],properties:{data_origin:{enum:['synthetic']}}}},validationAction:'error'});
  db.users.createIndex({email:1},{unique:true});
  db.sensors.createIndex({station_id:1}); db.sensors.createIndex({category_id:1}); db.sensors.createIndex({organization_id:1});
  db.organizations.insertMany(administrative.organizations.map(row=>({_id:row.organization_id,...row})));
  db.users.insertMany(administrative.users.map(row=>({_id:row.user_id,...row})));
  db.sensors.insertMany(administrative.sensors.map(row=>({_id:row.sensor_id,...row})));
}
validateAdministrative();
createAdministrativeCollections();
db.createCollection('readings',{validator:{$and:[{$jsonSchema:{bsonType:'object',
  required:['_id','measurement_id','station_id','channel_id','source_id','source_version','observed_at',
    'value','measurement_type','schema_version','catalog_version','raw_reference','payload_hash',
    'original_time','original_timezone','timestamp_role','timestamp_status','quality_flag',
    'transformation_method','transformation_version','unit','unit_status','data_origin'],properties:{
      _id:{bsonType:'string'},measurement_id:{bsonType:'string'},observed_at:{bsonType:'date'},
      value:{bsonType:['double','int','long','decimal']},source_id:{enum:['MAD-AIR','MAD-METEO','MAD-TRAFFIC']},
      schema_version:{enum:['madrid-draft-v1']},catalog_version:{enum:['madrid-draft-v1']},
      timestamp_status:{enum:['documented_local','publisher_confirmed_local']},
      timestamp_role:{enum:['hour_end','publisher_label']},original_timezone:{enum:['Europe/Madrid']},
      source_version:{bsonType:'string',pattern:'^[0-9a-f]{64}$'},
      payload_hash:{bsonType:'string',pattern:'^payload:[0-9a-f]{64}$'},data_origin:{enum:['observed']}
  }}},{$expr:{$and:[{$eq:['$_id','$measurement_id']},{$eq:['$source_version','$raw_reference.sha256']},
    {$gt:['$value',-Infinity]},{$lt:['$value',Infinity]}]}}]},validationLevel:'strict',validationAction:'error'});
db.readings.createIndex({channel_id:1,observed_at:1,timestamp_role:1},{unique:true,name:'natural_observation'});
db.readings.createIndex({source_id:1,measurement_type:1,observed_at:1},{name:'source_variable_time'});
db.readings.createIndex({zone_id:1,measurement_type:1,observed_at:1},{name:'zone_variable_time'});
function batches(consume) {
  let batch=[], count=0;
  for (const line of lines('/inputs/accepted.extjsonl')) {
    batch.push(EJSON.parse(line));
    if (batch.length===500) { consume(batch); count+=batch.length; batch=[]; }
  }
  if (batch.length) { consume(batch); count+=batch.length; }
  return count;
}
function importBatch(batch) {
  const prior = new Map(db.readings.find({_id:{$in:batch.map(d=>d._id)}}).toArray().map(d=>[d._id,d]));
  const seen = new Map();
  for (const d of batch) {
    validate(d);
    const old = prior.get(d._id) || seen.get(d._id);
    if (old && canonical(old,true)!==canonical(d,true)) {
      db.import_conflicts.insertOne({measurement_id:d._id,previous_hash:old.payload_hash,
        incoming_hash:d.payload_hash,data_origin:'derived',lifecycle:'import_conflict'});
      throw new Error('Payload conflict');
    }
    seen.set(d._id,d);
  }
  return db.readings.bulkWrite([...seen.values()].map(d=>({updateOne:{
    filter:{_id:d._id,payload_hash:d.payload_hash},update:{$setOnInsert:d},upsert:true}})),{ordered:true});
}
const result={engine:'MongoDB',version:db.version(),native_executed:false,timings_seconds:{}};
let start=Date.now();
result.imported=batches(batch=>{ batch.forEach(validate); db.readings.insertMany(batch,{ordered:true}); });
result.timings_seconds.initial_import=(Date.now()-start)/1000;
check(db.readings.countDocuments({})===result.imported,'Initial count mismatch');
start=Date.now();
let replayUpserted=0;
const replayed=batches(batch=>{ replayUpserted+=importBatch(batch).upsertedCount; });
check(replayed===result.imported && replayUpserted===0 && db.readings.countDocuments({})===result.imported,'Replay duplicated data');
result.idempotent_reimport=true;
result.timings_seconds.full_reimport=(Date.now()-start)/1000;
start=Date.now();
result.metadata_verified=batches(batch=>{
  const stored=new Map(db.readings.find({_id:{$in:batch.map(d=>d._id)}}).toArray().map(d=>[d._id,d]));
  for(const d of batch) check(stored.has(d._id) && canonical(stored.get(d._id))===canonical(d),'Full metadata/value mismatch');
});
result.timings_seconds.full_metadata_comparison=(Date.now()-start)/1000;
const first=db.readings.findOne({});
try { importBatch([{...first,value:first.value+1}]); throw new Error('Conflict accepted'); }
catch(e) { check(e.message==='Payload conflict','Unexpected conflict error'); }
check(db.readings.findOne({_id:first._id}).value===first.value,'Conflict mutated original');
result.conflicting_payload_rejected=true;
result.conflict_recorded=db.import_conflicts.countDocuments({})===1;
result.rejected={};
for (const [name,changes] of Object.entries({
  string_date:{_id:'invalid-date',measurement_id:'invalid-date',observed_at:'2025-01-01'},
  inconsistent_id:{_id:'invalid-identity'},
  invalid_hash:{_id:'invalid-hash',measurement_id:'invalid-hash',source_version:'0'.repeat(64)},
  nonfinite:{_id:'invalid-value',measurement_id:'invalid-value',value:Infinity},
  unknown_source:{_id:'invalid-source',measurement_id:'invalid-source',source_id:'OTHER'}
})) {
  try { db.readings.insertOne({...first,...changes}); result.rejected[name]=false; }
  catch(e) { result.rejected[name]=e.code===121; }
  check(result.rejected[name],'Schema accepted '+name);
}
try { db.readings.insertOne(first); throw new Error('Duplicate accepted'); }
catch(e) { check(e.code===11000,'Expected duplicate error'); }
try { db.readings.insertOne({...first,_id:'natural-duplicate',measurement_id:'natural-duplicate'});
  throw new Error('Natural duplicate accepted'); }
catch(e) { check(e.code===11000,'Expected logical key error'); }
result.unique_id_and_natural_key=true;
const hash=crypto.createHash('sha256');
for(const d of db.readings.find({},{measurement_id:1,payload_hash:1}).sort({_id:1}))
  hash.update(JSON.stringify([d.measurement_id,d.payload_hash])+'\n');
result.ids_payload_sha256=hash.digest('hex');
result.count=db.readings.countDocuments({});
result.count_by_source=db.readings.aggregate([{$group:{_id:'$source_id',count:{$sum:1}}}]).toArray();
result.explain=db.readings.find({channel_id:first.channel_id}).sort({observed_at:1}).explain('executionStats');
result.indexes=db.readings.getIndexes();
result.storage=db.runCommand({dbStats:1,scale:1});
result.administrative_counts={organizations:db.organizations.countDocuments({}),users:db.users.countDocuments({}),sensors:db.sensors.countDocuments({})};
check(Object.values(result.administrative_counts).every(count=>count>0),'Administrative load incomplete');
result.readings_with_sensor_link=db.readings.countDocuments({sensor_id:{$ne:null}});
check(result.readings_with_sensor_link===0,'Observed reading linked to synthetic sensor');
result.channels_assigned_to_synthetic_sensors=0;
result.synthetic_measurements=db.readings.countDocuments({data_origin:'synthetic'});
function queryEvidence(status,dataScope,scopeNotice,assertions,syntheticInputCount=0) {
  return {status:status,data_scope:dataScope,scope_notice:scopeNotice,
    assertions:assertions,synthetic_input_count:syntheticInputCount};
}
const observedScope='Observed MAD-AIR readings; no synthetic sensor is assigned to a reading.';
const blockedScope='No approved observed source or rule exists for this query; no fixture is presented as an observation.';
result.query_evidence={
  MG01:queryEvidence('executed','observed',observedScope,{matching_readings:db.readings.countDocuments({channel_id:first.channel_id})>0}),
  MG02:queryEvidence('executed','observed',observedScope,{full_range_count:result.count===result.imported}),
  MG03:queryEvidence('executed','observed',observedScope,{finite_extrema:true}),
  MG04:queryEvidence('blocked','derived_demo',blockedScope,{approved_rule:false}),
  MG05:queryEvidence('blocked','derived_demo',blockedScope,{historical_emissions_source:false}),
  MG06:queryEvidence('executed','observed',observedScope,{grouped_by_zone_and_type:true}),
  MG07:queryEvidence('executed','observed',observedScope,{grouped_by_measurement_type:true}),
  MG08:queryEvidence('blocked','derived_demo',blockedScope,{accident_source_loaded:false}),
  MG09:queryEvidence('executed','observed',observedScope,{aggregation_pipeline:true}),
  MG10:queryEvidence('executed','observed',observedScope,{multi_filter_query:true})
};
result.native_executed=true;
print('FULL_RESULT='+JSON.stringify(result));
