from datetime import datetime

import streamlit as st
import altair as alt
import numpy as np
import pandas as pd

from utils.dataset import DataSet

@st.cache(show_spinner=False, ttl=60*60*24)
def get_dataset(dummy=f'{datetime.now():%Y-%m-%d}'):
    return DataSet(repo='italia/covid19-opendata-vaccini', 
        path='dati/somministrazioni-vaccini-summary-latest.csv',
        date_cols=['data_somministrazione'],
        index_cols=['data_somministrazione'])

def get_regions(dataset):
    return np.sort(dataset.df['nome_area'].unique())

def region_df(dataset, region):
    return dataset.df[dataset.df['nome_area'] == region].sort_index()
    
def vac_chart(df, region, loc, height=300):
    d = df.reset_index()
    d = pd.melt(d, id_vars=['data_somministrazione'], var_name='type', value_name='doses')

    chart = alt.Chart(d) \
        .mark_area() \
        .encode(
            x=alt.X('data_somministrazione', title=''),
            y=alt.Y('doses', title=''),
            color=alt.Color('type', title='')
        ) \
        .properties(
            title={
                'text': loc.get_text('vac_fig_title_1', region=region),
                'subtitle': loc.get_text('last_day_title', date=df.index[-1])
            },
            width='container',
            height=height
        )
    return chart

def vaccinations_page(loc):
    dataset = get_dataset()
    region = st.sidebar.selectbox(loc.get_text('Region'), get_regions(dataset))
    st.markdown(f'''
    ## {loc.get_text('page_menu_vaccinations')} \u2013 {region}
    ''')
    df = region_df(dataset, region)
    df = df[['prima_dose', 'seconda_dose']]

    chart = vac_chart(df, region, loc)
    st.altair_chart(chart, use_container_width=True)
