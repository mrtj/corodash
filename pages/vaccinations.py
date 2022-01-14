from datetime import datetime, timedelta

import streamlit as st
import altair as alt
import numpy as np
import pandas as pd

from utils.dataset import DataSet
from utils.colors import tableau10

@st.cache(show_spinner=False, ttl=60*60*24)
def get_dataset(dummy=f'{datetime.now():%Y-%m-%d}'):
    return DataSet(repo='italia/covid19-opendata-vaccini', 
        path='dati/somministrazioni-vaccini-summary-latest.csv',
        date_cols=['data_somministrazione'],
        index_cols=['data_somministrazione'])

@st.cache
def get_region_pop_df():
    return pd.read_csv('data/region_pop.csv', names=['region', 'population'])

def get_region_pop(region_pop_df, region):
    return region_pop_df[region_pop_df['region'] == region]['population'].iloc[0]

def get_regions(dataset):
    return np.sort(dataset.df['nome_area'].unique())

def region_df(dataset, region):
    df = dataset.df[dataset.df['nome_area'] == region].sort_index()
    hide_today = datetime.now() - df.index.max() < timedelta(days=1)
    if hide_today:
        df = df[:-1]
    return df[['prima_dose', 'seconda_dose']]

def vac_chart(d, title, subtitle, height, loc, color_scale=None, per_population=False):
    y_kwargs = {}
    if per_population:
        y_kwargs['axis'] = alt.Axis(format='%')
    color_kwargs = {}
    if color_scale:
        color_kwargs['scale'] = color_scale
    chart = alt.Chart(d) \
        .mark_area() \
        .encode(
            x=alt.X(loc.get_text('date'), title=''),
            y=alt.Y('doses', title='', **y_kwargs),
            color=alt.Color('type', title='', **color_kwargs),
            order=alt.Order('order', sort='descending')
        ) \
        .properties(
            title={
                'text': title,
                'subtitle': subtitle
            },
            width='container',
            height=height
        )
    return chart

def get_daily_vac_data(df, region, loc):
    d = df.reset_index()
    first_dose = loc.get_text('first dose')
    second_dose = loc.get_text('second dose')
    date = loc.get_text('date')
    d = d.rename(columns={
        'prima_dose': first_dose,
        'seconda_dose': second_dose,
        'data_somministrazione': date
    })
    return d

def get_daily_vac_chart(data, region, loc, height=300):
    first_dose = loc.get_text('first dose')
    second_dose = loc.get_text('second dose')
    date = loc.get_text('date')
    domain = [first_dose, second_dose]
    range_ = [tableau10['blue'], tableau10['orange']]
    data = pd.melt(data, id_vars=[date], var_name='type', value_name='doses')
    data['order'] = (data['type'] == first_dose).astype(int)
    chart = vac_chart(
        data,
        title=loc.get_text('vac_fig_title_1', region=region),
        subtitle=loc.get_text('last_day_title', date=max(data[date])),
        height=height,
        loc=loc,
        color_scale=alt.Scale(domain=domain, range=range_)
    )
    return chart

def get_daily_vac_table(data, loc):
    first_dose = loc.get_text('first dose')
    second_dose = loc.get_text('second dose')
    total = loc.get_text('total')
    data = data.copy()
    data = data.set_index(loc.get_text('date'))
    data.index = data.index.strftime('%Y-%m-%d')
    data[total] = data[first_dose] + data[second_dose]
    return data

def get_total_vac_data(region, loc, population=None):
    dataset = get_dataset()
    df = region_df(dataset, region)
    df = df[['prima_dose', 'seconda_dose']]
    d = df.cumsum()
    d = d.reset_index()
    d['prima_dose'] -= d['seconda_dose']
    first_dose = loc.get_text('first dose')
    both_dose = loc.get_text('both doses')
    d = d.rename(columns={
        'prima_dose': first_dose,
        'seconda_dose': both_dose,
        'data_somministrazione': loc.get_text('date')
    })
    if population:
        d[first_dose] /= population
        d[both_dose] /= population
    return d

def get_total_vac_chart(data, region, loc, height=300, population=None):
    first_dose = loc.get_text('first dose')
    both_dose = loc.get_text('both doses')
    date = loc.get_text('date')
    data = pd.melt(data, id_vars=[date], var_name='type', value_name='doses')
    data['order'] = (data['type'] == both_dose).astype(int)
    domain = [first_dose, both_dose]
    range_ = [tableau10['blue'], tableau10['orange']]
    chart = vac_chart(
        data,
        title=loc.get_text('total_vac_fig_title_1', region=region),
        subtitle=loc.get_text('last_day_title', date=max(data[date])),
        height=height,
        loc=loc,
        color_scale=alt.Scale(domain=domain, range=range_),
        per_population=bool(population)
    )
    return chart

def get_total_vac_table(data, loc, per_population):
    first_dose = loc.get_text('first dose')
    both_dose = loc.get_text('both doses')
    total = loc.get_text('total')
    data = data.copy()
    data[total] = data[first_dose] + data[both_dose]
    table_format = {
        loc.get_text('date'): '{:%Y-%m-%d}'
    }
    if per_population:
        table_format[first_dose] = '{:.2%}'
        table_format[both_dose] = '{:.2%}'
        table_format[total] = '{:.2%}'
    data = data.set_index(loc.get_text('date'))
    data.index = data.index.strftime('%Y-%m-%d')
    return data.style.format(table_format)

def vaccinations_page(loc, default_region='Lombardia'):
    dataset = get_dataset()
    regions = list(get_regions(dataset))
    default_index = regions.index(default_region) if default_region in regions else 0
    region = st.sidebar.selectbox(loc.get_text('Region'), regions, index=default_index)
    st.markdown(f'''
    ## {loc.get_text('page_menu_vaccinations')} \u2013 {region}
    ''')
    df = region_df(dataset, region)

    population = get_region_pop(get_region_pop_df(), region) \
        if st.checkbox(loc.get_text('per population')) else None

    daily_vac_data = get_daily_vac_data(df, region, loc)
    daily_chart = get_daily_vac_chart(daily_vac_data, region, loc)

    total_vac_data = get_total_vac_data(region, loc, population=population)
    total_chart = get_total_vac_chart(data=total_vac_data, region=region, loc=loc, population=population)

    chart = alt.vconcat(daily_chart, total_chart) \
        .resolve_scale(x='shared', color='independent') 
    st.altair_chart(chart)

    if st.checkbox(loc.get_text('show data')):
        col1, col2 = st.columns(2)

        col1.markdown(f'''
        **{loc.get_text('vac_fig_title_1', region=region)}**
        ''')
        daily_vac_table = get_daily_vac_table(daily_vac_data, loc)
        col1.write(daily_vac_table)

        col2.markdown(f'''
        **{loc.get_text('total_vac_fig_title_1', region=region)}**
        ''')
        total_vac_table = get_total_vac_table(total_vac_data, loc, per_population=bool(population))
        col2.write(total_vac_table)

    st.markdown(f'{loc.get_text("data source")}: {dataset.repo_url}')
