import streamlit as st

class Storage:
    
    def get(self, key):
        params = st.experimental_get_query_params()
        return params.get(key)[0]

    def set(self, key, value, expire_after=None):
        st.experimental_set_query_params(**{key:value})
    
    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)
