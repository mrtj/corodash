from datetime import datetime

import streamlit as st
import epyestim
import epyestim.covid19 as covid19
import altair as alt
from scipy.stats import dgamma
import numpy as np
import pandas as pd

from utils.dataset import DataSet
from utils.colors import tableau10

# #### Data

def region_df(dataset, region, resample=True):
    df = dataset.df[dataset.df['denominazione_regione'] == region]
    if resample:
        df = df.resample('D').last()
    return df['2020-06-01':]
    
def get_dataset(dummy=f'{datetime.now():%Y-%m-%d}'):
    return DataSet('dati-regioni/dpc-covid19-ita-regioni.csv')

def get_regions(dataset):
    return np.sort(dataset.df['denominazione_regione'].unique())
    
@st.cache()
def get_si(shape=1.87, rate=0.28, N=300):
    # parametri dell'intervallo seriale stimati da dati di contact tracing lombardia
    ## massimo numero di giorni dell'intervallo seriale
    N = 300
    dist = dgamma(a=shape, scale=1/rate)
    intervallo = dist.pdf(range(0, N))
    SI = intervallo / sum(intervallo)
    return SI

def get_time_varying_r(
        dataset, 
        region, 
        column='nuovi_positivi', 
        smoothing_window=None, 
        r_window_size=None, 
        si_distrb = covid19.generate_standard_si_distribution(),
        delay_distrb = covid19.generate_standard_infection_to_reporting_distribution(),
        dummy=f'{datetime.now():%Y-%m-%d}'):
    df = region_df(dataset, region)
    kwargs = {}
    if smoothing_window:
        kwargs['smoothing_window'] = smoothing_window
    if r_window_size:
        kwargs['r_window_size'] = r_window_size
    kwargs['gt_distribution'] = si_distrb
    kwargs['delay_distribution'] = delay_distrb
    series = df[column].copy()
    # the epyestim package - correctly - does not like negative daily cases
    series = series.where(series >= 0, 0)
    time_varying_r = covid19.r_covid(series, **kwargs)
    return time_varying_r

def get_cases(dataset, region, column='nuovi_positivi', window=7):
    df = region_df(dataset, region)
    return df[column].rolling(window).mean().to_frame()


# #### UI

def hline(y, color=None, strokeDash=[]):
    return alt.Chart(pd.DataFrame({'y': [y]})) \
        .mark_rule(color=color, strokeDash=strokeDash) \
        .encode(y='y')
        
def cases_chart(cases, region, loc, start=None, height=250):
    d = cases if start is None else cases[start:]
    d = d.reset_index()
    chart = alt.Chart(d) \
        .mark_line() \
        .encode(
            x=alt.X('data:T', title=''),
            y=alt.Y('nuovi_positivi:Q', title='')
        ) \
        .properties(
            title={
                'text': loc.get_text('case_fig_title_1', region=region),
                'subtitle': loc.get_text('case_fig_title_2', date=cases.index[-1])
            },
            width='container',
            height=height
        )
    return chart

def r_effective_chart(time_varying_r, region, loc, start=None, height=250):
    error_range_opacity = 0.1
    d = time_varying_r if start is None else time_varying_r[start:]
    d = d.reset_index()
    d = d.rename(columns={'Q0.5': 'Q05', 'Q0.025': 'Q0025', 'Q0.975': 'Q0975'})
    r_eff = alt.Chart(d) \
        .mark_line(color='red') \
        .encode(
            x=alt.X('index:T', title=''),
            y=alt.Y('Q05:Q', title='')
        )
    r_conf = alt.Chart(d) \
        .mark_area(color='red', opacity=0.25) \
        .encode(
            x=alt.X('index:T', title=''),
            y=alt.Y('Q0025:Q', title=''),
            y2=alt.Y2('Q0975:Q', title='')
        )
    hline1 = hline(1, tableau10['blue'])
    hline2 = hline(1.25, tableau10['blue'], strokeDash=[4, 2])
    chart = alt.layer(hline1, hline2, r_conf, r_eff) \
        .properties(
            title={
                'text': loc.get_text('r_fig_title_1', region=region),
                'subtitle': loc.get_text('r_fig_title_2', date=time_varying_r.index[-1])
            },
            width='container',
            height=height
        )
    return chart

def r_effective_page(loc, default_region='Lombardia'):
    dataset = get_dataset()
    regions = list(get_regions(dataset))
    default_index = regions.index(default_region) if default_region in regions else 0
    region = st.sidebar.selectbox(loc.get_text('Region'), regions, index=default_index)
    st.markdown(f'''
    ## {loc.get_text('R effective')} \u2013 {region}
    ''')
    if st.checkbox(loc.get_text('show_info')):
        st.markdown(f'''
        {loc.get_text('r-eff_description')}
        ''')

    start = '2020-09-01'
    cases = get_cases(dataset, region)
    subchart1 = cases_chart(cases, region, loc, start=start)
    si = get_si()
    with st.spinner(loc.get_text('Updating...')):
        time_varying_r = get_time_varying_r(dataset, region, si_distrb=si)
    subchart2 = r_effective_chart(time_varying_r, region, loc, start=start)
    chart = alt.vconcat(subchart1, subchart2) \
        .resolve_scale(x='shared') 
    st.altair_chart(chart, use_container_width=True)
    st.markdown(f'{loc.get_text("data source")}: {dataset.repo_url}')
