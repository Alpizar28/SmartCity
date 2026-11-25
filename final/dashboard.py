"""Explorador de las mediciones de aire y tráfico de Madrid."""
import json
import logging
import os
from pathlib import Path

import altair as alt
import pandas as pd
import pyarrow.parquet as pq
import streamlit as st
from psycopg import Error as PostgresError
from pymongo.errors import PyMongoError

from final.mongo import query as mongo_query
from final.postgres import query as postgres_query

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(os.environ.get('SMARTCITY_SPARK_OUTPUT', ROOT / 'data/spark-cluster-20261111'))
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


def trend_chart(series, start, end, unit, color):
    # Keep missing days visible as gaps rather than connecting unrelated readings.
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
        alt.Tooltip('mean_label:N', title=f'Promedio ({unit})'),
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
        with st.container(height=320, border=False):
            st.html(table.to_html(index=False, border=0, classes='daily-table'))


def main():
    st.set_page_config(page_title='SmartCity · Madrid', layout='wide')
    st.html(STYLE)
    with st.container(key='intro'):
        st.html('<p class="city">Madrid, España</p>')
        st.title('SmartCity', anchor=False)
        st.caption('Explora las lecturas históricas de calidad del aire y tráfico')

    try:
        summary_file = OUTPUT / 'summary.json'
        summary = json.loads(summary_file.read_text(encoding='utf-8'))
        daily = (read_daily(OUTPUT, summary_file.stat().st_mtime_ns)
                 if summary.get('status') in ('PASS', 'PASS_SAMPLE') else pd.DataFrame())
    except (OSError, ValueError):
        daily = pd.DataFrame()
    if daily.empty:
        st.info('Todavía no hay lecturas para mostrar. Recarga el panel cuando termine Spark.')
        return
    if summary['status'] == 'PASS_SAMPLE':
        st.info('Estás viendo una muestra del conjunto de datos')
    options = list(daily[['measurement_type', 'unit']].drop_duplicates()
                   .itertuples(index=False, name=None))
    order = {measurement: i for i, measurement in enumerate(MEASUREMENTS)}
    options.sort(key=lambda option: (order.get(option[0], len(order)), *option))

    def option_label(option):
        measurement, unit = option
        return f'{MEASUREMENTS.get(measurement, measurement)} · {UNITS.get(unit, unit)}'

    with st.container(key='filters'):
        measure, source = st.columns([2, 1])
        measurement, unit = measure.selectbox('Medición', options, format_func=option_label)
        engine = source.selectbox('Fuente', ('Spark', *ENGINES),
                                  help='Spark usa resultados ya calculados; PostgreSQL y MongoDB consultan el motor local.')
        selected = daily[daily['measurement_type'].eq(measurement) & daily['unit'].eq(unit)]
        first = selected['source_day'].min().date()
        last = selected['source_day'].max().date()
        zones = selected['zone_id'].dropna().unique()
        if len(zones):
            names = json.loads(DISTRICTS.read_text(encoding='utf-8'))['names']

            def zone_label(zone):
                return names.get(zone, zone).title() if zone is not None else 'Todos los distritos'

            period, district = st.columns([2, 1])
            zone = district.selectbox('Distrito', [None, *sorted(zones, key=zone_label)],
                                      format_func=zone_label, key='district')
        else:
            period, zone = st.container(), None
        dates = period.date_input('Periodo', (first, last), min_value=first, max_value=last,
                                  format='DD/MM/YYYY', key=f'period:{measurement}:{unit}')
    if len(dates) != 2:
        st.info('Selecciona la fecha final para ver el promedio diario.')
        return
    start, end = dates
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


if __name__ == '__main__':
    main()
