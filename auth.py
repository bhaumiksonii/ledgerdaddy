import streamlit as st
from streamlit_authenticator import Authenticate
import os
import json
from google.oauth2.service_account import Credentials

# Load credentials from GitHub secrets
google_credentials_json = os.environ['GOOGLE_CREDENTIALS_JSON']
credentials_info = json.loads(google_credentials_json)
credentials = Credentials.from_service_account_info(credentials_info)
class Auth:
    def __init__(self):
        self.authenticator = Authenticate(
            name='Google Authentication',
            credentials_file=credentials,  # Add your Google OAuth credentials file here
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
