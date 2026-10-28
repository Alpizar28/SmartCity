'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
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
