from datetime import datetime

import streamlit as st
import numpy as np

from utils.dataset import DataSet

@st.cache(show_spinner=False, ttl=60*60*24)
def get_dataset(dummy=f'{datetime.now():%Y-%m-%d}'):
    return DataSet(repo='italia/covid19-opendata-vaccini', 
        path='dati/somministrazioni-vaccini-summary-latest.csv',
        date_cols=['data_somministrazione'],
        index_cols=['data_somministrazione'])

def get_regions(dataset):
    return np.sort(dataset.df['nome_area'].unique())

def vaccinations_page(loc):
    dataset = get_dataset()
    region = st.sidebar.selectbox(loc.get_text('Region'), get_regions(dataset))
    st.markdown(f'''
    ## {loc.get_text('page_menu_vaccinations')} \u2013 {region}
    ''')

