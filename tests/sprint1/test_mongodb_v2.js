'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
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
