"""SP01–SP10 con DataFrames/Spark SQL, entrada local o HDFS.

Salida NUEVA. Nunca etiqueta una ejecución local como un clúster entre máquinas.
Compatible con Spark 3.5.6 (Docker) y 4.0.1 (entorno Python local).
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time

from pyspark.sql import SparkSession, Window, functions as F, types as T


# Qué hace: arma el esquema fijo del JSONL para que Spark no adivine los tipos.
def schema():
    strings = ('_id', 'channel_id', 'station_id', 'station_name', 'source_id', 'source_version',
               'measurement_type', 'unit', 'observed_at', 'original_time', 'source_day', 'zone_id',
               'schema_version', 'record_hash', 'element_type', 'coordinate_crs')
    fields = [T.StructField(name, T.StringType()) for name in strings]
    fields += [T.StructField(name, T.DoubleType()) for name in
               ('value', 'latitude', 'longitude', 'speed_kmh', 'occupancy_percent', 'load_index')]
    fields += [T.StructField(name, T.IntegerType()) for name in ('source_year', 'source_month')]
    fields += [T.StructField('demo_event', T.BooleanType()),
               T.StructField('raw_reference', T.StructType([T.StructField('column', T.StringType())]))]
    return T.StructType(fields)


# Qué hace: calcula SP01 a SP10 y la serie horaria: conteos, promedios, zonas, anomalías, correlación NO2–ozono y la comparación entre años.
def products(df):
    keys = ['source_id', 'measurement_type', 'unit']
    daily = df.groupBy(*keys, 'source_day', 'source_year', 'source_month', 'zone_id').agg(
        F.count('*').alias('count'), F.sum('value').alias('total_value'),
        F.avg('value').alias('mean'), F.min('value').alias('min'), F.max('value').alias('max'),
        F.sum(F.col('demo_event').cast('long')).alias('demo_events'),
        F.avg('speed_kmh').alias('speed_kmh'), F.avg('occupancy_percent').alias('occupancy_percent'),
        F.avg('load_index').alias('load_index'))
    categories = df.groupBy(*keys).agg(F.count('*').alias('count'), F.sum('value').alias('total_value'),
        F.avg('value').alias('mean'), F.min('value').alias('min'), F.max('value').alias('max'))
    channels = df.groupBy('source_id', 'channel_id', 'station_name', 'measurement_type', 'unit').count()
    events = df.filter(F.col('demo_event') & F.col('zone_id').isNotNull()).groupBy('zone_id').count()
    zones = df.filter(F.col('zone_id').isNotNull()).groupBy('zone_id', *keys).count()
    trend_window = Window.partitionBy(*keys, 'zone_id').orderBy(
        F.unix_timestamp('source_day', 'yyyy-MM-dd')).rangeBetween(-6 * 86400, 0)
    trend = daily.withColumn('rolling_7d', F.sum('total_value').over(trend_window) /
                            F.sum('count').over(trend_window))
    stats = df.groupBy('channel_id').agg(F.avg('value').alias('baseline_mean'),
                                       F.stddev_samp('value').alias('baseline_std'))
    anomalies = df.join(stats, 'channel_id').filter(F.col('baseline_std') > 0).withColumn(
        'z_score', (F.col('value') - F.col('baseline_mean')) / F.col('baseline_std'))
    anomalies = anomalies.filter(F.abs('z_score') > 3).groupBy(*keys, 'source_year').agg(
        F.count('*').alias('anomaly_count'), F.max(F.abs('z_score')).alias('max_abs_z'))
    air = df.filter(F.col('source_id') == 'MAD-AIR')
    no2 = air.filter(F.col('measurement_type') == 'MAD-AIR:8').select(
        'station_id', 'observed_at', F.col('value').alias('no2'))
    ozone = air.filter(F.col('measurement_type') == 'MAD-AIR:14').select(
        'station_id', 'observed_at', F.col('value').alias('ozone'))
    correlations = no2.join(ozone, ['station_id', 'observed_at']).agg(
        F.count('*').alias('paired_hours'), F.corr('no2', 'ozone').alias('pearson_no2_ozone'))
    common = air.filter(F.col('source_month') <= 8).withColumn(
        'day_of_month', F.substring('source_day', 9, 2)).withColumn('hour_slot', F.col('raw_reference.column'))
    pairing = ['channel_id', 'measurement_type', 'unit', 'source_month', 'day_of_month', 'hour_slot']
    first = common.filter(F.col('source_year') == 2025).select(*pairing, F.col('value').alias('value_2025'))
    second = common.filter(F.col('source_year') == 2026).select(*pairing, F.col('value').alias('value_2026'))
    comparison = first.join(second, pairing).groupBy('measurement_type', 'unit', 'source_month').agg(
        F.count('*').alias('paired_channel_hours'), F.countDistinct('channel_id').alias('paired_channels'),
        F.avg('value_2025').alias('mean_2025'), F.avg('value_2026').alias('mean_2026'))
    comparison = comparison.withColumn('delta', F.col('mean_2026') - F.col('mean_2025'))
    stations = df.groupBy('station_id', 'station_name', 'source_id', 'latitude', 'longitude', 'coordinate_crs').count()
    hourly = df.withColumn('local_hour', F.hour(F.to_timestamp('original_time'))).groupBy(
        *keys, 'source_day', 'source_year', 'source_month', 'zone_id', 'local_hour').agg(
        F.count('*').alias('count'), F.sum('value').alias('total_value'),
        F.min('value').alias('min'), F.max('value').alias('max'),
        F.sum(F.col('demo_event').cast('long')).alias('demo_events'))
    return {'SP01_channels': channels, 'SP02_events': events, 'SP03_daily': daily,
            'SP04_correlation': correlations, 'SP05_zones': zones, 'SP06_trends': trend,
            'SP07_anomalies': anomalies, 'SP08_categories': categories,
            'SP09_comparison': comparison, 'SP10_stations': stations, 'hourly': hourly}


# Qué hace: lee el JSONL, exige el mínimo de registros (1 millón en la entrega), guarda los parquet y el resumen. Si la carpeta de salida ya existe, no la toca.
def run(input_path, manifest_path, output, master=None, min_records=1_000_000):
    if output.exists():
        raise ValueError('Use a new output directory; previous evidence is immutable')
    manifest = json.loads(manifest_path.read_text())
    builder = SparkSession.builder.appName('SmartCity-final-SP01-SP10').config(
        'spark.sql.session.timeZone', 'UTC').config('spark.sql.shuffle.partitions', '8').config(
        'spark.sql.adaptive.enabled', 'true')
    if master:
        builder = builder.master(master)
    spark = builder.getOrCreate()
    started = time.perf_counter()
    spark.sparkContext.setLogLevel('WARN')
    try:
        df = spark.read.schema(schema()).option('mode', 'FAILFAST').json(input_path).cache()
        count = df.count()
        if min_records < 1:
            raise ValueError('min_records must be at least 1')
        if count != manifest['count'] or count < min_records:
            raise ValueError(f'Input count mismatch or below minimum ({min_records})')
        invalid = df.filter(F.col('_id').isNull() | F.col('value').isNull() |
                            F.isnan('value') | F.col('observed_at').isNull() |
                            (F.col('schema_version') != 'smartcity-analytics-v1')).count()
        unique = df.select('_id').distinct().count()
        if invalid or unique != count:
            raise ValueError('Null/invalid/duplicate input')
        output.mkdir(parents=True)
        frames = products(df)
        result = {}
        for name, frame in frames.items():
            frame.write.mode('error').parquet(str(output / name))
            saved = spark.read.parquet(str(output / name))
            result[name] = {'rows': saved.count()}
            print(name, result[name], flush=True)
        categories = [row.asDict() for row in frames['SP08_categories'].collect()]
        for row in categories:
            reference = manifest['reference_by_measurement'][row['measurement_type']]
            if row['count'] != reference['count'] or row['min'] != reference['min'] or row['max'] != reference['max']:
                raise ValueError('Independent count/extrema reference mismatch')
            if not math.isclose(row['total_value'], reference['sum'], rel_tol=1e-9, abs_tol=1e-6):
                raise ValueError('Independent sum reference mismatch')
        # Physical plan is preserved; it is evidence, not a claim of optimal performance.
        (output / 'daily-plan.txt').write_text(frames['SP03_daily']._jdf.queryExecution().toString())
        executors = str(spark.sparkContext._jsc.sc().getExecutorMemoryStatus().toString())
        academic = min_records >= 1_000_000 and count >= 1_000_000
        limits = ['Single-host demonstration, not multi-machine resilience',
            'Events are demo intensity >2000 veh/h; anomaly baseline uses full historical input',
            'No official alerts, physical sensor count, energy or CO2 coverage',
            'Interannual comparison uses exactly paired channel/month/day/H-slot observations',
            'Air district unknown; geospatial inventory has unverified historical validity']
        if not academic:
            limits.append('Sample or smoke run: below the academic minimum of 1000000 records')
        summary = {'status': 'PASS' if academic else 'PASS_SAMPLE',
            'data_origin': manifest.get('data_origin', 'observado'),
            'min_records_required': min_records,
            'spark_version': spark.version, 'master': spark.sparkContext.master,
            'application_id': spark.sparkContext.applicationId, 'input_uri': input_path,
            'input_manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'input_records': count, 'unique_ids': unique, 'input_partitions': df.rdd.getNumPartitions(),
            'executor_memory_status': executors, 'independent_reference_verified': True,
            'products': result, 'categories': categories, 'elapsed_seconds': time.perf_counter() - started,
            'finished_at_utc': datetime.now(timezone.utc).isoformat(),
            'limits': limits}
        with (output / 'summary.json').open('x') as stream:
            json.dump(summary, stream, indent=2, allow_nan=False)
        return summary
    finally:
        spark.stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--master')
    parser.add_argument('--min-records', type=int, default=1_000_000,
                        help='Academic runs keep the default of 1000000. Lower it only for a labeled sample.')
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.manifest, args.output, args.master, args.min_records), indent=2))
