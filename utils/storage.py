import datetime
import extra_streamlit_components as stx

class Storage:

    def __init__(self, expire_after=datetime.timedelta(days=7)):
        self.cookie_manager = stx.CookieManager()
        self.expire_after = expire_after
    
    def get(self, key):
        return self.cookie_manager.get(key)

    def set(self, key, value, expire_after=None):
        expire_after = expire_after or self.expire_after
        self.cookie_manager.set(key, str(value), expires_at=datetime.datetime.now() + expire_after)
    
    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)
