import streamlit as st

import epyestim
import epyestim.covid19 as covid19

import numpy as np
import pandas as pd
import altair as alt
from scipy.stats import dgamma
from datetime import datetime

from dataset import DataSet

localizations = {
    'English': {
        'R effective': 'R effective',
        '95% confidence interval': '95% conf. interval',
        'r_fig_title_1': 'R effective in {region}',
        'r_fig_title_2': 'Last day of estimate: {date:%Y-%m-%d}',
        'case_fig_title_1': 'Daily new cases in {region}',
        'case_fig_title_2': 'Last day: {date:%Y-%m-%d}',
        'Daily Positives': 'Daily positives',
        'Region': 'Region',
        'Language': 'Language',
        'date': 'date',
        'Updating...': 'Updating...'
    },
    'Italiano': {
        'R effective': 'R effettivo',
        '95% confidence interval': 'intervallo di conf. al 95%',
        'r_fig_title_1': 'R effettivo in {region}',
        'r_fig_title_2': 'Ultima data stimata: {date:%Y-%m-%d}',
        'case_fig_title_1': 'Nuovi positivi in {region}',
        'case_fig_title_2': 'Ultima data: {date:%Y-%m-%d}',
        'Daily Positives': 'Nuovi positivi',
        'Region': 'Regione',
        'Language': 'Lingua',
        'date': 'data',
        'Updating...': 'Aggiornamento...'
    }
}

tableau10 = {
    'blue': '#1f77b4',
    'orange': '#ff7f0e',
    'green': '#2ca02c',
    'red': '#d62728',
    'purple': '#9467bd',
    'brown': '#8c564b',
    'pink': '#e377c2',
    'gray': '#7f7f7f',
    'olive': '#bcbd22',
    'cyan': '#17becf'
}

selected_lang = None

@st.cache
def get_text(key, **kwargs):
    global selected_lang
    res = localizations[selected_lang].get(key, key)
    return res.format(**kwargs)

@st.cache
def get_languages():
    return list(localizations.keys())

# #### Data

def region_df(dataset, region, resample=True):
    df = dataset.df[dataset.df['denominazione_regione'] == region]
    if resample:
        df = df.resample('D').last()
    return df['2020-06-01':]
    
@st.cache(show_spinner=False, ttl=60*60*24, persist=True)
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

@st.cache(show_spinner=False, ttl=60*60*24, persist=True)
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
        
def cases_chart(cases, region, start=None, width=800, height=250):
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
                'text': get_text('case_fig_title_1', region=region),
                'subtitle': get_text('case_fig_title_2', date=cases.index[-1])
            },
            # width=width,
            height=height
        )
    return chart

def r_effective_chart(time_varying_r, region, start=None, width=800, height=250):
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
                'text': get_text('r_fig_title_1', region=region),
                'subtitle': get_text('r_fig_title_2', date=time_varying_r.index[-1])
            },
            # width=width,
            height=height
        )
    return chart

def main():
    st.set_page_config(page_title='Epyestim', layout='wide')
    global selected_lang
    dataset = get_dataset()
    start = '2020-09-01'

    st.sidebar.markdown(f'''
        # Epyestim
        Estimates of the time varying reproduction number for the COVID-10 epidemic curve in the regions of Italy.
        ''')
    selected_lang = st.sidebar.selectbox('Language / Lingua', get_languages())
    region = st.sidebar.selectbox(get_text('Region'), get_regions(dataset))
    st.header(region)
    
    cases = get_cases(dataset, region)
    chart1 = cases_chart(cases, region, start=start)
    
    si = get_si()
    with st.spinner(get_text('Updating...')):
        time_varying_r = get_time_varying_r(dataset, region, si_distrb=si)
    
    chart2 = r_effective_chart(time_varying_r, region, start=start)
    
    chart = alt.vconcat(chart1, chart2).resolve_scale(x='shared')
    st.altair_chart(chart)

if __name__ == '__main__':
    main()
