// Práctica básica. Sin GUARDAR=true no modifica nada.
// Usa una colección separada y copias de tres lecturas reales ya presentes.
if (typeof GUARDAR === 'undefined' || GUARDAR !== true) {
  print('Solo revisión. Para practicar CRUD debes indicar GUARDAR=true explícitamente.');
} else {
  const base = db;
  const ejemplos = base.readings.find().sort({ _id: 1 }).limit(3).toArray();
  if (ejemplos.length !== 3) {
    throw new Error('Se necesitan tres lecturas reales; no se inventarán registros.');
  }
  if (base.getCollectionNames().includes('practica_crud')) {
    throw new Error('practica_crud ya existe. No se borra trabajo previo.');
  }
  const cantidadOriginal = base.readings.countDocuments({});

  // Quitar los IDs locales para que MongoDB cree otros en la colección de práctica.
  for (const ejemplo of ejemplos) {
    delete ejemplo._id;
  }
  base.createCollection('practica_crud');
  const practica = base.practica_crud;

  print('1. insertOne: insertar la primera copia');
  const primeraInsercion = practica.insertOne(ejemplos[0]);
  const id = primeraInsercion.insertedId;

  print('2. insertMany: insertar las otras dos copias');
  practica.insertMany([ejemplos[1], ejemplos[2]]);

  print('3. findOne: buscar por el ID asignado');
  printjson(practica.findOne({ _id: id }));

  print('4. find: ver las tres copias');
  printjson(practica.find({}, { channel_id: 1, value: 1, unit: 1 }).toArray());

  // Estas marcas son de práctica, NO nuevas observaciones ni estados de sensores.
  print('5. updateOne: agregar una marca de revisión a una copia');
  const uno = practica.updateOne({ _id: id }, { $set: { revisado_en_practica: true } });
  if (uno.modifiedCount !== 1) {
    throw new Error('No se actualizó la copia esperada.');
  }

  print('6. updateMany: agregar una marca de práctica a las tres copias');
  const varios = practica.updateMany({}, { $set: { solo_practica: true } });
  if (varios.modifiedCount !== 3) {
    throw new Error('Se esperaban tres copias actualizadas.');
  }

  print('7. deleteOne: eliminar únicamente la primera copia');
  const borrado = practica.deleteOne({ _id: id });
  if (borrado.deletedCount !== 1 || practica.countDocuments({}) !== 2) {
    throw new Error('El resultado del borrado no coincide.');
  }
  if (base.readings.countDocuments({}) !== cantidadOriginal) {
    throw new Error('No se deben modificar las lecturas originales.');
  }

  // Solo se borra la colección que este archivo acaba de crear.
  practica.drop();
  print('CRUD_BASICO_PASS: práctica terminada, sin cambiar readings.');
}
