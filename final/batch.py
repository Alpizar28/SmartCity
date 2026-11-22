#!/usr/bin/python
"""Hadoop Streaming: conteos por fuente/tipo/unidad, Python 2/3 compatible.

El modo MapReduce local sigue siendo MapReduce real, no YARN distribuido.
"""
from __future__ import print_function
import json
import sys


# Qué hace: lee cada observación y suelta la llave fuente|tipo|unidad con un 1.
def mapper(lines):
    for line in lines:
        row = json.loads(line)
        key = '|'.join([row['source_id'], row['measurement_type'], row['unit']])
        print(key + '\t1')


# Qué hace: suma los 1 de cada llave. Ocupa que las líneas ya vengan ordenadas.
def reducer(lines):
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
    if len(sys.argv) != 2 or sys.argv[1] not in ('map', 'reduce'):
        raise SystemExit('Usage: batch.py map|reduce')
    if sys.argv[1] == 'map':
        mapper(sys.stdin)
    else:
        reducer(sys.stdin)
