"""Canonical identities and explicit clock conversion, independent of Phase 5."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from zoneinfo import ZoneInfo

VERSION = 'madrid-draft-v1-frozen'
SOURCES = ('MAD-AIR', 'MAD-METEO', 'MAD-TRAFFIC')
ZONE = ZoneInfo('Europe/Madrid')
METHOD = 'sprint1-local-core-v1'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def stable_id(kind, *parts):
    return kind + ':' + sha256(canonical(['sca-id-v1', *parts]).encode()).hexdigest()


def payload_hash(document):
    """New staging fingerprint, not the historical Phase 5 payload algorithm.

    Local storage IDs and the fingerprint itself are not content. No scientific
    measurement identity is created from this hash.
    """
    content = {k: v for k, v in document.items() if k not in ('storage_id', 'payload_hash')}
    return 'payload:' + sha256(canonical(content).encode()).hexdigest()


def staging_key(document):
    """Local reconciliation tuple, not a scientific measurement identity."""
    return canonical([document['source_id'], document['source_version'],
                      document['channel_id'], document['source_key']])


def local_to_utc(local, fold=None):
    if local.tzinfo is not None:
        raise ValueError('expected_naive_original_time')
    if fold is not None and (type(fold) is not int or fold not in (0, 1)):
        raise ValueError('invalid_fold')
    candidates = {}
    for candidate in (0, 1):
        utc = local.replace(tzinfo=ZONE, fold=candidate).astimezone(timezone.utc)
        if utc.astimezone(ZONE).replace(tzinfo=None) == local:
            candidates[candidate] = utc
    if not candidates:
        raise ValueError('nonexistent_local_time')
    if len(set(candidates.values())) > 1 and fold is None:
        raise ValueError('ambiguous_local_time_requires_publisher_fold')
    return candidates[fold if fold is not None else min(candidates)]


def hourly_endpoint(day, hour):
    if type(hour) is not int or not 1 <= hour <= 24:
        raise ValueError('expected_H01_to_H24')
    return datetime.strptime(day, '%Y-%m-%d') + timedelta(hours=hour)
