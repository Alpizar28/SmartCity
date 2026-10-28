# Diagramas textuales — contrato común `smartcity`

**Modelo PostgreSQL vigente:** [E-R normalizado completo](diagrama_3nf.md),
con catorce tablas y DTO v2 compatible. Las doce tablas y diagramas siguientes
corresponden al DDL histórico conservado para reproducir sus evidencias.


Formato Mermaid versionable y renderizable en GitHub. Las flechas de flujo expresan transferencia local o propuesta, **no FK ni servicios desplegados**. El E-R histórico refleja las relaciones entre las doce tablas centrales del [DDL `smartcity`](../../research/datasets/scripts/phase5_postgresql.sql); las FK compuestas refuerzan coherencia de fuente y estación. `smartcity_demo.entities` está separado y no tiene FK al núcleo. Versión histórica: [contrato común](../equipo/CONTRATO_UNIFICADO.md).

La muestra de 5.000 de estos diagramas describe la validación inicial, no el volumen actual disponible. La [ampliación anual](../equipo/AMPLIACION_REAL_SPRINT1.md) añade una ruta configurable de todo 2025 con 1.076.813 observaciones reales y validación completa en motores locales. Meteorología y tráfico siguen separados, sin afirmar integración temporal validada.

## 1. Arquitectura de datos

```mermaid
flowchart LR
  O[Snapshots originales inmutables] --> V[Validacion de SHA, QA y claves]
  V --> N[Normalizacion temporal condicionada]
  N --> I[IDs deterministas y catalogos]
  I --> S[Muestra acotada reproducible]
  S --> P[PostgreSQL smartcity local desechable]
  S --> M[MongoDB readings local desechable]
  P -. exportacion futura .-> E[CSV y Parquet posteriores]
  M -. exportacion futura .-> E
  E -. no implementado .-> H[HDFS y Spark futuros]
  H -. no implementado .-> D[Dashboard futuro]
```

La muestra CSV/Parquet local ya existe; la exportación completa desde motores y los nodos HDFS/Spark/dashboard son futuros. No representan contenedores adicionales de Compose. Fuente: [05_ingestion_plan.md](../../research/datasets/05_ingestion_plan.md).

## 2. Flujo ETL acotado y controles

```mermaid
flowchart TD
  R[Originales locales y manifiesto] --> H{Hashes y CRC coherentes}
  H -->|no| F[Abortar sin modificar originales]
  H -->|si| J[Filtro enero y estrato ID de trafico]
  J --> Q[Validar campos, flags, reloj y catalogo]
  Q -->|no elegible| X[Contar rechazo y conservar origen]
  Q -->|elegible| T[UTC bajo estado temporal documentado]
  T --> K[ID canonico y hash de payload]
  K --> L{Ledger de identidad}
  L -->|nuevo| A[Aceptar observacion]
  L -->|identico| B[Replay sin incremento]
  L -->|payload distinto| C[Bloquear o excluir conflicto]
  A --> E[Muestra y exportaciones locales limitadas]
  E --> P[Prueba PostgreSQL]
  E --> M[Prueba MongoDB]
```

Reanudación actual: reutilizar cache completa/hash válido o reconstruir determinísticamente el ledger incompleto. No se declara un checkpoint distribuido. Flags inválidos y tiempos no confirmados quedan en cuarentena referenciada; un conflicto de payload impide publicar un lote completo. Fuente: [phase5_prepare.py](../../research/datasets/scripts/phase5_prepare.py).

## 3. E-R PostgreSQL — doce tablas preliminares

Revisión PostgreSQL v2: se mantienen las mismas doce tablas y FK. La extensión
`sprint1/postgres/contract_v2.sql` añade dos atributos de observación y cambia
CHECK, no cardinalidades. [Auditoría formal](../../sprint1/postgres/normalizacion_3fn.md):
`channels` y `observations` **no cumplen 3FN estricta**; el diagrama refleja el
DDL implementado, no la descomposición propuesta.

Leyenda: `||` exactamente uno; `o|` cero o uno; `o{` cero o muchos. Se permite un padre sin hijos; una FK nullable permite hijo sin padre. Las FK NOT NULL obligan a cada hijo a un padre. Se usan relaciones no identificadoras porque las PK de los hijos son independientes de las FK. **No se infiere obligatoriedad de hijos ni unicidad uno-a-uno de la muestra.**

```mermaid
erDiagram
  sources ||..o{ source_versions : source_id
  sources ||..o{ stations : source_id
  sources ||..o{ measurement_types : source_id
  sources ||..o{ channels : source_id
  sources ||..o{ observations : source_id
  zones o|..o{ locations : zone_id_nullable
  source_versions o|..o{ locations : inventory_version_nullable
  locations o|..o{ stations : location_id_nullable
  sensor_categories ||..o{ measurement_types : category_id
  sensor_categories ||..o{ sensors : category_id
  stations ||..o{ sensors : station_id
  organizations o|..o{ sensors : organization_id_nullable
  stations ||..o{ channels : station_id
  sensors o|..o{ channels : sensor_id_nullable
  measurement_types ||..o{ channels : measurement_type
  channels ||..o{ observations : channel_id
  source_versions ||..o{ observations : source_version

  sources {
    text source_id PK
    text name
    text publisher
  }
  source_versions {
    text source_version PK
    text source_id FK
    text original_path
    timestamptz acquired_at
  }
  zones {
    text zone_id PK
    text name
    text level
  }
  locations {
    text location_id PK
    text zone_id FK
    text inventory_version FK
    text coordinate_crs
    boolean historical_location_verified
  }
  stations {
    text station_id PK
    text source_id FK
    text location_id FK
    text source_key
    boolean inventory_present
  }
  sensor_categories {
    text category_id PK
    text name
  }
  measurement_types {
    text measurement_type PK
    text source_id FK
    text category_id FK
    text code
    text unit
    text unit_status
  }
  organizations {
    text organization_id PK
    text name
    text responsible_person_or_role
  }
  users {
    text user_id PK
    text email UK
    text consent_reference
  }
  sensors {
    text sensor_id PK
    text category_id FK
    text station_id FK
    text organization_id FK
    date installation_date
    text administrative_status
    text identity_evidence_reference
  }
  channels {
    text channel_id PK
    text station_id FK
    text source_id FK
    text sensor_id FK
    text measurement_type FK
    jsonb source_key
    text catalog_basis
  }
  observations {
    text measurement_id PK
    text channel_id FK
    text source_id FK
    text source_version FK
    timestamptz observed_at
    text timestamp_role
    float value
    jsonb measurements
    text payload_hash
    text transformation_version
    text catalog_version
    text schema_version
    int integration_sample_count
    text zone_scope
  }
```

Este diagrama muestra atributos seleccionados, no sustituye el diccionario/DDL completo. `users` es independiente, sin FK. En la muestra histórica los maestros físicos quedaron vacíos; la entrega v2 sí carga `sensors`, `users` y `organizations` **sintéticos administrativos**, sin enlazarlos a canales observados. El trigger de fuente coherente es una restricción adicional, no otra FK. Las relaciones de `inventory_version` y unidad/tipo son las reales del DDL. Las UNIQUE compuestas y sus atributos NOT NULL están detallados en la auditoría formal; el dibujo no representa una restricción uno-a-uno por estación ni sensor.

## 4. Relación entre motores: coherencia, no FK cruzada

```mermaid
flowchart LR
  C[Contrato comun e IDs de Fase 5] --> P[SQL: catalogos normalizados y observations]
  C --> M[MongoDB: readings y copias versionadas]
  P --> V[Comparar membresia, IDs, payload y conteos]
  M --> V
  P -. SQL reconstruye DTO con vista .-> D[DTO comun]
  M -. Mongo conserva DTO desnormalizado .-> D
  V -. reconciliacion durable futura .-> L[Manifiesto de lotes propuesto]
```

No se modela `SQL → MongoDB` como FK, sincronización automática o transacción distribuida. La reconciliación durable entre escrituras parciales está propuesta, no implementada remotamente.

## 5. Fuentes principales y complementarias separadas

```mermaid
flowchart TD
  subgraph CORE[Nucleo propuesto: enero de 2025]
    A[Aire horario confirmado] --> R[Observaciones aceptadas]
    W[Meteorologia horaria] --> Q[Cuarentena: reloj no confirmado]
    T[Trafico: intervalo multivariable] --> Q
    I[Inventarios actuales de sitios] -. referencias con vigencia pendiente .-> R
  end
  R --> S[Muestra 5000 para SQL y MongoDB]
  subgraph EXTRA[Complementos: fuera de la muestra]
    X[Expedientes de accidentes 2026] -. propuesta .-> IC[incidents_2026]
    E[Consumo de energia mensual] -. propuesta .-> EC[energy_reports_monthly]
  end
  subgraph FUTURE[Dependencias no acreditadas]
    CO[CO2 ambiental: sin fuente]
    RT[Tiempos de recorrido: sin fuente]
    EV[Eventos y alertas: reglas y emisiones pendientes]
  end
```

No hay aristas de unión temporal entre 2026 y enero de 2025 ni conversión de mensual a horario. La ausencia de enlaces desde los nodos sin fuente es deliberada. Conteos y separaciones: [manifiesto de Fase 5](../../research/datasets/05_dataset_manifest.md).
