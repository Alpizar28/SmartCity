'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
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
