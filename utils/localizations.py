import json

import streamlit as st

@st.cache()
def _get_localizations():
    with open('resource/localizations.json') as f:
        localizations = json.load(f)
    return localizations

class Localizations:

    def __init__(self):
        self.text_map = _get_localizations()
        self.selected_lang = self.get_languages()[0]

    def get_languages(self):
        return list(self.text_map)
        
    def get_text(self, key, **kwargs):
        res = self.text_map[self.selected_lang].get(key, key)
        return res.format(**kwargs)
