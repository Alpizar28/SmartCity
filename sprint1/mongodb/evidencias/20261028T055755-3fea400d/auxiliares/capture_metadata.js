'use strict';
// Evidence only, executed inside the container owned by the official v2 runner.
async function main() {
  const base = db;
  if (!/^smartcity_v2_[a-f0-9]{12}$/.test(base.getName())) {
    throw new Error('Owned disposable v2 database required');
  }
  const collections = [];
  for (const info of await base.getCollectionInfos()) {
    if (info.type !== 'collection') continue;
    const collection = base.getCollection(info.name);
    collections.push({
      name: info.name,
      count: await collection.countDocuments({}),
      options: info.options,
      indexes: await collection.getIndexes(),
    });
  }
  const contracts = await (await base.readings.aggregate([
    { $group: { _id: {
      contract: '$schema_version', catalog: '$catalog_version', source: '$source_id',
    }, count: { $sum: 1 } } },
    { $sort: { '_id.source': 1 } },
  ])).toArray();
  const first = await base.readings.findOne({ source_id: 'MAD-TRAFFIC' });
  if (!first) throw new Error('Traffic source missing');
  const dates = { observed_at: {
    $gte: new Date('2024-12-31T23:00:00Z'),
    $lt: new Date('2025-01-31T23:00:00Z'),
  } };
  const channel = await base.readings.find({
    channel_id: first.channel_id, source_version: first.source_version,
  }, { _id: 1, observed_at: 1, value: 1 });
  const sortedChannel = await channel.sort({ observed_at: 1 });
  const channelPage = await sortedChannel.limit(5);
  const multiple = await base.readings.find({ ...dates,
    source_id: 'MAD-TRAFFIC', quality_flag: 'N', value: { $gt: 2000 },
    zone_id: { $ne: null },
  }, { _id: 1, zone_id: 1, value: 1, unit: 1 });
  const sortedMultiple = await multiple.sort({ value: -1, _id: 1 });
  const multiplePage = await sortedMultiple.limit(5);
  const plans = {
    channel_sample_MG01: await channelPage.explain('executionStats'),
    multiple_filters_sample_MG10: await multiplePage.explain('executionStats'),
  };
  const count = await base.readings.countDocuments({});
  if (count !== 748889) throw new Error('Native count mismatch');
  if (await base.incidents.countDocuments({}) !== 14388) throw new Error('Incident count mismatch');
  const readingInfo = collections.find(c => c.name === 'readings');
  if (!readingInfo.options.validator || readingInfo.options.validationAction !== 'error' ||
      readingInfo.options.validationLevel !== 'strict') throw new Error('Strict validator missing');
  if (!readingInfo.indexes.some(i => i.unique === true &&
      i.key.channel_id === 1 && i.key.observed_at === 1 && i.key.timestamp_role === 1)) {
    throw new Error('Unique natural observation index missing');
  }
  print('NATIVE_METADATA=' + EJSON.stringify({
    version: await base.version(), database: base.getName(),
    scope: 'Owned v2 disposable container; metadata captured before official cleanup',
    collections, contracts, plans,
  }));
}
main().catch(error => { console.error(error); quit(1); });
