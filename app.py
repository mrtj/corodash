import streamlit as st

from utils.localizations import Localizations
from pages.r_eff import r_effective_page
from pages.vaccinations import vaccinations_page
from utils.storage import Storage

def main():
    st.set_page_config(page_title='CoroDash', layout='wide')
    storage = Storage()
    st.markdown(
        '''<style>
            div.vega-embed {
                width: 95%;
            }
            </style>
        ''',
        unsafe_allow_html=True
    )
    loc = Localizations()
    
    intro_placeholder = st.sidebar.empty()

    loc.selected_lang = st.sidebar.selectbox('Language / Lingua', loc.get_languages())

    intro_placeholder.markdown(
        f'''
            # {loc.get_text('app_title')}
            {loc.get_text('app_intro')}
        ''')

    selected_page = st.sidebar.selectbox(
        loc.get_text('page_menu_name'), 
        [
            loc.get_text('page_menu_r_eff'), 
            loc.get_text('page_menu_vaccinations')
        ]
    )

    if selected_page == loc.get_text('page_menu_r_eff'):
        r_effective_page(loc, storage)
    elif selected_page == loc.get_text('page_menu_vaccinations'):
        vaccinations_page(loc, storage)

if __name__ == '__main__':
    main()
