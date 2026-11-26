"""Explorador de las mediciones de aire y tráfico de Madrid."""
from collections import Counter
from functools import lru_cache
from html import escape
import json
import logging
import os
from pathlib import Path
import re
import subprocess

import altair as alt
import pandas as pd
import pyarrow.parquet as pq
import streamlit as st
from psycopg import Error as PostgresError
from psycopg.errors import InvalidCatalogName, UndefinedTable
from pymongo.errors import PyMongoError

from final.manage import DEFAULT_ACTIVITY_REPORT, DEFAULT_BATCH_REPORT, DEFAULT_SPARK_OUTPUT, hdfs
from final.mongo import incident_coverage, incidents_by_category, measurement_extrema, query as mongo_query
from final import mongo_queries
from final.postgres import query as postgres_query
from final.postgres_normalized import TITLES as PG_TITLES, query as postgres_normalized_query

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(os.environ.get('SMARTCITY_SPARK_OUTPUT', DEFAULT_SPARK_OUTPUT))
BATCH_REPORT = Path(os.environ.get('SMARTCITY_BATCH_REPORT', DEFAULT_BATCH_REPORT))
ACTIVITY_REPORT = Path(os.environ.get('SMARTCITY_HADOOP_ACTIVITY_REPORT', DEFAULT_ACTIVITY_REPORT))
DISTRICTS = ROOT / 'sprint1/postgres/distritos_madrid.json'
MEASUREMENTS = {
    'MAD-AIR:8': 'Dióxido de nitrógeno (NO₂)',
    'MAD-AIR:14': 'Ozono (O₃)',
    'MAD-AIR:9': 'Partículas PM₂,₅',
    'MAD-AIR:10': 'Partículas PM₁₀',
    'MAD-AIR:1': 'Dióxido de azufre (SO₂)',
    'MAD-AIR:6': 'Monóxido de carbono (CO)',
    'MAD-AIR:7': 'Monóxido de nitrógeno (NO)',
    'MAD-AIR:12': 'Óxidos de nitrógeno (NOₓ)',
    'MAD-AIR:20': 'Tolueno',
    'MAD-AIR:30': 'Benceno',
    'MAD-AIR:35': 'Etilbenceno',
    'MAD-TRAFFIC:intensidad': 'Intensidad de tráfico',
}
UNITS = {'ug/m3': 'µg/m³', 'mg/m3': 'mg/m³'}
ENGINES = {'PostgreSQL': postgres_query, 'MongoDB': mongo_query}
ACCIDENTS = ('accidents', '')
HADOOP_COUNTS = ('hadoop_counts', '')
HADOOP_ACTIVITY = {
    ('hadoop_channels', ''): 'Canales con más lecturas',
    ('hadoop_months', ''): 'Actividad mensual por canal',
    ('hadoop_events', ''): 'Eventos de demostración por distrito',
}
MONGO_EXTREMA = ('mongo_extrema', '')
PG_OPTIONS = {(code, ''): title for code, title in PG_TITLES.items()}
MG_OPTIONS = {(code, ''): title for code, title in mongo_queries.TITLES.items()}
SPARK_VIEWS = {
    ('spark_channels', ''): ('Canales con más lecturas', 'SP01_channels'),
    ('spark_events', ''): ('Eventos de demostración por distrito', 'SP02_events'),
    ('spark_zones', ''): ('Lecturas por distrito', 'SP05_zones'),
    ('spark_trends', ''): ('Tendencia de siete días', 'SP06_trends'),
    ('spark_categories', ''): ('Distribución por tipo de medición', 'SP08_categories'),
    ('spark_anomalies', ''): ('Anomalías por medición', 'SP07_anomalies'),
    ('spark_correlation', ''): ('Correlación entre NO₂ y ozono', 'SP04_correlation'),
    ('spark_comparison', ''): ('Comparación entre 2025 y 2026', 'SP09_comparison'),
}
DAILY_COLUMNS = ['source_day', 'measurement_type', 'unit', 'zone_id', 'count', 'total_value']
AIR_COLOR = '#2451c6'
TRAFFIC_COLOR = '#bc4530'

STYLE = """
<style>
.stMainBlockContainer { max-width: 1120px; padding-top: 4.5rem; padding-bottom: 3rem; }
.st-key-intro { gap: 0.5rem; padding-bottom: 1rem; border-bottom: 1px solid #dfded7; }
.st-key-intro h1 {
    font-weight: 400; font-size: clamp(2.75rem, 6vw, 4rem);
    line-height: 1.12; letter-spacing: -0.04em; padding: 0 0 0.25rem;
}
.city { font-size: 0.875rem; font-weight: 600; margin: 0; }
.city::before {
    content: ""; display: inline-block; width: 1rem; height: 0.25rem;
    margin-right: 0.5rem; vertical-align: middle; background: #e1a522;
}
.st-key-filters { padding: 0.5rem 0; }
.st-key-results { background: #fff; }
.st-key-results h2 { font-size: 1.375rem; font-weight: 600; padding: 0; }
.st-key-metrics [data-testid="stMetric"] { text-align: center; }
.st-key-metrics [data-testid="stMetricLabel"] { display: flex; justify-content: center; }
.st-key-metrics [data-testid="stMetricLabel"] p { white-space: normal; }
.st-key-metrics [data-testid="stMetricValue"] {
    font-family: monospace; font-size: clamp(1.125rem, 3vw, 1.875rem);
}
.daily-table { width: 100%; border-collapse: collapse; }
.daily-table th, .daily-table td { padding: 0.5rem; text-align: right; border-bottom: 1px solid #dfded7; }
.daily-table th:first-child, .daily-table td:first-child { text-align: left; }
.daily-table td { font-family: monospace; }
.count-bars { list-style: none; margin: 0; padding: 0; }
.count-bars li { padding: 0 0 0.75rem; }
.count-bars .label { display: flex; justify-content: space-between; gap: 0.75rem; }
.count-bars .label span:last-child { font-family: monospace; white-space: nowrap; }
.count-bars .track { height: 0.375rem; margin-top: 0.25rem; background: #eceef4; border-radius: 4px; }
.count-bars .bar { display: block; height: 100%; border-radius: inherit; }
@media (max-width: 640px) {
    .stMainBlockContainer { padding: 4.5rem 1rem 2rem; }
    .st-key-metrics [data-testid="stHorizontalBlock"] {
        display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.5rem;
    }
    .st-key-metrics [data-testid="stColumn"] { min-width: 0; width: 100%; }
}
</style>
"""


def number(value, decimals=0):
    return f'{value:,.{decimals}f}'.translate(str.maketrans({',': '.', '.': ','}))


def date_label(value):
    return value.strftime('%d/%m/%Y')


@lru_cache(maxsize=1)
def district_names():
    return json.loads(DISTRICTS.read_text(encoding='utf-8'))['names']


def district_label(zone):
    return district_names().get(zone, zone).title() if zone is not None else 'Todos los distritos'


def measurement_options(rows):
    return sorted(set(zip(rows['measurement_type'], rows['unit'])))


def show_table(table):
    st.html(table.to_html(index=False, border=0, classes='daily-table', na_rep='No disponible'))


def show_counts(counts, color, proportional=False):
    values = [count for _, count in counts]
    scale = sum(values) if proportional else max(values)
    if not scale:
        scale = 1
    items = []
    for label, count in counts:
        value = f'{number(count / scale * 100, 1)} %' if proportional else number(count)
        items.append(f'<li><div class="label"><span>{escape(label)}</span><span>{value}</span></div>'
                     f'<div class="track" aria-hidden="true"><span class="bar" '
                     f'style="width:{count / scale:.2%};background:{color}"></span></div></li>')
    st.html('<ul class="count-bars">' + ''.join(items) + '</ul>')


@st.cache_data(max_entries=4)
def read_daily(output, fingerprint):
    rows = pq.read_table(output / 'SP03_daily', columns=DAILY_COLUMNS).to_pandas()
    rows['source_day'] = pd.to_datetime(rows['source_day'])
    return rows


@st.cache_data(ttl=60, max_entries=32, show_spinner=False)
def query_daily(engine, measurement, unit, start, end, zone):
    rows = pd.DataFrame.from_records(ENGINES[engine](measurement, start, end, zone),
                                     columns=['source_day', 'unit', 'count', 'total_value'])
    rows['source_day'] = pd.to_datetime(rows['source_day'])
    return rows[rows['unit'].eq(unit)]


def daily_series(rows):
    series = rows.groupby('source_day', as_index=True)[['count', 'total_value']].sum()
    series['mean'] = series['total_value'] / series['count']
    return series


def trend_chart(series, start, end, unit, color, *, value_label='Promedio'):
    # Los días sin lecturas quedan como huecos.
    days = pd.date_range(start, end, name='source_day')
    points = series.reindex(days).reset_index()
    points['date_label'] = points['source_day'].map(date_label)
    points['mean_label'] = points['mean'].map(lambda value: number(value, 2), na_action='ignore')
    points['count_label'] = points['count'].map(number, na_action='ignore')
    axis_format = '%d/%m/%y' if (end - start).days > 365 else '%d/%m'
    base = alt.Chart(points).encode(
        x=alt.X('source_day:T', title=None, scale=alt.Scale(type='utc'),
                axis=alt.Axis(format=axis_format, tickCount=5, labelOverlap='greedy', grid=False)),
        y=alt.Y('mean:Q', title=unit, scale=alt.Scale(zero=False),
                axis=alt.Axis(tickCount=5, labelExpr=(
                    "replace(replace(replace(format(datum.value, ',~f'), /,/g, '·'), '.', ','), /·/g, '.')"
                ))),
    )
    line = base.mark_line(color=color, strokeWidth=2, point=len(series) == 1)
    nearest = alt.selection_point(fields=['source_day'], nearest=True, on='pointerover',
                                  empty=False, clear='pointerout')
    tooltip = [
        alt.Tooltip('date_label:N', title='Fecha'),
        alt.Tooltip('mean_label:N', title=f'{value_label} ({unit})'),
        alt.Tooltip('count_label:N', title='Lecturas'),
    ]
    hover = (base.transform_filter('isValid(datum.mean)').mark_point(opacity=0)
             .encode(tooltip=tooltip).add_params(nearest))
    focus = base.mark_circle(color=color, size=48).transform_filter(nearest).encode(tooltip=tooltip)
    return ((line + hover + focus).properties(height=280)
            .configure_axis(labelFont='monospace', titleFont='monospace')
            .configure_view(stroke=None))


def show_results(rows, measurement, unit, start, end, engine):
    series = daily_series(rows)
    with st.container(border=True, key='results'):
        st.header('Promedio diario', anchor=False)
        st.caption(f'{MEASUREMENTS.get(measurement, measurement)} · {date_label(start)}–{date_label(end)}')
        if series.empty:
            st.info('No hay lecturas para esta selección. Prueba otro periodo o distrito.')
            return
        count = series['count'].sum()
        mean = series['total_value'].sum() / count
        with st.container(key='metrics'):
            readings, average, days = st.columns(3)
            readings.metric('Lecturas', number(count))
            average.metric(f'Promedio ({unit})', number(mean, 2))
            days.metric('Días con datos', number(len(series)))
        color = TRAFFIC_COLOR if measurement.startswith('MAD-TRAFFIC:') else AIR_COLOR
        st.altair_chart(trend_chart(series, start, end, unit, color), width='stretch')
        origin = 'resultados procesados por Spark' if engine == 'Spark' else f'consulta directa a {engine}'
        st.caption(f'Fuente: {origin}. Cada lectura tiene el mismo peso en el promedio.')
    with st.expander('Ver datos diarios'):
        table = pd.DataFrame({
            'Fecha': series.index.map(date_label),
            f'Promedio ({unit})': series['mean'].map(lambda value: number(value, 2)).to_numpy(),
            'Lecturas': series['count'].map(number).to_numpy(),
        })
        search = st.text_input('Buscar por fecha', placeholder='Ej. 01/2025').strip()
        matches = table[table['Fecha'].str.contains(search, regex=False)] if search else table
        if matches.empty:
            st.info('No hay fechas que coincidan con la búsqueda.')
        else:
            with st.container(height=320, border=False):
                show_table(matches)


@st.cache_data(ttl=60, max_entries=32, show_spinner=False)
def incident_counts(start, end, zone):
    return incidents_by_category(start, end, zone)


def district_select(widget, zones, key):
    return widget.selectbox('Distrito', [None, *sorted(zones, key=district_label)],
                            format_func=district_label, key=key)


def show_accidents():
    try:
        coverage = incident_coverage()
    except (OSError, RuntimeError, PyMongoError):
        logging.exception('Error al consultar la cobertura de accidentes')
        st.error('No se pudo conectar con MongoDB. Comprueba que el servicio esté en marcha.')
        return
    if coverage is None:
        st.info('Todavía no hay un conjunto de accidentes cargado en MongoDB.')
        return

    first, last, zones = coverage
    with st.container(key='filters'):
        period, district = st.columns([2, 1])
        dates = period.date_input('Periodo', (first, last), min_value=first, max_value=last,
                                  format='DD/MM/YYYY', key='incident_period')
        zone = district_select(district, [zone for zone in zones if zone is not None], 'incident_district')
    if len(dates) != 2:
        st.info('Selecciona la fecha final para ver los accidentes.')
        return
    try:
        rows = incident_counts(*dates, zone)
    except (OSError, RuntimeError, PyMongoError):
        logging.exception('Error al agrupar accidentes por categoría')
        st.error('No se pudo consultar el recuento en MongoDB. Intenta de nuevo.')
        return
    with st.container(border=True, key='results'):
        st.header('Accidentes por categoría', anchor=False)
        st.caption(f'{date_label(dates[0])}–{date_label(dates[1])} · Un registro por accidente, no por persona')
        with st.container(key='metrics'):
            st.metric('Accidentes registrados', number(sum(row['count'] for row in rows)))
        if rows:
            show_counts([('Sin categoría' if row['_id'] == 'sin_categoria' else row['_id'], row['count'])
                         for row in rows], TRAFFIC_COLOR)
        else:
            st.info('No hay accidentes registrados para este periodo y distrito.')
        st.caption('Fuente: MongoDB · Incidentes registrados por categoría (MG08)')


def load_measurements():
    try:
        summary_file = OUTPUT / 'summary.json'
        summary = json.loads(summary_file.read_text(encoding='utf-8'))
        daily = (read_daily(OUTPUT, summary_file.stat().st_mtime_ns)
                 if summary.get('status') in ('PASS', 'PASS_SAMPLE') else pd.DataFrame())
    except (OSError, ValueError):
        daily = pd.DataFrame()
    return daily, not daily.empty and summary['status'] == 'PASS_SAMPLE'


def option_label(option):
    if option == ACCIDENTS:
        return 'Accidentes'
    if option == HADOOP_COUNTS:
        return 'Conteos por tipo de medición'
    if option in HADOOP_ACTIVITY:
        return HADOOP_ACTIVITY[option]
    if option == MONGO_EXTREMA:
        return 'Valores máximos y mínimos'
    if option in PG_OPTIONS:
        return PG_OPTIONS[option]
    if option in MG_OPTIONS:
        return MG_OPTIONS[option]
    if option in SPARK_VIEWS:
        return SPARK_VIEWS[option][0]
    measurement, unit = option
    return f'{measurement_label(measurement)} · {UNITS.get(unit, unit)}'


def measurement_label(measurement):
    return MEASUREMENTS.get(measurement, 'Temperatura demo' if measurement == 'demo:temperature' else measurement)


def show_postgres_query(selection):
    code = selection[0]
    with st.container(border=True, key='results'):
        st.header(PG_OPTIONS[selection], anchor=False)
        if code in ('PG07', 'PG08'):
            st.caption('Solo considera vínculos conocidos. Un vínculo desconocido no indica inactividad.')
        if code in ('PG01', 'PG02', 'PG03', 'PG04', 'PG05', 'PG06'):
            st.caption('Inventario administrativo sintético: no acredita sensores físicos.')
        try:
            with st.spinner('Consultando PostgreSQL…'):
                rows = postgres_normalized_query(code)
        except (InvalidCatalogName, UndefinedTable):
            st.info('Primero carga el modelo 3FN del laboratorio con `python -m final.postgres_normalized`.')
            return
        except (OSError, PostgresError):
            logging.exception('Error al ejecutar %s', code)
            st.error('No se pudo ejecutar la consulta. Comprueba que PostgreSQL esté en marcha.')
            return
        if rows:
            table = pd.DataFrame(rows).rename(columns={
                'sensor_type': 'Tipo', 'sensor_type_name': 'Nombre del tipo',
                'sensor_count': 'Sensores', 'station_id': 'Estación', 'location_id': 'ID de ubicación',
                'location_name': 'Ubicación', 'administrative_status': 'Estado',
                'organization_id': 'Organismo', 'name': 'Nombre', 'installation_year': 'Año',
                'sensor_id': 'Sensor', 'zone_id': 'Distrito', 'zone_rank': 'Puesto',
                'channel_id': 'Canal', 'readings': 'Lecturas', 'first_observed_at': 'Primera lectura (UTC)',
                'last_observed_at': 'Última lectura (UTC)', 'channel_count': 'Canales',
            })
            per_page = 15
            pages = (len(table) + per_page - 1) // per_page
            page = (st.number_input('Página', min_value=1, max_value=pages, step=1, key=f'page:{code}')
                    if pages > 1 else 1)
            offset = (page - 1) * per_page
            show_table(table.iloc[offset:offset + per_page])
            st.caption(f'{number(len(table))} filas')
        else:
            st.info('La consulta no encontró filas con los criterios de este conjunto de datos.')
        st.caption(f'Fuente: PostgreSQL · modelo normalizado · {code}')


@st.cache_data(ttl=60, max_entries=32, show_spinner=False)
def read_mongo_query(code, params):
    return mongo_queries.query(code, **params)


def mongo_filters(code, daily):
    if code == 'MG01':
        sensors = {row['_id']: row['name'] for row in mongo_queries.sensors()}
        return {'sensor': st.selectbox('Sensor de demostración', sensors, format_func=sensors.get)}
    if code not in ('MG02', 'MG04', 'MG06', 'MG10'):
        return {}
    if daily.empty:
        st.info('Primero genera la salida Spark para obtener la cobertura de las mediciones.')
        return None
    available = daily
    if code == 'MG06':
        available = available[available['zone_id'].notna()]
    if code == 'MG04':
        available = available[available['measurement_type'].eq('MAD-TRAFFIC:intensidad')]
    if available.empty:
        st.info('No hay mediciones compatibles con esta consulta.')
        return None
    options = measurement_options(available)
    if code == 'MG04':
        measurement, unit = options[0]
    else:
        measurement, unit = st.selectbox('Variable', options, format_func=option_label, key=f'variable:{code}')
    selected = available[available['measurement_type'].eq(measurement) & available['unit'].eq(unit)]
    first, last = selected['source_day'].min().date(), selected['source_day'].max().date()
    period, extra = st.columns([2, 1])
    dates = period.date_input('Periodo', (first, last), min_value=first, max_value=last,
                              format='DD/MM/YYYY', key=f'mongo-period:{code}:{measurement}:{unit}')
    params = {'measurement': measurement, 'unit': unit}
    zones = selected['zone_id'].dropna().unique()
    if len(zones) and code == 'MG10':
        params['zone'] = district_select(extra, zones, f'mongo-zone:{code}')
    if code == 'MG10':
        params['minimum'] = st.number_input(
            f'Valor mínimo ({UNITS.get(unit, unit)})', value=0.0, key=f'mongo-min:{measurement}:{unit}')
    if len(dates) != 2:
        st.info('Selecciona la fecha final para ejecutar la consulta.')
        return None
    return dict(params, start=dates[0], end=dates[1])


def show_mongo_query(selection, daily):
    code = selection[0]
    with st.container(border=True, key='results'):
        st.header(MG_OPTIONS[selection], anchor=False)
        st.caption(mongo_queries.NOTES[code])
        try:
            params = mongo_filters(code, daily)
            if params is None:
                return
            with st.spinner('Consultando MongoDB…'):
                rows = read_mongo_query(code, params)
        except mongo_queries.DemoNotLoaded:
            st.info('Primero carga las demostraciones con `python -m final.mongo_queries`.')
            return
        except (OSError, RuntimeError, PyMongoError):
            logging.exception('Error al ejecutar %s en MongoDB', code)
            st.error('No se pudo ejecutar la consulta. Comprueba MongoDB o prueba con un periodo más corto.')
            return
        if rows:
            labels = {
                'source_day': 'Fecha local', 'observed_at': 'Instante UTC', 'station_name': 'Estación',
                'zone_id': 'Distrito', 'source_id': 'Origen de datos', 'measurement_type': 'Medición',
                'device_type': 'Tipo de sensor', 'value': 'Valor', 'count': 'Lecturas', 'mean': 'Promedio',
                'unit': 'Unidad',
            }
            if code == 'MG05':
                labels['count'] = 'Alertas demo'
            records = []
            for row in rows:
                fields = {**row.get('_id', {}), **{key: value for key, value in row.items() if key != '_id'}}
                if 'zone_id' in fields and fields['zone_id'] is not None:
                    fields['zone_id'] = district_label(fields['zone_id'])
                if 'measurement_type' in fields:
                    fields['measurement_type'] = measurement_label(fields['measurement_type'])
                if 'source_day' in fields:
                    fields['source_day'] = date_label(pd.Timestamp(fields['source_day']))
                if code == 'MG06':
                    fields['unit'] = params['unit']
                if 'unit' in fields:
                    fields['unit'] = UNITS.get(fields['unit'], fields['unit'])
                for field, decimals in (('value', 2), ('mean', 2), ('count', 0)):
                    if field in fields:
                        fields[field] = number(fields[field], decimals)
                records.append(fields)
            table = pd.DataFrame(records).rename(columns=labels)
            with st.container(height=min(340, 64 + len(rows) * 40), border=False):
                show_table(table)
        else:
            st.info('No hay resultados para esta selección.')
        st.caption(f'Fuente: MongoDB · {code}')


@st.cache_data(ttl=60, max_entries=8, show_spinner=False)
def read_batch_counts(destination):
    rows = []
    for line in hdfs('dfs', '-cat', destination + '/part-*').splitlines():
        key, count = line.split('\t')
        rows.append((key.split('|'), int(count)))
    return rows


def show_hadoop(selection):
    by_type = selection == HADOOP_COUNTS
    report_path, job = (BATCH_REPORT, 'counts') if by_type else (ACTIVITY_REPORT, 'activity')
    try:
        report = json.loads(report_path.read_text(encoding='utf-8'))
        destination = report.get('destination')
        if (report.get('status') != 'EXECUTED' or not isinstance(destination, str)
                or not re.fullmatch(rf'/smartcity/batch-{job}-\d{{8}}T\d{{6}}', destination)):
            raise ValueError('Invalid MapReduce output path')
        with st.spinner('Leyendo el resultado en HDFS…'):
            rows = read_batch_counts(destination)
    except FileNotFoundError:
        st.info('El trabajo MapReduce aún no tiene resultados disponibles.')
        return
    except (OSError, ValueError, subprocess.SubprocessError):
        logging.exception('Error al consultar HDFS')
        st.error('No se pudo leer el resultado de MapReduce en HDFS. Comprueba el laboratorio y el informe de la carga batch.')
        return
    with st.container(border=True, key='results'):
        st.header(option_label(selection), anchor=False)
        if by_type:
            counts = [(option_label((measurement, unit)), count)
                      for (_, measurement, unit), count in rows]
            counts.sort(key=lambda item: (-item[1], item[0]))
            with st.container(key='metrics'):
                st.metric('Lecturas procesadas', number(sum(count for _, count in counts)))
        elif selection[0] == 'hadoop_events':
            counts = [(district_label(key[1]), count) for key, count in rows if key[0] == 'event']
            counts.sort(key=lambda item: (-item[1], item[0]))
            st.caption('Eventos con distrito asignado derivados de la regla demo de tráfico. No son accidentes ni avisos oficiales.')
        else:
            channels = [(key[1], key[2], count) for key, count in rows if key[0] == 'channel']
            totals = Counter()
            for channel, _, count in channels:
                totals[channel] += count
            labels = hadoop_channel_labels()
            if selection[0] == 'hadoop_channels':
                counts = [(labels.get(channel, channel), count) for channel, count in totals.most_common(15)]
                st.caption('Los 15 canales con más lecturas de toda la carga. Un canal no equivale a un sensor físico.')
            elif totals:
                channel = st.selectbox('Canal', [key for key, _ in totals.most_common()],
                                       format_func=lambda key: labels.get(key, key))
                counts = [(month, count) for key, month, count in channels if key == channel]
                counts.sort()
                st.caption('Lecturas por mes en el canal seleccionado. Solo se muestran meses con datos.')
            else:
                counts = []
        if counts and any(count for _, count in counts):
            show_counts(counts, TRAFFIC_COLOR if selection[0] == 'hadoop_events' else AIR_COLOR)
        else:
            st.info('MapReduce no devolvió conteos para esta consulta.')
        st.caption('Fuente: Hadoop MapReduce · conteos leídos de HDFS')


def hadoop_channel_labels():
    try:
        summary = (OUTPUT / 'summary.json').stat()
        channels = read_spark_view(OUTPUT, 'SP01_channels', summary.st_mtime_ns)
    except (OSError, ValueError):
        return {}
    # Spark aporta los nombres; los conteos vienen de HDFS.
    return {row.channel_id: (
        f'{row.station_name or "Estación sin nombre"} · {option_label((row.measurement_type, row.unit))}'
        f' · {row.channel_id[-8:]}'
    ) for row in channels.itertuples(index=False)}


@st.cache_data(max_entries=12)
def read_spark_view(output, product, fingerprint):
    return pq.read_table(output / product).to_pandas()


def show_spark_analysis(selection):
    title, product = SPARK_VIEWS[selection]
    try:
        data = read_spark_view(OUTPUT, product, (OUTPUT / 'summary.json').stat().st_mtime_ns)
    except (OSError, ValueError):
        st.info('Este resultado todavía no está disponible. Comprueba la salida del trabajo Spark.')
        return
    with st.container(border=True, key='results'):
        st.header(title, anchor=False)
        kind = selection[0]
        origin = f'Fuente: Spark · {product.split("_", 1)[0]}'
        if kind == 'spark_trends':
            if data.empty:
                st.info('No hay datos para calcular una tendencia.')
            else:
                options = measurement_options(data)
                measurement, unit = st.selectbox('Medición de la tendencia', options, format_func=option_label)
                selected = data[data['measurement_type'].eq(measurement) & data['unit'].eq(unit)]
                zones = selected['zone_id'].dropna().unique()
                if len(zones):
                    zone = st.selectbox('Distrito', sorted(zones, key=district_label),
                                        format_func=district_label,
                                        key='trend_district')
                    selected = selected[selected['zone_id'].eq(zone)]
                else:
                    selected = selected[selected['zone_id'].isna()]
                series = (selected.assign(source_day=pd.to_datetime(selected['source_day']))
                          .set_index('source_day').sort_index()[['count', 'rolling_7d']]
                          .rename(columns={'rolling_7d': 'mean'}))
                start, end = series.index.min().date(), series.index.max().date()
                color = TRAFFIC_COLOR if measurement.startswith('MAD-TRAFFIC:') else AIR_COLOR
                st.altair_chart(trend_chart(series, start, end, UNITS.get(unit, unit), color,
                                           value_label='Promedio móvil'), width='stretch')
                st.caption('Promedio ponderado por lecturas de los últimos siete días. El conteo al pasar por la gráfica corresponde a ese día.')
            st.caption(origin)
            return
        if kind == 'spark_correlation':
            result = data.iloc[0] if not data.empty else None
            if result is None or pd.isna(result['pearson_no2_ozone']):
                st.info('No hay pares suficientes para calcular una correlación.')
            else:
                correlation, pairs = st.columns(2)
                correlation.metric('Correlación de Pearson', number(result['pearson_no2_ozone'], 3))
                pairs.metric('Pares de lecturas', number(result['paired_hours']))
                st.caption('Pares de NO₂ y ozono de la misma estación y hora. Correlación no implica causalidad.')
            st.caption(origin)
            return
        if kind == 'spark_comparison':
            if data.empty:
                st.info('No hay lecturas comparables entre los dos años.')
            else:
                options = measurement_options(data)
                measurement, unit = st.selectbox('Medición comparada', options, format_func=option_label)
                matched = data[data['measurement_type'].eq(measurement) & data['unit'].eq(unit)]
                matched = matched.sort_values('source_month')
                table = pd.DataFrame({
                    'Mes': matched['source_month'].map(lambda month: f'{month:02d}'),
                    '2025': matched['mean_2025'].map(lambda value: number(value, 2)),
                    '2026': matched['mean_2026'].map(lambda value: number(value, 2)),
                    'Cambio': matched['delta'].map(lambda value: number(value, 2)),
                    'Pares': matched['paired_channel_hours'].map(number),
                })
                st.caption(f'Promedios en {UNITS.get(unit, unit)} de enero a agosto. Solo se comparan lecturas del mismo canal y franja horaria.')
                show_table(table)
            st.caption(origin)
            return
        if kind in ('spark_zones', 'spark_events'):
            counts = data.groupby('zone_id')['count'].sum().sort_values(ascending=False)
            rows = [(district_label(zone), count) for zone, count in counts.items()]
            if kind == 'spark_events':
                st.caption('Lecturas superiores a 2.000 veh/h con distrito asignado. Son eventos de una regla demo, no accidentes ni alertas oficiales.')
            else:
                st.caption('Solo incluye lecturas con un distrito asignado. No es un ranking de contaminación.')
        elif kind == 'spark_channels':
            top = data.sort_values(['count', 'channel_id'], ascending=[False, True]).head(15)
            rows = [(f'{row.station_name or row.channel_id} · {option_label((row.measurement_type, row.unit))}',
                     row.count) for row in top.itertuples(index=False)]
            st.caption('Los 15 canales con más lecturas. Un canal no equivale a un sensor físico.')
        else:
            if kind == 'spark_anomalies':
                years = sorted(data['source_year'].unique(), reverse=True)
                if years:
                    year = st.selectbox('Año', years)
                    data = data[data['source_year'].eq(year)]
                field = 'anomaly_count'
                st.caption('Lecturas a más de tres desviaciones estándar de la media de su canal. No son alertas oficiales.')
            else:
                field = 'count'
                st.caption('Porcentaje de lecturas por tipo de medición en toda la carga.')
            rows = [(option_label((row.measurement_type, row.unit)), getattr(row, field))
                    for row in data.sort_values(field, ascending=False).itertuples(index=False)]
        if rows:
            show_counts(rows, TRAFFIC_COLOR if kind in ('spark_zones', 'spark_events') else AIR_COLOR,
                        proportional=kind == 'spark_categories')
        else:
            st.info('No hay resultados para esta consulta.')
        st.caption(origin)


@st.cache_data(ttl=60, max_entries=32, show_spinner=False)
def extrema(measurement, unit, start, end, zone):
    return measurement_extrema(measurement, unit, start, end, zone)


def show_measurements(daily, measurement, unit, engine, *, show_extrema=False):
    with st.container(key='filters'):
        selected = daily[daily['measurement_type'].eq(measurement) & daily['unit'].eq(unit)]
        first = selected['source_day'].min().date()
        last = selected['source_day'].max().date()
        zones = selected['zone_id'].dropna().unique()
        if len(zones):
            period, district = st.columns([2, 1])
            zone = district_select(district, zones, 'district')
        else:
            period, zone = st.container(), None
        dates = period.date_input('Periodo', (first, last), min_value=first, max_value=last,
                                  format='DD/MM/YYYY', key=f'period:{measurement}:{unit}')
    if len(dates) != 2:
        st.info('Selecciona la fecha final para ver el promedio diario.')
        return
    start, end = dates
    if show_extrema:
        with st.container(border=True, key='results'):
            st.header('Valores máximos y mínimos', anchor=False)
            st.caption(f'{option_label((measurement, unit))} · {date_label(start)}–{date_label(end)}')
            try:
                with st.spinner('Consultando MongoDB…'):
                    result = extrema(measurement, unit, start, end, zone)
            except (OSError, RuntimeError, PyMongoError):
                logging.exception('Error al consultar extremos en MongoDB')
                st.error('No se pudo consultar MongoDB. Comprueba el servicio o elige un periodo más corto.')
                return
            if result:
                minimum, maximum, readings = st.columns(3)
                minimum.metric('Mínimo', number(result['min'], 2))
                maximum.metric('Máximo', number(result['max'], 2))
                readings.metric('Lecturas', number(result['count']))
            else:
                st.info('No hay lecturas para esta selección.')
            st.caption('Fuente: MongoDB · valores máximos y mínimos registrados (MG03)')
        return
    if engine == 'Spark':
        rows = selected[selected['source_day'].between(pd.Timestamp(start), pd.Timestamp(end))]
        if zone is not None:
            rows = rows[rows['zone_id'].eq(zone)]
    else:
        try:
            with st.spinner(f'Consultando {engine}…'):
                rows = query_daily(engine, measurement, unit, start, end, zone)
        except (OSError, RuntimeError, PostgresError, PyMongoError):
            logging.exception('Error al consultar %s', engine)
            st.error(f'No se pudo consultar {engine}. Comprueba que el servicio esté en marcha o elige Spark.')
            return
    show_results(rows, measurement, UNITS.get(unit, unit), start, end, engine)
    if not len(zones):
        st.caption('Esta medición no tiene distritos asignados en el conjunto de datos.')


def main():
    st.set_page_config(page_title='SmartCity · Madrid', layout='wide')
    st.html(STYLE)
    with st.container(key='intro'):
        st.html('<p class="city">Madrid, España</p>')
        st.title('SmartCity', anchor=False)
        st.caption('Explora las lecturas de aire, tráfico y los accidentes registrados')

    daily, sample = load_measurements()
    measurements = measurement_options(daily) if not daily.empty else []
    order = {measurement: i for i, measurement in enumerate(MEASUREMENTS)}
    measurements.sort(key=lambda option: order.get(option[0], len(order)))

    source, measure = st.columns([1, 2])
    engine = source.selectbox('Fuente', ('Spark', *ENGINES, 'Hadoop'),
                              help='Spark usa resultados procesados; Hadoop lee de HDFS; PostgreSQL y MongoDB consultan el motor local.')
    options = measurements
    if engine == 'MongoDB':
        queries = [*MG_OPTIONS, ACCIDENTS]
        if measurements:
            queries.append(MONGO_EXTREMA)
        codes = {ACCIDENTS: 'MG08', MONGO_EXTREMA: 'MG03'}
        options = [*sorted(queries, key=lambda option: codes.get(option, option[0])), *measurements]
    elif engine == 'PostgreSQL':
        options = [*PG_OPTIONS, *measurements]
    elif engine == 'Spark' and not daily.empty:
        options = [*measurements, *SPARK_VIEWS]
    elif engine == 'Hadoop':
        options = [HADOOP_COUNTS, *HADOOP_ACTIVITY]
    if st.session_state.get('measurement') not in options:
        default = measurements[0] if measurements and engine != 'Hadoop' else (options[0] if options else None)
        st.session_state['measurement'] = default
    label = 'Consulta' if engine == 'Hadoop' else 'Consulta o medición'
    selection = measure.selectbox(label, options, format_func=option_label,
                                  key='measurement', disabled=not options)
    if engine in ENGINES and measurements:
        measure.caption('10 consultas del enunciado · También puedes elegir una medición')
    if selection == ACCIDENTS:
        show_accidents()
    elif selection == MONGO_EXTREMA:
        measurement, unit = st.selectbox('Variable de los extremos', measurements, format_func=option_label)
        show_measurements(daily, measurement, unit, engine, show_extrema=True)
    elif selection in PG_OPTIONS:
        show_postgres_query(selection)
    elif selection in MG_OPTIONS:
        show_mongo_query(selection, daily)
    elif selection == HADOOP_COUNTS or selection in HADOOP_ACTIVITY:
        show_hadoop(selection)
    elif selection in SPARK_VIEWS:
        if sample:
            st.info('Estás viendo una muestra del conjunto de datos')
        show_spark_analysis(selection)
    elif selection is None:
        st.info('Todavía no hay lecturas para mostrar. Recarga el panel cuando termine Spark.')
    else:
        if sample:
            st.info('Estás viendo una muestra del conjunto de datos')
        show_measurements(daily, *selection, engine)


if __name__ == '__main__':
    main()
