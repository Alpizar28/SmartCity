"""Panel inicial del laboratorio final.

TODO(Kembly): mapa (SP10; el CRS no está verificado), más gráficos y filtros,
consultas nativas PG/MG, inventario HDFS en vivo y estilo. CO₂, energía horaria,
tiempo de recorrido y sensores físicos siguen en «no disponible».
"""
import json
import os
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(os.environ.get('SMARTCITY_SPARK_OUTPUT', str(ROOT / 'data/spark-cluster-20261111')))
HDFS_REPORT = Path(os.environ.get('SMARTCITY_HDFS_REPORT', str(ROOT / 'data/hdfs-upload.json')))
BATCH_REPORT = Path(os.environ.get('SMARTCITY_BATCH_REPORT', str(ROOT / 'data/hadoop-batch.json')))
UNAVAILABLE = (
    {'indicador': 'CO₂', 'valor': 'no disponible',
     'motivo': 'La generación no incluye emisiones de CO₂.'},
    {'indicador': 'Energía horaria', 'valor': 'no disponible',
     'motivo': 'No hay serie horaria de energía ni desglose por zona.'},
    {'indicador': 'Tiempo de recorrido', 'valor': 'no disponible',
     'motivo': 'El tráfico publicado no trae tiempo de recorrido.'},
    {'indicador': 'Sensores físicos', 'valor': 'no disponible',
     'motivo': 'El canal administrativo no está ligado a un sensor físico.'},
)
TECHNOLOGIES = ('PostgreSQL', 'MongoDB', 'HDFS / MapReduce', 'Spark')


# Qué hace: abre el summary.json de Spark. Si no está, devuelve None y el panel no inventa números.
def load_summary(output):
    path = Path(output) / 'summary.json'
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


# Qué hace: arma la etiqueta de origen según la tecnología. Si no hay consulta real, lo dice.
def origin_label(technology, summary):
    if technology == 'Spark':
        if not summary:
            return 'Spark: sin salida materializada'
        if summary.get('data_origin'):
            return 'Spark: ' + str(summary['data_origin'])
        return 'Spark: observado (aire y tráfico de Madrid, generación analítica)'
    if technology == 'PostgreSQL':
        return 'PostgreSQL: el panel todavía no consulta el motor'
    if technology == 'MongoDB':
        return 'MongoDB: el panel todavía no consulta la colección'
    return 'HDFS / MapReduce: evidencia guardada, no una consulta en vivo'


# Qué hace: saca la lista de tipos de medición, ordenada, para el filtro.
def measurements(categories):
    return sorted({row['measurement_type'] for row in categories})


# Qué hace: cuenta observaciones y promedio solo de la medición que usted eligió.
def kpis(categories, measurement):
    rows = [row for row in categories if row.get('measurement_type') == measurement]
    if not rows:
        return None
    count = sum(int(row['count']) for row in rows)
    total = sum(float(row['total_value']) for row in rows)
    return {'observaciones': count, 'promedio': total / count, 'unidad': rows[0].get('unit')}


# Qué hace: junta la serie diaria de esa medición y calcula el promedio de cada día.
def daily_series(rows, measurement):
    buckets = {}
    for row in rows:
        if row.get('measurement_type') != measurement:
            continue
        day = str(row['source_day'])[:10]
        bucket = buckets.setdefault(day, {'source_day': day, 'count': 0, 'total_value': 0.0})
        bucket['count'] += int(row['count'])
        bucket['total_value'] += float(row['total_value'])
    series = []
    for day in sorted(buckets):
        bucket = buckets[day]
        series.append({'source_day': day, 'count': bucket['count'],
                       'mean': bucket['total_value'] / bucket['count']})
    return series


# Qué hace: lee un parquet de la salida de Spark y lo deja como lista de filas. Streamlit lo guarda en caché.
@st.cache_data
def read_product(output_dir, name, fingerprint):
    return pq.read_table(Path(output_dir) / name).to_pylist()


# Qué hace: muestra un informe ya guardado (HDFS o MapReduce). Si el archivo no está, no se inventa el contenido.
def show_saved_report(path, title):
    st.caption(title)
    if not path.is_file():
        st.info('No hay evidencia en ' + str(path) + '.')
        return
    evidence = json.loads(path.read_text(encoding='utf-8'))
    for key in ('mode', 'files', 'blocks', 'counts'):
        if key in evidence:
            st.text(key)
            st.code(str(evidence[key]), language='text')


# Qué hace: pinta los KPI, los dos gráficos de Spark y la tabla, filtrados por la medición elegida.
def show_spark(summary):
    if not summary or summary.get('status') not in ('PASS', 'PASS_SAMPLE'):
        st.info('No hay una salida Spark usable en ' + str(OUTPUT) + '. No se muestran cifras de relleno.')
        return
    if summary.get('status') == 'PASS_SAMPLE':
        st.warning('Esta salida está por debajo de 1.000.000 de registros. No es la evidencia académica.')
    fingerprint = (OUTPUT / 'summary.json').stat().st_mtime_ns
    categories = read_product(str(OUTPUT), 'SP08_categories', fingerprint)
    daily = read_product(str(OUTPUT), 'SP03_daily', fingerprint)
    selected = st.selectbox('Medición', measurements(categories))
    figures = kpis(categories, selected)
    if figures is None:
        st.info('No hay observaciones para ese filtro.')
        return
    series = daily_series(daily, selected)
    first, second, third = st.columns(3)
    first.metric('Observaciones', f'{figures["observaciones"]}')
    second.metric('Promedio · ' + str(figures['unidad']), f'{figures["promedio"]:.2f}')
    third.metric('Días en la serie', f'{len(series)}')
    counts = [{'measurement_type': row['measurement_type'], 'count': int(row['count'])}
              for row in sorted(categories, key=lambda row: row['measurement_type'])]
    st.subheader('Conteos por medición')
    st.caption('Origen: Spark SP08.')
    st.bar_chart(pd.DataFrame(counts), x='measurement_type', y='count')
    st.subheader('Promedio diario de la medición elegida')
    st.caption('Origen: Spark SP03. El filtro de medición sí se aplica.')
    if series:
        st.line_chart(pd.DataFrame(series), x='source_day', y='mean')
    st.subheader('Tabla')
    st.caption('Origen: Spark SP03, agregada por día para la medición elegida.')
    st.dataframe(pd.DataFrame(series), hide_index=True)


st.set_page_config(page_title='SmartCity — panel inicial', layout='wide')
st.title('SmartCity')
st.caption('Panel inicial. Kembly completa mapa, filtros, consultas nativas y estilo.')
summary = load_summary(OUTPUT)
technology = st.selectbox('Tecnología', list(TECHNOLOGIES), index=list(TECHNOLOGIES).index('Spark'))
st.caption('Origen: ' + origin_label(technology, summary))
st.subheader('Sin cobertura en el dataset')
columns = st.columns(len(UNAVAILABLE))
for column, item in zip(columns, UNAVAILABLE):
    column.metric(item['indicador'], item['valor'])
    column.caption(item['motivo'])
if technology == 'Spark':
    show_spark(summary)
elif technology == 'HDFS / MapReduce':
    st.info('Esta vista no calcula indicadores. Muestra la evidencia ya guardada del laboratorio.')
    show_saved_report(HDFS_REPORT, 'Carga HDFS')
    show_saved_report(BATCH_REPORT, 'Conteos MapReduce')
elif technology == 'PostgreSQL':
    st.info('PostgreSQL todavía no se consulta desde este panel.')
else:
    st.info('MongoDB todavía no se consulta desde este panel.')
