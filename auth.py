import streamlit as st
from streamlit_authenticator import Authenticate

class Auth:
    def __init__(self):
        self.authenticator = Authenticate(
            name='Google Authentication',
            credentials_file="credentials.json",  # Add your Google OAuth credentials file here
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
