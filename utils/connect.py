import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os 
import streamlit as st

def connect():  
    """Connect to the Google Sheets API."""
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    credentials_dct = {
        "type": st.secrets['credentials']["type"],
        "project_id": st.secrets['credentials']["project_id"],
        "private_key_id": st.secrets['credentials']["private_key_id"],
        "private_key": st.secrets['credentials']["private_key"],
        "client_email": st.secrets['credentials']["client_email"],
        "client_id": st.secrets['credentials']["client_id"],
        "auth_uri": st.secrets['credentials']["auth_uri"],
        "token_uri": st.secrets['credentials']["token_uri"],
        "auth_provider_x509_cert_url": st.secrets['credentials']["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets['credentials']["client_x509_cert_url"],
        "universe_domain": st.secrets['credentials']["universe_domain"]
    }

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dct, scope)
    client = gspread.authorize(credentials)
    sheet = client.open(st.secrets['credentials']["sheet"]).sheet1  # Access first sheet
    return sheet