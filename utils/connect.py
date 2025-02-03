import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os 
import dotenv

# load the environmet
dotenv.load_dotenv(os.path.join('env_and_cred', '.env'))

def connect():
    """Connect to the Google Sheets API."""
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('env_and_cred/credentials.json', scope)
    client = gspread.authorize(credentials)
    sheet = client.open(os.getenv("sheet")).sheet1  # Access first sheet
    return sheet