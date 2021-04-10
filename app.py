import streamlit as st

from utils.localizations import Localizations
from pages.r_eff import r_effective_page

def main():
    st.set_page_config(page_title='CoroDash', layout='wide')
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
            # loc.get_text('page_menu_vaccinations')
        ]
    )

    if selected_page == loc.get_text('page_menu_r_eff'):
        r_effective_page(loc)
    elif selected_page == loc.get_text('page_menu_vaccinations'):
        pass

if __name__ == '__main__':
    main()
