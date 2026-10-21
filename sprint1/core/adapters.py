"""Validated immutable DTO and pure storage projections, never database writes."""
from dataclasses import dataclass
from datetime import datetime
import json

from .contract import canonical, staging_key
from .validation import validate_document


@dataclass(frozen=True, init=False)
class ReadingDTO:
    """Store canonical JSON rather than a mutable nested dict.

    Construction always validates the frozen contract and catalog references.
    No historical-version conversion or scientific identity assignment occurs.
    """
    _json: str

    def __init__(self, document, catalogs):
        validate_document(document, catalogs)
        object.__setattr__(self, '_json', canonical(document))

    def document(self):
        return json.loads(self._json)

    def mongo_document(self):
        """BSON-ready values; PyMongo can encode the timezone-aware datetime.

        No ObjectId is assigned here. Mongo will assign its own staging locator.
        The fingerprint describes pre-storage canonical Extended JSON.
        """
        doc = self.document()
        doc.pop('storage_id', None)
        doc['staging_key'] = staging_key(doc)
        observed = doc.get('observed_at')
        if observed is not None:
            doc['observed_at'] = datetime.fromisoformat(observed['$date'].replace('Z', '+00:00'))
        return doc

    def postgres_record(self):
        """Column/value mapping, NOT SQL. Future writer must bind parameters.

        JSONB fields remain Python objects; a driver-specific Jsonb wrapper will
        be needed in the future authorized persistence layer.
        """
        doc = self.document()
        fields = ('source_id', 'source_version', 'channel_id', 'source_key',
                  'original_timezone', 'timestamp_role', 'timestamp_status',
                  'value', 'unit', 'unit_status', 'quality_flag', 'payload_hash',
                  'raw_reference', 'schema_version')
        record = {field: doc.get(field) for field in fields}
        record['original_time'] = datetime.fromisoformat(doc['original_time'])
        record['observed_at'] = self.mongo_document().get('observed_at')
        record['document'] = doc
        return record
