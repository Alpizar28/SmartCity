# Modelo E-R definitivo — PostgreSQL Madrid v2

Autoridad: [DDL normalizado](../../sprint1/postgres/schema_v2_3nf.sql).
Se conservan las doce entidades del núcleo y se incorporan dos tablas auxiliares:
`sensor_types` y `channel_sensors`. El esquema contiene **catorce tablas** y
diecisiete FK. Las vistas de compatibilidad no son tablas adicionales.

Cada padre admite cero a muchos hijos; una referencia opcional admite cero o un
padre por hijo. La PK de `channel_sensors` limita cada canal a una asignación.
El esquema de práctica `sprint1.readings(storage_id)` y el modelo histórico de
doce tablas están separados de esta versión.

```mermaid
erDiagram
  sources ||..o{ source_versions : source_id
  zones o|..o{ zones : parent_zone_id
  zones o|..o{ locations : zone_id
  source_versions o|..o{ locations : inventory_version
  locations o|..o{ stations : location_id
  sources ||..o{ stations : source_id
  sources ||..o{ measurement_types : source_id
  sensor_categories ||..o{ sensor_types : category_id
  sensor_types o|..o{ sensors : sensor_type
  stations ||..o{ sensors : station_id
  organizations o|..o{ sensors : organization_id
  stations ||..o{ channels : station_id
  measurement_types ||..o{ channels : measurement_type
  channels ||..o| channel_sensors : channel_id
  sensors ||..o{ channel_sensors : sensor_id
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
    text parent_zone_id FK
  }
  locations {
    text location_id PK
    text zone_id FK
    text name
    double_precision latitude
    double_precision longitude
    text coordinate_crs
    boolean historical_location_verified
    text inventory_version FK
  }
  stations {
    text station_id PK
    text source_id FK
    text source_key
    text name
    text location_id FK
    boolean inventory_present
  }
  sensor_categories {
    text category_id PK
    text name
  }
  measurement_types {
    text measurement_type PK
    text source_id FK
    text code
    text unit
    text candidate_unit
    text unit_status
  }
  organizations {
    text organization_id PK
    text name
    text responsible_person_or_role
    text evidence_reference
    text data_origin
    jsonb provenance
  }
  users {
    text user_id PK
    text name
    text email UK
    text consent_reference
    boolean demo_only
    text data_origin
  }
  sensor_types {
    text sensor_type PK
    text name
    text category_id FK
    text data_origin
    text evidence_reference
  }
  sensors {
    text sensor_id PK
    text name
    text sensor_type FK
    text station_id FK
    date installation_date
    text administrative_status
    timestamptz status_effective_at
    text organization_id FK
    text identity_evidence_reference
    text data_origin
    jsonb provenance
  }
  channels {
    text channel_id PK
    text station_id FK
    jsonb source_key
    text measurement_type FK
    text catalog_basis
  }
  channel_sensors {
    text channel_id PK,FK
    text sensor_id FK
  }
  observations {
    text measurement_id PK
    text channel_id FK
    timestamptz observed_at
    double_precision value
    text source_version FK
    text payload_hash
    text transformation_method
    text transformation_version
    jsonb raw_locator
    jsonb source_key
    jsonb provenance
    text element_type
    jsonb measurements
    integer integration_sample_count
    text zone_scope
  }
```

## Relaciones y restricciones complementarias

- Estación y magnitud de un canal deben pertenecer a la misma fuente.
- Canal y snapshot de observación deben pertenecer a la misma fuente.
- Una asignación exige que canal y sensor compartan estación.
- Una zona local solo puede referenciar un distrito como padre.
- Las identidades de catálogo y los hechos observados son inmutables por UPDATE.
- `location_geography` obtiene distrito y zona; no repite distrito en ubicaciones.
- `observation_contract` reconstruye el DTO v2 sin recalcular identidades.

Las claves compuestas, los opcionales y las DF se documentan en
[normalización e impacto](../../sprint1/postgres/impacto_3nf.md). JSONB se considera
un dominio SQL tipado, sin afirmar normalización recursiva de sus componentes.
Los vínculos físicos desconocidos permanecen ausentes. Los catálogos demo no
acreditan dispositivos productores de las mediciones públicas.
