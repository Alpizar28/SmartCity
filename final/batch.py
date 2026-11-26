#!/usr/bin/python
# coding: utf-8
"""Hadoop Streaming: conteos por fuente, tipo y unidad. Compatible con Python 2 y 3."""
from __future__ import print_function
import json
import sys


def mapper(lines):
    for line in lines:
        row = json.loads(line)
        key = '|'.join([row['source_id'], row['measurement_type'], row['unit']])
        print(key + '\t1')


def activity_mapper(lines):
    for line in lines:
        row = json.loads(line)
        print('channel|%s|%s\t1' % (row['channel_id'], row['source_day'][:7]))
        if row['demo_event'] and row['zone_id']:
            print('event|%s\t1' % row['zone_id'])


def reducer(lines):
    """Streaming entrega las claves ordenadas."""
    previous = None
    total = 0
    for line in lines:
        key, value = line.rstrip('\n').split('\t')
        if previous is not None and key != previous:
            print(previous + '\t' + str(total))
            total = 0
        previous = key
        total += int(value)
    if previous is not None:
        print(previous + '\t' + str(total))


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('map', 'map-activity', 'reduce'):
        raise SystemExit('Usage: batch.py map|map-activity|reduce')
    if sys.argv[1] == 'map':
        mapper(sys.stdin)
    elif sys.argv[1] == 'map-activity':
        activity_mapper(sys.stdin)
    else:
        reducer(sys.stdin)
