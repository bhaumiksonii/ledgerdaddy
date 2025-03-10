import streamlit as st
from streamlit_authenticator import Authenticate
import streamlit as st
import json

# Get Google credentials from Streamlit secrets
google_credentials_json = st.secrets["GOOGLE_CREDENTIALS_JSON"]
credentials_info = json.loads(google_credentials_json)


class Auth:
    def __init__(self):
        self.authenticator = Authenticate(
            name='Google Authentication',
            credentials_file=credentials_info,  # Add your Google OAuth credentials file here
        )

    def authenticate(self):
        try:
            user_info = self.authenticator.authenticate()
            if user_info:
                return user_info
            else:
                return None
        except Exception as e:
            st.error(f"Authentication failed: {e}")
            return None
