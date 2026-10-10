// Only disposable container localhost; no environment DSN accepted.
if (!/^smartcity_phase5_[a-f0-9]{12}$/.test(db.getName())) {
  throw new Error('Disposable Phase5 database name required');
}
const sample = EJSON.parse(fs.readFileSync('/inputs/sample.extjson', 'utf8'));
const catalogs = JSON.parse(fs.readFileSync('/inputs/catalogs.json', 'utf8'));
const expected = JSON.parse(fs.readFileSync('/evidence/sample_reference.json', 'utf8'));
function check(condition, message) { if (!condition) throw new Error(message); }
check(sample.length >= 1000 && sample.length <= 10000, 'Bounded sample required');
db.createCollection('readings', {validator: {$jsonSchema: {
  bsonType: 'object', required: ['_id','measurement_id','station_id','channel_id','observed_at',
    'source_id','source_version','measurement_type','value','unit','sensor_id','data_origin','raw_reference'],
  properties: {
    _id: {bsonType: 'string'}, measurement_id: {bsonType: 'string'},
    station_id: {bsonType: 'string'}, channel_id: {bsonType: 'string'},
    sensor_id: {bsonType: ['null','string']}, zone_id: {bsonType: ['null','string']},
    observed_at: {bsonType: 'date'}, value: {bsonType: ['double','int','long','decimal']},
    unit: {bsonType: ['null','string']}, source_id: {bsonType: 'string'},
    source_version: {bsonType: 'string'}, measurement_type: {bsonType: 'string'},
    data_origin: {enum: ['observed','derived','synthetic']}, raw_reference: {bsonType:'object'}
  }
}}, validationLevel: 'strict', validationAction: 'error'});
const result = {engine: 'MongoDB', version: db.version(), sample_size:sample.length,
  native_executed:false, queries:{}, timings_ms:{}, physical_sensor_semantics_approved:false};
const start = performance.now();
for (let i=0; i<sample.length; i+=500) db.readings.insertMany(sample.slice(i,i+500), {ordered:true});
result.timings_ms.insert_batches = performance.now()-start;
const indexStart = performance.now();
db.readings.createIndex({channel_id:1, observed_at:1, timestamp_role:1}, {unique:true, name:'natural_observation'});
db.readings.createIndex({channel_id:1, observed_at:1}, {name:'channel_time'});
db.readings.createIndex({source_id:1, measurement_type:1, observed_at:1}, {name:'source_variable_time'});
db.readings.createIndex({zone_id:1, measurement_type:1, observed_at:1}, {name:'zone_variable_time'});
result.timings_ms.create_indexes = performance.now()-indexStart;
result.catalog_reference_errors = sample.filter(d => !catalogs.channels[d.channel_id] ||
  catalogs.channels[d.channel_id].station_id!==d.station_id || !catalogs.stations[d.station_id] ||
  (d.zone_id!==null && !catalogs.zones[d.zone_id])).length;
check(result.catalog_reference_errors===0, 'Cross-catalog FK mismatch');
const target = sample[0].channel_id;
let t = performance.now();
const channel = db.readings.find({channel_id:target}, {_id:1,observed_at:1,value:1}).sort({observed_at:1}).toArray();
check(channel.length===expected.channel_count, 'Channel reference mismatch');
result.queries.MG01 = {count:channel.length, scope:'logical channel; physical sensor pending', reference_equal:true};
result.timings_ms.MG01 = performance.now()-t;
const from = new Date('2024-12-31T23:00:00Z'), until = new Date('2025-02-01T00:00:00Z');
t = performance.now();
const range = db.readings.countDocuments({observed_at:{$gte:from,$lt:until}});
check(range===sample.length, 'Calendar January source observations/range mismatch');
result.queries.MG02 = {count:range, from:from, until:until, reference_equal:true};
result.timings_ms.MG02 = performance.now()-t;
t = performance.now();
const grouped = db.readings.aggregate([
  {$match:{observed_at:{$gte:from,$lt:until}}},
  {$group:{_id:{source:'$source_id',variable:'$measurement_type',unit:'$unit'},
    n:{$sum:1},min:{$min:'$value'},max:{$max:'$value'},sum:{$sum:'$value'}}},
  {$sort:{'_id.source':1,'_id.variable':1}}
]).toArray();
for (const source of Object.keys(expected.by_source)) {
  const g = grouped.filter(r=>r._id.source===source), ref = expected.by_source[source];
  check(g.reduce((n,r)=>n+r.n,0)===ref.count, 'Aggregation count mismatch');
  check(Math.min(...g.map(r=>r.min))===ref.min && Math.max(...g.map(r=>r.max))===ref.max, 'Extrema mismatch');
  check(Math.abs(g.reduce((n,r)=>n+r.sum,0)-ref.sum)<=Math.max(1e-6,Math.abs(ref.sum)*1e-10),'Sum mismatch');
}
result.queries.MG03 = {reference_equal:true, grouped_by:'source/variable/unit', result:grouped};
result.queries.MG09 = {native_framework:true, stages:['$match','$group','$sort'],reference_equal:true};
result.timings_ms.MG03_MG09 = performance.now()-t;
t = performance.now();
result.queries.MG06 = {scope:'only published traffic districts; inventory historical validity pending',
  result:db.readings.aggregate([{$match:{zone_id:{$ne:null},unit:{$ne:null}}},
    {$group:{_id:{zone:'$zone_id',type:'$measurement_type',unit:'$unit'},mean:{$avg:'$value'},n:{$sum:1}}},
    {$sort:{'_id.zone':1}}]).toArray()};
result.queries.MG07 = {scope:'measurement variable, not physical device type',
  result:db.readings.aggregate([{$match:{unit:{$ne:null}}},
    {$group:{_id:{source:'$source_id',type:'$measurement_type',unit:'$unit'},mean:{$avg:'$value'},n:{$sum:1}}}]).toArray()};
result.timings_ms.MG06_MG07 = performance.now()-t;
t = performance.now();
const multiQuery = {channel_id:target, observed_at:{$gte:from,$lt:until}, value:{$gte:sample[0].value}, quality_flag:sample[0].quality_flag};
const multi = db.readings.find(multiQuery, {_id:1,value:1}).sort({observed_at:1}).toArray();
const multiExpected = sample.filter(d=>d.channel_id===target && d.observed_at>=from && d.observed_at<until && d.value>=sample[0].value && d.quality_flag===sample[0].quality_flag).length;
check(multi.length===multiExpected, 'Multiple filters mismatch');
result.queries.MG10 = {count:multi.length, reference_equal:true};
result.timings_ms.MG10 = performance.now()-t;
result.explain = db.readings.find({channel_id:target, observed_at:{$gte:from,$lt:until}})
  .sort({observed_at:1}).explain('executionStats');
result.hinted_explain = db.readings.find({channel_id:target, observed_at:{$gte:from,$lt:until}})
  .hint('channel_time').explain('executionStats');
result.hint_is_demonstration_not_optimizer_claim = true;
result.indexes = db.readings.getIndexes();
// Reject schema/unique errors; never change original imported observations.
result.rejected = {};
try { db.readings.insertOne(sample[0]); result.rejected.duplicate=false; }
catch(e) { result.rejected.duplicate = e.code===11000; }
try { db.readings.insertOne({...sample[0],_id:'bad-date-demo',observed_at:'not-BSON-date'}); result.rejected.string_date=false; }
catch(e) { result.rejected.string_date = e.code===121; }
check(result.rejected.duplicate && result.rejected.string_date, 'Expected rejection failed');
check(sample.every(d=>db.readings.findOne({_id:d._id}).payload_hash===d.payload_hash),'Conflict on replay');
const reimport = db.readings.bulkWrite(sample.map(d=>({updateOne:{filter:{_id:d._id},update:{$setOnInsert:d},upsert:true}})),{ordered:true});
check(reimport.upsertedCount===0 && db.readings.countDocuments({})===sample.length,'Idempotence failed');
result.idempotent_reimport = {upserted:reimport.upsertedCount,count:db.readings.countDocuments({})};
db.createCollection('crud_demo');
db.crud_demo.insertOne({_id:'demo-one',record_kind:'crud_fixture',data_origin:'synthetic',annotation:'fixture, not measurement'});
db.crud_demo.insertMany([{_id:'demo-two',data_origin:'synthetic'},{_id:'demo-three',data_origin:'synthetic'}]);
check(db.crud_demo.findOne({_id:'demo-one'})!==null,'findOne failed');
check(db.crud_demo.updateOne({_id:'demo-one'},{$set:{annotation:'reviewed'}}).modifiedCount===1,'updateOne failed');
check(db.crud_demo.updateMany({},{$set:{demo_only:true}}).modifiedCount===3,'updateMany failed');
check(db.crud_demo.deleteOne({_id:'demo-three'}).deletedCount===1,'deleteOne failed');
result.crud = {insertOne:true,insertMany:true,find:true,findOne:true,updateOne:true,updateMany:true,deleteOne:true,
  collection:'crud_demo',synthetic_nonmeasurement_fixtures:3,original_measurements_mutated:0};
result.queries.MG04 = {executed:false,blocked:'No approved rule, threshold, unit/duration/severity policy'};
result.queries.MG05 = {executed:false,blocked:'No historical emissions or authorized replay'};
result.queries.MG08 = {executed:false,blocked:'Accidents2026 separated; not in January2025 native sample'};
result.local_native_query_designs_executed = 7;
result.not_full_academic_compliance = true;
result.native_executed = true;
print('PHASE5_RESULT='+EJSON.stringify(result));
