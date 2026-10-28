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

// Consultas sobre las dos fuentes de la generación v2.
{
  const { consultar } = require('../../sprint1/basico/consultas_mongodb_v2');

  function baseSimulada(asincrona = false) {
    const llamadas = [];
    function coleccion(nombre) {
      const operaciones = {
        findOne: () => ({ channel_id: 'canal-real-del-test', source_version: 'version-del-test' }),
        countDocuments: filtro => { llamadas.push({ nombre, tipo: 'count', filtro }); return 1; },
        find: filtro => {
          llamadas.push({ nombre, tipo: 'find', filtro });
          return { sort() { return this; }, limit() { return this; }, toArray: () => [] };
        },
        aggregate: pipeline => {
          llamadas.push({ nombre, tipo: 'aggregate', pipeline });
          return { toArray: () => [] };
        },
      };
      if (asincrona) {
        for (const nombreOperacion of ['findOne', 'countDocuments', 'find', 'aggregate']) {
          const original = operaciones[nombreOperacion];
          operaciones[nombreOperacion] = async (...argumentos) => original(...argumentos);
        }
      }
      return operaciones;
    }
    return { llamadas, readings: coleccion('readings'), derived_events: coleccion('events'),
      alerts: coleccion('alerts'), incidents: coleccion('incidents') };
  }
  const regla = { threshold: 2000, version: 'traffic-intensity-demo-v1', official_rule: false };

  test('v2 espera operaciones asíncronas reales del módulo mongosh', async () => {
    const resultados = await consultar(baseSimulada(true), regla);
    assert.equal(Object.keys(resultados).length, 10);
    assert.equal(resultados.MG01.total, 1);
    assert.ok(Array.isArray(resultados.MG03));
  });

  test('v2 ejecuta diez consultas de lectura y exige la segunda fuente', async () => {
    const base = baseSimulada();
    assert.equal(Object.keys(await consultar(base, regla)).length, 10);
    base.readings.findOne = () => null;
    await assert.rejects(() => consultar(base, regla), /Falta la segunda fuente/);
  });

  test('v2 usa ventana semiabierta de Madrid y filtros múltiples explícitos', async () => {
    const resultados = await consultar(baseSimulada(), regla);
    const fechas = resultados.MG02.parametros.observed_at;
    assert.equal(fechas.$gte.toISOString(), '2024-12-31T23:00:00.000Z');
    assert.equal(fechas.$lt.toISOString(), '2025-01-31T23:00:00.000Z');
    assert.equal(resultados.MG10.parametros.quality_flag, 'N');
    assert.equal(resultados.MG10.parametros.value.$gt, 2000);
    assert.deepEqual(resultados.MG10.parametros.zone_id, { $ne: null });
  });

  test('v2 separa fuentes/unidades y no promedia zonas desconocidas', async () => {
    const base = baseSimulada();
    await consultar(base, regla);
    const pipelines = base.llamadas.filter(l => l.tipo === 'aggregate' && l.nombre === 'readings');
    const promedioZona = pipelines.find(l => l.pipeline[0].$match?.zone_id);
    assert.deepEqual(promedioZona.pipeline[0].$match.zone_id, { $ne: null });
    for (const fila of pipelines.filter(l => l.pipeline.some(etapa => etapa.$group?.promedio))) {
      const agrupacion = fila.pipeline.find(etapa => etapa.$group).$group;
      assert.equal(agrupacion._id.fuente, '$source_id');
      assert.equal(agrupacion._id.unidad, '$unit');
    }
  });

  test('v2 consulta accidentes aparte y alertas desde la colección emitida', async () => {
    const base = baseSimulada();
    await consultar(base, regla);
    const accidentes = base.llamadas.find(l => l.nombre === 'incidents');
    assert.equal(accidentes.pipeline[0].$group._id, '$category');
    const alertas = base.llamadas.find(l => l.nombre === 'alerts');
    assert.equal(alertas.pipeline[1].$group.primera_emision.$min, '$emitted_at');
    assert.ok(base.llamadas.some(l => l.nombre === 'events' && l.tipo === 'count'));
  });
}

// Laboratorio sintético: referencias, aislamiento y consultas por sensor.
{
  const fixtures = require('../../sprint1/mongodb/academico/fixtures.json');
  const { comprobarAislamiento, comprobarReferencias } = require('../../sprint1/mongodb/academico/modelo_demo');
  const { lecturasPorSensor } = require('../../sprint1/mongodb/academico/consultas_demo');
  const copiar = d => JSON.parse(JSON.stringify(d));

  test('las referencias y unidades del conjunto sintético son coherentes', () => {
    comprobarReferencias(fixtures);
    for (const [collection, field, value, error] of [
      ['readings', 'sensor_id', 'unknown', /Sensor inexistente/],
      ['sensors', 'sensor_type', 'unknown', /Tipo de sensor inexistente/],
      ['readings', 'unit', '%', /Magnitud\/unidad incompatible/],
      ['dynamic_information', 'subject_sensor_id', 'unknown', /Sujeto narrativo inexistente/],
    ]) {
      const d = copiar(fixtures); d[collection][0][field] = value;
      assert.throws(() => comprobarReferencias(d), error);
    }
  });
  test('el laboratorio rechaza destinos oficiales y nombres ambiguos', () => {
    comprobarAislamiento('smartcity_academic_0123456789abcdef');
    for (const name of ['smartcity', 'admin', 'smartcity_v2_012345abcdef', 'smartcity_academic_']) {
      assert.throws(() => comprobarAislamiento(name), /exclusiva/);
    }
  });
  test('MG01 requiere identidad explícita antes de consultar', async () => {
    await assert.rejects(() => lecturasPorSensor({}, undefined), /sensor_id explícito/);
    await assert.rejects(() => lecturasPorSensor({}, ''), /sensor_id explícito/);
  });
}

// La versión de estudio debe conservar las operaciones de la versión oficial.
{
  const oficial = require('../../sprint1/basico/consultas_mongodb_v2');
  const estudio = require('../../sprint1/basico/consultas_mongodb_estudio');

  function crearBase(asincrona, conTrafico = true) {
    const llamadas = [];
    function coleccion(nombre) {
      function registrar(operacion, argumentos, resultado) {
        llamadas.push({ nombre, operacion, argumentos });
        return asincrona ? Promise.resolve(resultado) : resultado;
      }
      function cursor() {
        return {
          sort(orden) { return registrar('sort', orden, this); },
          limit(cantidad) { return registrar('limit', cantidad, this); },
          toArray() { return registrar('toArray', [], [{ ejemplo: nombre }]); },
        };
      }
      return {
        findOne(filtro) {
          const lectura = conTrafico ? { channel_id: 'canal-1', source_version: 'version-1' } : null;
          return registrar('findOne', filtro, lectura);
        },
        countDocuments(filtro) { return registrar('countDocuments', filtro, 7); },
        find(...argumentos) { return registrar('find', argumentos, cursor()); },
        aggregate(etapas) { return registrar('aggregate', etapas, cursor()); },
      };
    }
    return {
      llamadas,
      readings: coleccion('readings'),
      derived_events: coleccion('derived_events'),
      alerts: coleccion('alerts'),
      incidents: coleccion('incidents'),
    };
  }

  for (const asincrona of [false, true]) {
    test(`versión de estudio conserva consultas y resultados; async=${asincrona}`, async () => {
      const baseOficial = crearBase(asincrona);
      const baseEstudio = crearBase(asincrona);
      const regla = { threshold: 2000, version: 'demo-v1', official_rule: false };
      const esperado = await oficial.consultar(baseOficial, regla);
      const obtenido = await estudio.consultar(baseEstudio, regla);
      assert.deepEqual(obtenido, esperado);
      assert.deepEqual(baseEstudio.llamadas, baseOficial.llamadas);
    });
  }

  test('versión de estudio rechaza la ausencia de tráfico', async () => {
    await assert.rejects(
      () => estudio.consultar(crearBase(true, false), { threshold: 2000, version: 'demo-v1' }),
      /Falta la segunda fuente real de tráfico/,
    );
  });
}
